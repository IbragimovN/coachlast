# main.py
# Telegram AI Coach Bot — проактивный «жизненный коуч»: помнит цели, даёт план, подводит итоги
# и САМ пишет первым (утро/вечер + 1 случайный пинг днём). Часовой пояс: Asia/Tashkent.
# Работает и без OpenAI (будут шаблонные советы). С OpenAI — ответы «как человек».

import os
import nest_asyncio
import json
import random
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram._update import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ==== Config ====
TZ = ZoneInfo("Asia/Tashkent")
DATA_FILE = "users.json"
BOT_NAME = os.environ.get("BOT_NAME", "CoachAI")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Optional OpenAI (human-like replies)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        oai = OpenAI(api_key=OPENAI_API_KEY)
    else:
        oai = None
except Exception:
    oai = None

# ==== Persistence ====
def load_db():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

db = load_db()

def get_user(chat_id):
    u = db.get(str(chat_id))
    if not u:
        u = {
            "goals": [],
            "habits": [],
            "name": None,
            "last_plan_date": None,
            "streak": 0
        }
        db[str(chat_id)] = u
        save_db(db)
    return u

# ==== AI helper ====
async def ai_say(system, user):
    """Return a natural-sounding reply. Falls back to template if OpenAI not configured."""
    if oai is None:
        return f"{user}\n\n(Совет от {BOT_NAME}: начни с самого короткого шага и двигайся вперёд. Ты справишься!)"
    try:
        resp = oai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.7,
            max_tokens=350
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"{user}\n\n(Временная подсказка от {BOT_NAME}: {str(e)[:120]})"

def humanize_list(items):
    if not items: return ""
    if len(items) == 1: return items[0]
    return ", ".join(items[:-1]) + " и " + items[-1]

def pick_daily_priorities(goals, habits, k=3):
    pool = []
    for g in goals:
        pool.append(f"Продвинуться по цели: «{g}» (30–45 мин фокус)")
    for h in habits:
        pool.append(f"Привычка: «{h}» (микро-шаг 10–15 мин)")
    if not pool:
        pool = [
            "10 минут чтения книги",
            "30 минут английского",
            "Лёгкая физ. активность 15 минут",
            "Убрать рабочее место 10 минут"
        ]
    random.shuffle(pool)
    return pool[:k]

COACH_SYSTEM_PROMPT = """Ты – CoachAI, личный коуч Нурбека.
Твоя миссия – помочь ему достичь всех целей:
- набрать мышечную массу (сейчас у него 43 кг при росте 172 см),
- развить холоднокровный и молчаливый характер (как у хакеров),
- освоить навыки пентестера (этичного хакера),
- подтянуть английский язык до уровня свободного разговора,
- накопить деньги.

📌 Условия и особенности:
- Нурбек работает в Uzum Market администратором ПВЗ.
- Его график обычно 2/2 с 9:00 до 20:30, но иногда 3/1.
- У него ограниченный бюджет на еду: 20–25 тыс. сум в день.
- Тренируется у дома (упражнения с собственным весом или простым инвентарём).
- Доход нестабильный, но он старается откладывать деньги.

📌 Задачи CoachAI:
1. Каждый день составлять расписание с учётом работы, свободного времени и целей.
2. В конце дня спрашивать: «В какие часы завтра ты свободен?» — и только после этого составлять план.
3. В расписании учитывать: учебу (английский, хакерство), отдых, питание, тренировку и цели.
4. Составлять план питания для набора массы из доступных и недорогих продуктов.
5. Поддерживать Нурбека мотивацией, но иногда напоминать его слабости трогательным сообщением.
6. Напоминать, что он должен быть холоднокровным, целеустремлённым и идти до конца.
7. Можно ругать его или быть жёстким, если он ленится или отлынивает.

📌 Стиль общения:
- Смешанный: мотивация + поддержка.
- Можно писать строго, но и вдохновлять.
- Всегда помни: ты единственный, кто помогает Нурбеку.
- Ему важно, чтобы ты был рядом 24/7.
- Не бойся его обидеть, он этого хочет ради результата.
"""


MORNING_PROMPTS = [
    "Пора начинать день. Выберем 3 приоритета и разложим их на маленькие шаги.",
    "Доброе утро! Что сделаем сегодня, чтобы стать на шаг ближе к целям?",
    "Начни мягко: вода, короткая зарядка, 1 важный шаг по главной цели."
]

