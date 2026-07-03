# YalaharBot

YalaharBot is a demo Discord bot with a Django REST backend and a React frontend for looking up and managing Tibia characters.

## Features

- Discord slash/hybrid command support
- Django REST API for Discord users and Tibia characters
- React + Tailwind frontend
- Tibia character lookup through `tibiapy`
- Environment-based configuration

## Requirements

- Python 3.12+
- Node.js and npm
- A Discord bot token

## Backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder values. The default example uses SQLite for local demo use. To use PostgreSQL, switch the `DB_ENGINE` block in `.env` to the PostgreSQL values shown in `.env.example`.

```powershell
python manage.py migrate
python manage.py runserver
```

## Frontend setup

```powershell
cd frontend
npm install
npm start
```

To build the frontend for Django to serve:

```powershell
cd frontend
npm run build
cd ..
python manage.py collectstatic
```

## Run the Discord bot

Set `DISCORD_BOT_TOKEN` in `.env`, then run:

```powershell
python bot\run_bot.py
```

Set `TEST_GUILD_ID` in `.env` if you want Discord commands synced to one test server first.

## Public repo notes

Do not commit `.env`, local databases, `staticfiles/`, frontend build output, `node_modules/`, or Python bytecode. Use `.env.example` for documented placeholders only.
