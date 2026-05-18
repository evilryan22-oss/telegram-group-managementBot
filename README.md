# Telegram Group Manager Bot

Production-ready group management bot built with **python-telegram-bot v20+**,
**asyncio**, and **SQLite**. Drop-in deployable to a VPS, Docker, Railway or Render.

## Features

- **Welcomes & goodbyes** with customisable templates (`{mention}`, `{name}`, `{username}`, `{chat}`, `{id}`).
- **Member tracking** persisted in SQLite, learned from joins *and* from anyone who speaks.
- **Intelligent replies** to greetings/thanks/goodbyes when the bot is mentioned or replied to.
- **Per-chat keyword auto-replies** (`/addreply`, `/delreply`, `/replies`).
- **/tagall** — chunked, admin-only, cooldown-protected, safe mentions for users without usernames.
- **Moderation**: `/mute` (with `10m`/`2h`/`1d` durations), `/unmute`, `/ban`, `/kick`, `/warn` (auto-ban on threshold).
- **Flood/spam suppression** with sliding-window + duplicate-message detection.
- **Bot-loop protection** (ignores other bots, ignores its own messages, cooldowns per user).
- **Safe HTML escaping** everywhere, never crashes on missing usernames or deleted accounts.
- **Centralised logging** + global error handler.

## Project structure

```
.
├── bot.py                 # entry point, wires handlers
├── config.py              # .env loader + tunables
├── database.py            # SQLite persistence layer
├── handlers/
│   ├── commands.py        # /start /help /about /rules /ping /joke /settings + setters
│   ├── members.py         # welcome/goodbye + author tracking
│   ├── replies.py         # smart replies + keyword auto-replies
│   ├── tagall.py          # /tagall
│   └── admin.py           # /mute /unmute /ban /kick /warn
├── utils/
│   ├── helpers.py         # admin checks, mentions, cooldowns, flood tracker
│   └── logger.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── Procfile               # Railway / Heroku-style worker
└── README.md
```

## 1. Setup

### Create a bot
1. Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **token**.
2. Disable privacy mode so the bot can read group messages:
   `/setprivacy` → choose your bot → **Disable**.
3. Get your own Telegram user id from [@userinfobot](https://t.me/userinfobot).

### Configure
```bash
cp .env.example .env
# edit .env: paste BOT_TOKEN and your numeric ADMIN_IDS
```

## 2. Install & run

### Local (Linux / macOS)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Windows (PowerShell)
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bot.py
```

### Docker
```bash
docker build -t tg-group-bot .
docker run -d --name tg-group-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  tg-group-bot
```

### Linux VPS as a systemd service
Create `/etc/systemd/system/tg-group-bot.service`:
```ini
[Unit]
Description=Telegram Group Manager Bot
After=network.target

[Service]
WorkingDirectory=/opt/tg-group-bot
EnvironmentFile=/opt/tg-group-bot/.env
ExecStart=/opt/tg-group-bot/.venv/bin/python bot.py
Restart=always
RestartSec=5
User=botuser

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tg-group-bot
journalctl -u tg-group-bot -f
```

### Railway
1. New project → **Deploy from GitHub repo**.
2. Add the variables from `.env.example` in *Variables*.
3. Railway detects the `Procfile` and runs the `worker` process. Done.

### Render
1. New → **Background Worker**.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python bot.py`
4. Add the environment variables from `.env.example`.

## 3. Add the bot to your group

1. Add the bot to your **supergroup**.
2. Promote it to **admin** and grant: *Delete messages*, *Restrict members*, *Ban members*, *Invite via link* (optional).
3. Send `/start` to verify it's alive, then `/help`.

## 4. Admin reference

| Command | Description |
|---|---|
| `/setwelcome <text>` | Custom welcome. Placeholders: `{mention}` `{name}` `{username}` `{chat}` `{id}` |
| `/setgoodbye <text>` | Custom farewell (same placeholders) |
| `/setrules <text>`   | Custom rules shown by `/rules` |
| `/addreply kw \| reply` | Add a keyword auto-reply for this chat |
| `/delreply kw`       | Remove a keyword auto-reply |
| `/replies`           | List configured auto-replies |
| `/tagall [msg]`      | Mention every known member, in chunks |
| `/mute [10m\|2h\|1d]`| Mute (reply to user or pass `@user`/id) |
| `/unmute`            | Lift mute |
| `/ban` / `/kick`     | Ban / kick (kick = ban + unban) |
| `/warn`              | Warn — auto-bans on `MAX_WARNINGS` (default 3) |

## 5. Notes on stability

- Every Telegram call is wrapped in `safe_call` or `try/except TelegramError`.
- The flood tracker drops messages exceeding `flood_max_messages` inside `flood_window_seconds` and also drops back-to-back duplicates.
- `cooldown` enforces per-user per-feature rate limits (`reply_cooldown_seconds`, `tagall_cooldown_seconds`).
- The bot never replies to other bots, never replies to its own messages, and ignores empty/command messages in passive handlers.
- SQLite uses WAL mode; access is serialised by a process-level lock and dispatched off the event loop via `asyncio.to_thread`.

## License

MIT — do whatever you want, no warranty.