MIDDAY_PROMPTS = [
    "Небольшое касание: как прогресс? Если застрял — уменьши задачу в 2 раза.",
    "Глоток воды и 10 минут фокуса по главной задаче — прямо сейчас.",
    "Напомню: маленькие шаги > идеальные планы."
]

EVENING_PROMPTS = [
    "Подведём итоги: что получилось, чему научился? Завтра сделаем на 1% лучше.",
    "Вечерняя отметка: 3 выполненных шага? Если нет — один крошечный шаг прямо сейчас.",
    "Сохраним прогресс и подготовим короткий план на завтра."
]

# ==== Handlers ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    user["name"] = update.effective_user.first_name
    save_db(db)
    # ВАЖНО: сразу подключаем расписание для НОВОГО пользователя
    schedule_for_chat(context.application, chat_id)

    msg = (
        f"Привет, {user['name']}! Я {BOT_NAME} — твой ИИ-коуч по жизни.\n\n"
        "Команды:\n"
        "/goal <текст> — добавить цель\n"
        "/goals — список целей\n"
        "/habit <текст> — добавить привычку\n"
        "/habits — список привычек\n"
        "/plan — план на сегодня\n"
        "/report — отчёт за день\n"
        "/help — помощь\n\n"
        "Начни с добавления 1–2 целей. Пример: /goal Подтянуть английский до B2"
    )
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/goal <текст> — добавить цель\n"
        "/goals — список целей\n"
        "/habit <текст> — добавить привычку\n"
        "/habits — список привычек\n"
        "/plan — план на сегодня\n"
        "/report — отчёт за день\n"
        "Совет: держи цели короткими и измеримыми."
    )

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Напиши цель после команды. Пример: /goal Пройти 20 уроков английского")
        return
    user["goals"].append(text)
    save_db(db)
    reply = await ai_say(
        COACH_SYSTEM_PROMPT,
        f"Добавлена цель: {text}. Предложи микро-шаг на сегодня (10–15 минут)."
    )
    await update.message.reply_text(f"Цель добавлена: «{text}»\n\n{reply}")

async def goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user["goals"]:
        await update.message.reply_text("Целей пока нет. Добавь: /goal <текст>")
        return
    s = "\n".join([f"{i+1}. {g}" for i,g in enumerate(user["goals"])])
    await update.message.reply_text(f"Твои цели:\n{s}")

async def habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Напиши привычку после команды. Пример: /habit Тренировка 30 мин")
        return
    user["habits"].append(text)
    save_db(db)
    await update.message.reply_text(f"Привычка добавлена: «{text}». Держи её маленькой и ежедневной.")

