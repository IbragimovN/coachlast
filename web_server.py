# web_server.py
# Simple web server to keep the Replit alive and provide basic status

import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from zoneinfo import ZoneInfo

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        tz = ZoneInfo("Asia/Tashkent")
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Check if bot token is configured
        bot_token_status = "✅ Configured" if os.environ.get("BOT_TOKEN") else "❌ Missing"
        openai_status = "✅ Configured" if os.environ.get("OPENAI_API_KEY") else "⚠️ Optional - using fallback responses"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram AI Coach Bot Status</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                .status {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
                .running {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
                .info {{ background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}
                .time {{ font-family: monospace; font-size: 14px; }}
                .commands {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                code {{ background: #e9ecef; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram AI Coach Bot</h1>
                
                <div class="status running">
                    <strong>Status:</strong> Bot is running and ready to accept commands
                </div>
                
                <div class="status info">
                    <strong>Current Time:</strong> <span class="time">{current_time}</span>
                </div>
                
                <div class="status info">
                    <strong>Bot Token:</strong> {bot_token_status}
                </div>
                
                <div class="status info">
                    <strong>OpenAI API:</strong> {openai_status}
                </div>
                
                <div class="commands">
                    <h3>Available Bot Commands:</h3>
                    <ul>
                        <li><code>/start</code> - Initialize the bot and get welcome message</li>
                        <li><code>/goal &lt;text&gt;</code> - Add a new goal</li>
                        <li><code>/goals</code> - List all your goals</li>
                        <li><code>/habit &lt;text&gt;</code> - Add a new habit</li>
                        <li><code>/habits</code> - List all your habits</li>
                        <li><code>/plan</code> - Get daily plan with priorities</li>
                        <li><code>/report &lt;text&gt;</code> - Submit daily progress report</li>
                        <li><code>/help</code> - Show help message</li>
                    </ul>
                    
                    <h3>Proactive Features:</h3>
                    <ul>
                        <li>🌅 Morning motivation (7:30 AM Tashkent time)</li>
                        <li>🌙 Evening check-in (9:00 PM Tashkent time)</li>
                        <li>⏰ Random midday reminders (12:00-17:00)</li>
                        <li>📊 Streak tracking for consistency</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666; font-size: 14px;">
                    <p>Add your bot to Telegram and start your journey to better habits!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server():
    """Run the web server in a separate thread"""
    server = HTTPServer(('0.0.0.0', 5000), StatusHandler)
    print("Web server running on http://0.0.0.0:5000")
    server.serve_forever()

def start_web_server():
    """Start the web server in background thread"""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    start_web_server()
    # Keep the main thread alive
    try:
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped")
