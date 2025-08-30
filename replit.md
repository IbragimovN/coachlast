# Overview

A proactive Telegram bot that serves as a personal life coach, helping users track goals, build habits, and stay motivated through automated check-ins. The bot operates in Asia/Tashkent timezone and provides daily morning motivation (7:30 AM), evening check-ins (9:00 PM), and random midday reminders. It features AI-powered conversations using OpenAI GPT-5 with fallback template responses when OpenAI is unavailable.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Primary Framework**: Python Telegram Bot library (python-telegram-bot v21.4)
- **Architecture Pattern**: Event-driven message handling with command and message handlers
- **Deployment**: Designed for Replit with automatic keep-alive web server

## Scheduling System
- **Scheduler**: APScheduler (AsyncIOScheduler) for proactive messaging
- **Timezone Handling**: Asia/Tashkent timezone using Python's zoneinfo
- **Cron Jobs**: Morning motivation (7:30 AM), evening check-in (9:00 PM), random midday reminders (12:00-17:00)

## AI Integration
- **Primary AI**: OpenAI GPT-5 for human-like conversational responses
- **Fallback System**: Template-based responses when OpenAI API is unavailable
- **Configuration**: Flexible model selection via environment variables

## Data Persistence
- **Storage**: JSON file-based persistence (users.json)
- **Data Structure**: User-centric storage for goals, habits, progress tracking, and streaks
- **Atomic Writes**: Temporary file approach for safe data persistence

## Web Interface
- **Keep-Alive Server**: Simple HTTP server to maintain Replit instance
- **Status Dashboard**: Basic HTML interface showing bot status and configuration
- **Health Monitoring**: Real-time status of bot token and OpenAI API configuration

## Configuration Management
- **Environment Variables**: Secure configuration through Replit secrets
- **Required Config**: BOT_TOKEN (Telegram bot token)
- **Optional Config**: OPENAI_API_KEY, BOT_NAME, OPENAI_MODEL
- **Graceful Degradation**: Bot functions without OpenAI using fallback responses

# External Dependencies

## Core Services
- **Telegram Bot API**: Primary interface for user interactions via BOT_TOKEN
- **OpenAI API**: Optional AI-powered conversational responses (GPT-5 model)

## Python Libraries
- **python-telegram-bot v21.4**: Telegram bot framework with async support
- **apscheduler v3.10.4**: Advanced Python scheduler for proactive messaging
- **openai >=1.30.0**: OpenAI API client for AI conversations

## Runtime Environment
- **Replit Platform**: Cloud deployment with secrets management
- **Python 3.11+**: Required for zoneinfo timezone handling
- **File System**: Local JSON storage for user data persistence