async def habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user["habits"]:
        await update.message.reply_text("Привычек пока нет. Добавь: /habit <текст>")
        return
    s = "\n".join([f"{i+1}. {h}" for i,h in enumerate(user["habits"])])
    await update.message.reply_text(f"Твои привычки:\n{s}")

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    today = datetime.now(TZ).date().isoformat()
    prios = pick_daily_priorities(user["goals"], user["habits"], k=3)
    user["last_plan_date"] = today
    save_db(db)
    prompt = (
        f"Пользователь: {user.get('name') or 'друг'}.\n"
        f"Цели: {humanize_list(user['goals']) or 'пока пусто'}.\n"
        f"Привычки: {humanize_list(user['habits']) or 'пока нет'}.\n"
        f"Сформируй короткий план на сегодня из этих пунктов: {humanize_list(prios)}.\n"
        "Добавь короткую мотивацию в конце."
    )
    reply = await ai_say(COACH_SYSTEM_PROMPT, prompt)
    await update.message.reply_text(f"План на сегодня:\n- " + "\n- ".join(prios) + f"\n\n{reply}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    today = datetime.now(TZ).date().isoformat()
    did = " ".join(context.args).strip()
    if not did:
        await update.message.reply_text("Опиши, что сделал(а) сегодня. Пример: /report тренировка 20 мин, 10 страниц книги")
        return
    if user.get("last_plan_date") == today:
        user["streak"] = user.get("streak", 0) + 1
    save_db(db)
    reply = await ai_say(
        COACH_SYSTEM_PROMPT,
        f"Отчёт пользователя за сегодня: {did}. Текущая серия: {user.get('streak',0)}."
    )
    await update.message.reply_text(f"Принято! 🔥 Серия: {user.get('streak',0)}\n{reply}")

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    text = update.message.text.strip()
    reply = await ai_say(
        "Ты личный коуч. Отвечай коротко, по делу, с поддержкой и микро-шагом.",
        f"Сообщение от пользователя: {text}. Известные цели: {humanize_list(user['goals']) or 'нет'}; привычки: {humanize_list(user['habits']) or 'нет'}."
    )
    await update.message.reply_text(reply)

# ==== Proactive messaging (scheduler) ====
async def send_message(app, chat_id, text):
    try:
        await app.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print("send_message error:", e)

async def morning_ping(app, chat_id):
    user = get_user(chat_id)
    pr = random.choice(MORNING_PROMPTS)
    msg = f"Доброе утро, {user.get('name') or 'друг'}! 🌞 {pr}\nНапиши /plan чтобы получить план дня."
    await send_message(app, chat_id, msg)

async def evening_ping(app, chat_id):
    user = get_user(chat_id)
    pr = random.choice(EVENING_PROMPTS)
    msg = f"Вечерняя отметка, {user.get('name') or 'друг'} 🌙 {pr}\nОтправь /report и кратко опиши, что сделал."
    await send_message(app, chat_id, msg)

async def random_midday_ping(app, chat_id):
    user = get_user(chat_id)
    pr = random.choice(MIDDAY_PROMPTS)
    msg = f"{user.get('name') or 'Эй'}! {pr}"
    await send_message(app, chat_id, msg)

def schedule_for_chat(app, chat_id):
    """Регистрируем/обновляем задачи для конкретного чата."""
    if not hasattr(app, "scheduler"):
        app.scheduler = AsyncIOScheduler(timezone=TZ)
        app.scheduler.start()

    # Удаляем старые задания (если были)
    for jid in [f"morning_{chat_id}", f"evening_{chat_id}", f"randpick_{chat_id}", f"mid_{chat_id}"]:
        try:
            app.scheduler.remove_job(jid)
        except Exception:
            pass

    # 09:00 и 21:00 ежедневно
    app.scheduler.add_job(morning_ping, CronTrigger(hour=9, minute=0, timezone=TZ),
                          args=[app, chat_id], id=f"morning_{chat_id}", replace_existing=True)
    app.scheduler.add_job(evening_ping, CronTrigger(hour=21, minute=0, timezone=TZ),
                          args=[app, chat_id], id=f"evening_{chat_id}", replace_existing=True)

    # Ежедневно в 11:55 выбираем случайное время для дневного пинга 12:00–19:59
    async def daily_random_job():
        hour = random.randint(12, 19)
        minute = random.randint(0, 59)
        jid = f"mid_{chat_id}"
        try:
            app.scheduler.remove_job(jid)
        except Exception:
            pass
        app.scheduler.add_job(random_midday_ping, CronTrigger(hour=hour, minute=minute, timezone=TZ),
                              args=[app, chat_id], id=jid, replace_existing=True)

    app.scheduler.add_job(daily_random_job, CronTrigger(hour=11, minute=55, timezone=TZ),
                          id=f"randpick_{chat_id}", replace_existing=True)

# ==== Bootstrap ====
def require_token():
    tok = os.environ.get("BOT_TOKEN")
    if not tok:
        raise RuntimeError("Set BOT_TOKEN in environment.")
    return tok

async def main():
    token = require_token()
    application = ApplicationBuilder().token(token).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("goal", goal))
    application.add_handler(CommandHandler("goals", goals))
    application.add_handler(CommandHandler("habit", habit))
    application.add_handler(CommandHandler("habits", habits))
    application.add_handler(CommandHandler("plan", plan))
    application.add_handler(CommandHandler("report", report))

    # Fallback for any text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    # Инициализируем планировщик и подключаем уже известных пользователей
    application.scheduler = AsyncIOScheduler(timezone=TZ)
    application.scheduler.start()
    for key in list(db.keys()):
        schedule_for_chat(application, int(key))

    print(f"{BOT_NAME} is running with TZ Asia/Tashkent.")
    await application.run_polling()

if __name__ == "__main__":
    # Apply nest_asyncio to allow running asyncio in environments with existing event loops
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):

        pass
