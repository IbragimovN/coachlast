# Telegram AI Coach Bot

A proactive Telegram bot that acts as your personal life coach, helping you track goals, build habits, and stay motivated with automated check-ins.

## Features

### Core Functionality
- **Goal Management**: Add and track personal goals with AI-powered guidance
- **Habit Tracking**: Build consistent daily habits with micro-step approach
- **Daily Planning**: Get personalized daily plans based on your goals and habits
- **Progress Reporting**: Submit daily reports and track your consistency streak
- **AI Conversations**: Natural conversations powered by OpenAI GPT-5 (with fallback responses)

### Proactive Messaging
- **Morning Motivation** (7:30 AM Tashkent time): Daily motivation and plan suggestions
- **Evening Check-in** (9:00 PM Tashkent time): Progress review and reflection
- **Midday Reminders** (12:00-17:00): Random motivational pings throughout the day
- **Streak Tracking**: Maintains consistency streaks to encourage daily engagement

## Setup Instructions

### 1. Environment Variables
Configure the following secrets in your Replit:

**Required:**
- `BOT_TOKEN`: Your Telegram bot token from @BotFather

**Optional:**
- `OPENAI_API_KEY`: OpenAI API key for enhanced AI responses (without this, bot uses template responses)
- `BOT_NAME`: Custom bot name (default: "CoachAI")
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-5")

### 2. Getting a Telegram Bot Token
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the provided token and add it to your Replit secrets as `BOT_TOKEN`

### 3. Optional: OpenAI Setup
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Create an API key
3. Add it to your Replit secrets as `OPENAI_API_KEY`

### 4. Deployment
1. Clone this repository to Replit
2. Add your environment variables in the Secrets tab
3. Click "Run" - the bot will start automatically
4. The web interface will be available at your Replit URL

## Bot Commands

- `/start` - Initialize the bot and get welcome message
- `/goal <text>` - Add a new goal (e.g., `/goal Learn Spanish B2 level`)
- `/goals` - List all your current goals
- `/habit <text>` - Add a new habit (e.g., `/habit 20 minutes daily exercise`)
- `/habits` - List all your habits
- `/plan` - Get a personalized daily plan with 3 priorities
- `/report <text>` - Submit your daily progress report
- `/help` - Show available commands

## How It Works

### Data Persistence
- User data is stored in `users.json` with atomic writes for reliability
- Each user has goals, habits, streak counter, and last plan date
- Data is automatically backed up on every update

### AI Integration
- Uses OpenAI GPT-5 for natural, human-like coaching responses
- Falls back to template responses if OpenAI is not configured
- System prompts optimized for coaching and motivation

### Scheduling System
- Uses APScheduler with Asia/Tashkent timezone
- Automatically schedules tasks for new users
- Restores schedules for existing users on bot restart
- Random midday reminders for variety

### Replit Compatibility
- Runs both the Telegram bot and a web server for keep-alive
- Web interface shows bot status and configuration
- Proper environment variable handling
- Atomic file operations for data safety

## Technical Details

- **Python 3.11** with async/await patterns
- **python-telegram-bot 21.4** for Telegram API
- **APScheduler 3.10.4** for automated messaging
- **OpenAI 1.30.0+** for AI responses
- **Timezone-aware** scheduling (Asia/Tashkent)
- **JSON persistence** with atomic writes
- **Error handling** with graceful degradation

## Architecture

