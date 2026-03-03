# Telegram Timer Notification Bot

A Telegram bot that sends scheduled notifications.

## Features
- Independent YAML configuration for each user  
- `/add` to create a new task (interactive)  
- `/list` to view all tasks  
- `/del` to delete a task (via button selection)  
- `/turnon` to enable a task  
- `/turnoff` to disable a task  
- Automatically restores all enabled tasks when the bot restarts  
- CRON‑based scheduling (supports year-level precision)

## Install Dependencies

```bash
pip install -r requirements.txt
```