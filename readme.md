# ⬤ XTERMCHAT — Complete Documentation
### For Those Who Speak Terminal.

> **Version 1.0.0 — March 2026**
> Self-hosted terminal chat. Your server. Your data. Your rules.

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [How It Works](#2-how-it-works)
3. [Requirements](#3-requirements)
4. [Server Setup](#4-server-setup)
5. [Client Setup](#5-client-setup)
6. [First Time Use](#6-first-time-use)
7. [CLI Commands](#7-cli-commands)
8. [Chat Interface](#8-chat-interface)
9. [Web Interface](#9-web-interface)
10. [Room Management](#10-room-management)
11. [Identity & Security](#11-identity--security)
12. [HTTPS Setup](#12-https-setup)
13. [Server Management](#13-server-management)
14. [Database](#14-database)
15. [API Reference](#15-api-reference)
16. [Troubleshooting](#16-troubleshooting)
17. [FAQ](#17-faq)

---

## 1. INTRODUCTION

XtermChat is a lightweight, self-hosted chat system built for the terminal. Unlike Slack, Discord, or Matrix — XtermChat stores nothing on third-party servers. You deploy the server on your own VPS, your team connects via the CLI client or web browser, and all messages stay on infrastructure you control.

**Who is this for?**
- Developers and sysadmins who prefer the terminal
- Teams that need private internal communication between servers
- Anyone who does not want their data on someone else's servers
- Homelab and self-hosted enthusiasts

**What makes it different?**

| | XtermChat | Matrix/Synapse | Mattermost | Slack/Discord |
|--|-----------|----------------|------------|---------------|
| Self-hosted | ✅ | ✅ | ✅ | ❌ |
| Open source | ✅ | ✅ | ⚠️ partial | ❌ |
| Setup time | ~5 min | ~2–3 hrs | ~30 min | instant |
| RAM usage | ~30 MB | ~1–2 GB | ~300 MB | — |
| Terminal-first | ✅ | ❌ | ❌ | ❌ |
| Web UI included | ✅ | ✅ | ✅ | ✅ |
| No account required | ✅ | ❌ | ❌ | ❌ |
| Data ownership | ✅ | ✅ | ✅ | ❌ |

---

## 2. HOW IT WORKS

```
┌─────────────────────────────────────────────────────────┐
│                      YOUR VPS                           │
│                                                         │
│   xtc-server  (Python Flask + SQLite)                   │
│   Listening on :8080                                    │
│                                                         │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│   │  rooms   │   │ messages │   │  users   │           │
│   └──────────┘   └──────────┘   └──────────┘           │
│          xtc.db  (single file, auto-created)            │
└───────────────────────┬─────────────────────────────────┘
                        │  REST API (HTTP/HTTPS + JSON)
          ┌─────────────┼──────────────┐
          │             │              │
   ┌──────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
   │  CLI Client │ │Web Browser│ │ CLI Client│
   │  xtc-client │ │  :5000    │ │  (Linux)  │
   │  (macOS)    │ │           │ │           │
   └─────────────┘ └───────────┘ └───────────┘
```

**Architecture:**
- **Backend:** Python + Flask (REST API over HTTP/HTTPS)
- **Database:** SQLite3 — single file `xtc.db`, zero configuration
- **CLI Client:** Python with `prompt_toolkit` terminal UI
- **Web Client:** Flask serves HTML pages that connect to the same API
- **Auth:** Username + Hardware PIN (CLI) or Username + 5-digit PIN (Web)

---

## 3. REQUIREMENTS

### Server
- Ubuntu 20.04+ or Debian 11+
- Python 3.6+
- pip
- Port 8080 open (TCP)
- Minimum 512 MB RAM (any $4–6/month VPS works)

### CLI Client
- macOS or Linux
- Python 3.6+
- pip
- `make`

### Web Client
- Any modern browser
- No installation needed — just open the URL

---

## 4. SERVER SETUP

### Step 1 — Clone the repo

```bash
git clone https://github.com/dnysaz/xtc-server.git
cd xtc-server
```

### Step 2 — Install dependencies

```bash
pip3 install flask flask-cors werkzeug
```

### Step 3 — Open port 8080

```bash
sudo ufw allow 8080
sudo ufw enable
sudo ufw status
```

If your VPS provider has a separate firewall panel (DigitalOcean, Vultr, Hetzner, etc.), also open TCP port 8080 there.

### Step 4 — Start the server

```bash
python3 server.py start
# [*] Server started in background (PID: 12345)
```

### Step 5 — Verify it's running

```bash
# From the server itself
curl http://localhost:8080
# {"service": "XtermChat Gateway", "status": "online", "version": "1.1"}

# From your local machine
curl http://YOUR_VPS_IP:8080
# Same response
```

Server is live. ✅

---

### Server File Structure

```
xtc-server/
├── server.py       — Main Flask app, all API routes
├── db.py           — Database init and connection helper
├── room.py         — Room CRUD, password hashing, purge
├── connection.py   — Message save and retrieval
├── user.py         — User helper (admin check)
├── check_db.py     — Interactive database inspector utility
├── xtc.db          — SQLite database (auto-created on first run)
├── server.log      — Server output log (auto-created)
├── server.pid      — Process ID file (auto-created when running)
├── readme.md
└── LICENSE
```

### Auto-Created Files

These files are created automatically — you do not need to touch them:

| File | Created when | Purpose |
|------|-------------|---------|
| `xtc.db` | First run | All data: users, rooms, messages |
| `server.log` | First `start` | Background process output |
| `server.pid` | First `start` | Stores PID for stop command |

---

### Custom Port

Default is `8080`. To change it, edit the last section of `server.py`:

```python
# Find this at the bottom of server.py
elif command == "run_internal":
    app.run(host='0.0.0.0', port=8080, debug=False)  # ← change here
else:
    app.run(host='0.0.0.0', port=8080)               # ← and here
```

Then open the new port:
```bash
sudo ufw allow 9000
```

---

### Keep Server Running After SSH Logout

`python3 server.py start` already runs the server in the background using `subprocess.Popen` with `preexec_fn=os.setpgrp`. It survives SSH logout.

To verify after logout:
```bash
cat server.pid
ps aux | grep server.py
```

For auto-restart on reboot, see [systemd setup](#run-as-systemd-service).

---

## 5. CLIENT SETUP

### Step 1 — Clone the client

```bash
git clone https://github.com/dnysaz/xtc-client.git
cd xtc-client
```

### Step 2 — Install

```bash
make install
```

This installs all Python dependencies (`prompt_toolkit`, `requests`, `flask`) and creates a global `xtc` symlink so you can run it from anywhere.

### Step 3 — Verify

```bash
xtc
```

You should see:

```
┌──────────────────────────────────────────────────────────────┐
│                      X T E R M  C H A T                      │
│                For Those Who Speak Terminal.                 │
└──────────────────────────────────────────────────────────────┘
 TYPE: TERMINAL-CHAT  |  VER: 1.0  |  ENCRYPT: ON

 ➤ USAGE:
   $ xtc <command> [args]

 ➤ COMMANDS:
   connect         Sync with central gateway
   disconnect      Clear current server configuration
   status          Check current gateway connection
   list:rooms      Display all public chat rooms
   create:room     Deploy a new secured room
   delete:room     Wipe room & incinerate logs
   start:chat      Establish encrypted session
```

Installation complete. ✅

---

### Client File Structure

```
xtc-client/
├── xtc.py              — Entry point, command dispatcher
├── utils.py            — Config load/save (~/.xtc_config.json)
├── commands/
│   ├── connect.py      — xtc connect
│   ├── disconnect.py   — xtc disconnect
│   ├── status.py       — xtc status
│   ├── listRooms.py    — xtc list:rooms
│   ├── create.py       — xtc create:room
│   ├── delete.py       — xtc delete:room
│   └── chat.py         — xtc start:chat (terminal UI)
├── web/
│   ├── app.py          — Flask web server for browser UI
│   └── html/
│       ├── index.html  — Login / connect page
│       └── chat.html   — Web chat interface
├── Makefile
└── LICENSE
```

### Config File

The client stores server connection in `~/.xtc_config.json`:

```json
{
    "server_url": "http://103.45.67.89:8080"
}
```

This file is created by `xtc connect` and deleted by `xtc disconnect`. You can edit it manually if needed.

---

## 6. FIRST TIME USE

### Step 1 — Connect to your server

```bash
xtc connect @YOUR_VPS_IP:8080

# Examples:
xtc connect @103.45.67.89:8080
xtc connect @103.45.67.89        # port 8080 is assumed by default
```

The `@` prefix is optional — both formats work.

What happens internally: `utils.save_config()` writes the URL to `~/.xtc_config.json`. HTTP scheme is added automatically if not provided.

### Step 2 — Check connection

```bash
xtc status
```

```
 XTERMCHAT CONNECTION STATUS
 ─────────────────────────────────────────────
 GATEWAY :  http://103.45.67.89:8080
 SERVICE :  XtermChat Gateway v1.1
 STATUS  :  ONLINE (HTTP 200)
 LATENCY :  45 ms
 ─────────────────────────────────────────────
```

### Step 3 — Create a room

```bash
# Interactive mode — prompts for name, password, description
xtc create:room

# Quick mode via arguments
xtc create:room @general
xtc create:room @team secretpassword
```

### Step 4 — Start chatting

```bash
xtc start:chat @general
```

---

## 7. CLI COMMANDS

### `xtc connect`

Saves server address to `~/.xtc_config.json`. Only needs to be done once.

```bash
xtc connect @IP:PORT
xtc connect @103.45.67.89:8080
xtc connect @103.45.67.89        # uses :8080 by default
```

---

### `xtc disconnect`

Removes the saved config file.

```bash
xtc disconnect @103.45.67.89:8080
```

---

### `xtc status`

Checks if the server is reachable and shows connection details.

```bash
xtc status
```

Shows: gateway URL, service name, version, HTTP status, and latency in ms.

---

### `xtc list:rooms`

Lists all rooms on the server in a formatted table.

```bash
xtc list:rooms
```

```
 XTERMCHAT GATEWAY SERVICES
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ID   NAME               ACCESS   BY           CREATED         DESCRIPTION
 ─────────────────────────────────────────────────────────────────────────
 1    @general           OPEN     KETUT        14 Mar 2026     General chat
 2    @team              LOCKED   AGUNG        14 Mar 2026     Dev team only
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Total: 2 gateway access point(s)
```

- **OPEN** (green) — public room, no password needed
- **LOCKED** (yellow) — private room, password required

---

### `xtc create:room`

Creates a new room. Two modes:

**Interactive mode** (recommended for first time):
```bash
xtc create:room
# Prompts:
# > Room Name        : general
# > Room Password    : (leave blank for public)
# > Room Description : General discussion
# > Save to Gateway? (Yes/No): yes
```

**Quick mode via arguments:**
```bash
# Public room
xtc create:room @general

# Private room with password
xtc create:room @team secretpassword
```

Your hardware UUID is recorded as the room's `creator_pin`. Only you (from this machine) can delete or purge this room.

---

### `xtc delete:room`

Permanently deletes a room and all its messages.

```bash
xtc delete:room @general
```

You will be asked to confirm:
```
ARE YOU SURE TO DELETE ROOM '@general'?
All chat and history will be deleted permanently and can't be restored.
Confirm Deletion? (Yes/No):
```

Only the room creator (by username) can delete a room. Validated server-side.

---

### `xtc start:chat`

Opens the full interactive terminal chat UI.

```bash
# Public room
xtc start:chat @general

# Private room — password will be prompted automatically
xtc start:chat @team
```

---

### `xtc start:web`

Starts the local web server so you can use XtermChat from a browser.

```bash
xtc start:web
# [*] Starting XtermChat Web Gateway...
# [*] URL: http://localhost:5000
```

Then open `http://localhost:5000` in your browser. See [Web Interface](#9-web-interface) for details.

---

### `xtc help`

Shows the help menu.

```bash
xtc help
xtc --help
xtc -h
xtc          # no args also shows help
```

---

## 8. CHAT INTERFACE

When you run `xtc start:chat`, you enter the full terminal UI.

```
┌─ HEADER ─────────────────────────────────────────────────────────────┐
│  XtermChat-CLI  |  NODE: mac-dana  |  103.45.67.89  |  [ INPUT ]    │
├─ LEFT SIDEBAR ──┬──── CHAT AREA ─────────────────┬─ RIGHT SIDEBAR ──┤
│                 │                                 │                  │
│ ID              │  now  You   ❯  hello world      │ CHANNEL          │
│  KETUT          │  2m   AGUNG ❯  hey!             │  #GENERAL        │
│                 │  5m   You   ❯  https://x.com    │                  │
│ GATEWAY         │                                 │ CREATOR          │
│  103.45.67.89   │                                 │  KETUT           │
│                 │                                 │                  │
│ PUB_IP          │                                 │ CREATED          │
│  x.x.x.x        │                                 │  14 Mar 2026     │
│                 │                                 │                  │
│ AUTH            │                                 │ ABOUT            │
│  LOCKED         │                                 │  General chat    │
│                 │                                 │                  │
├─────────────────┴─────────────────────────────────┴──────────────────┤
│  STATUS BAR — shows mode and available shortcuts                      │
├───────────────────────────────────────────────────────────────────────┤
│  Message ❯❯❯ _                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### Panels

**Left Sidebar**
- `ID` — your username (taken from system `whoami`, max 5 chars, uppercased)
- `GATEWAY` — server IP you're connected to
- `PUB_IP` — your public IP (fetched from `api.ipify.org`)
- `AUTH` — always `LOCKED` (means your PIN is active)

**Chat Area**
- Messages appear here, newest at bottom
- Auto-scrolls when new messages arrive
- Links are shown in **cyan underline**

**Right Sidebar**
- `CHANNEL` — current room name
- `CREATOR` — who created this room
- `CREATED` — room creation date
- `ABOUT` — room description

**Status Bar**
- Changes dynamically based on current mode
- Shows available shortcuts for the current mode

**Input Area**
- Type messages here, press `Enter` to send
- Supports emoji shortcuts and commands

---

### Two Focus Modes

Press `Tab` to switch between modes:

**INPUT MODE** (default on startup)
- Cursor is in the message box
- Type and send messages normally
- Status bar: `✏️ INPUT MODE`
- Header: `[ INPUT ]`

**CHAT MODE** (press Tab to enter)
- Cursor moves into chat history
- Scroll, select text, copy, open links
- Status bar: `📋 CHAT MODE`
- Header: `[ CHAT ]`
- Auto-scroll pauses while in this mode
- Auto-scroll resumes when you press `End` or send a message

---

### Complete Keyboard Shortcuts

#### Global (work in both modes)

| Key | Action |
|-----|--------|
| `Tab` | Switch between INPUT ↔ CHAT mode |
| `Escape` | Return to INPUT mode / close emoji panel |
| `Ctrl + X` | Exit chat |
| `PageUp` | Scroll chat up 12 lines |
| `PageDown` | Scroll chat down 12 lines |

#### INPUT MODE

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Ctrl + C` | Exit chat |
| `:clear` | Clear chat display (local only, no server effect) |
| `:purge` | Delete all messages from server (creator only) |
| `:e` | Toggle emoji shortcuts reference panel |
| `:q` / `:quit` / `:exit` | Exit chat |

#### CHAT MODE (after pressing Tab)

| Key | Action |
|-----|--------|
| `↑` `↓` | Scroll line by line |
| `Home` | Jump to top of chat history |
| `End` | Jump to bottom, resume auto-scroll |
| `Shift + ←` | Select one character left |
| `Shift + →` | Select one character right |
| `Shift + ↑` | Select one line up |
| `Shift + ↓` | Select one line down |
| `Ctrl + Shift + →` | Select next word |
| `Ctrl + Shift + ←` | Select previous word |
| `Ctrl + C` | Copy selected text to clipboard |
| `Ctrl + L` | Open link at cursor position in browser |
| `Tab` | Return to INPUT mode |

---

### Copy Text from Chat

1. Press `Tab` → enter CHAT MODE
2. Navigate cursor to the message you want
3. Hold `Shift` + arrow keys to select text
4. Press `Ctrl + C` to copy
5. Status bar shows: `✅ COPIED TO CLIPBOARD!` for 2 seconds

Clipboard integration: `pbcopy` on macOS, `xclip`/`xsel` on Linux.

---

### Open Links

URLs in messages are automatically detected and shown in **cyan underline**.

To open a link:
1. Press `Tab` → CHAT MODE
2. Move cursor onto the link with arrow keys
3. Press `Ctrl + L` → opens in your default browser

macOS: uses `open`. Linux: uses `xdg-open`.

---

### Emoji Shortcuts

Type `:e` in input box to open the reference panel. All shortcuts auto-convert when you press Enter to send.

| Shortcut | Emoji | Shortcut | Emoji | Shortcut | Emoji |
|----------|-------|----------|-------|----------|-------|
| `:fire` | 🔥 | `:check` | ✅ | `:robot` | 🤖 |
| `:rocket` | 🚀 | `:warn` | ⚠️ | `:bug` | 🪲 |
| `:nice` | 👍 | `:heart` | ❤️ | `:coffee` | ☕ |
| `:cool` | 😎 | `:star` | ⭐ | `:beer` | 🍺 |
| `:laugh` | 😂 | `:ghost` | 👻 | `:globe` | 🌐 |
| `:smile` | 😊 | `:party` | 🎉 | `:key` | 🔑 |
| `:cry` | 😢 | `:eyes` | 👀 | `:box` | 📦 |
| `:pray` | 🙏 | `:100` | 💯 | `:link` | 🔗 |
| `:muscle` | 💪 | `:zap` | ⚡ | `:skull` | 💀 |
| `:lock` | 🔒 | `:cloud` | ☁️ | `:top` | 🔝 |

---

## 9. WEB INTERFACE

XtermChat includes a web UI for users who prefer a browser over the terminal.

### Start the Web Server

```bash
xtc start:web
# [*] Starting XtermChat Web Gateway...
# [*] URL: http://localhost:5000
```

Open `http://localhost:5000` in your browser.

The web server runs on port `5000` (Flask) and connects to your XtermChat server through the browser's fetch API.

---

### Login Page (`/`)

Fields required to connect:
- **Server IP** — IP address of your XtermChat server
- **Port** — default `8080`
- **User Handle** — your username (will be uppercased on server)
- **Security PIN** — 5-digit numeric PIN (you choose this, unlike CLI which uses hardware UUID)
- **Remember Config** — saves IP and port to `localStorage` for next visit

What happens on connect:
1. Browser sends `POST /login` to your server with username + PIN
2. If username is new → auto-registered on server
3. If username exists → PIN must match the registered one
4. On success → redirected to `/chat`

> **Note:** Web PIN is a 5-digit number you choose yourself, unlike the CLI which uses your machine's hardware UUID. This means web users can connect from any device, but must remember their PIN.

---

### Chat Page (`/chat`)

Full chat interface in the browser. Session data (IP, port, username, PIN, room) is stored in `localStorage` during the session.

---

### Web vs CLI — Key Differences

| | CLI | Web |
|--|-----|-----|
| PIN type | Hardware UUID (auto) | 5-digit number (user-chosen) |
| PIN device-bound | ✅ Yes | ❌ No (any device) |
| Installation needed | ✅ Yes | ❌ No |
| Works on mobile | ❌ | ✅ |
| Tab/focus modes | ✅ | ❌ |
| Link click | Ctrl+L | Direct click |

---

## 10. ROOM MANAGEMENT

### Public vs Private Rooms

**Public room** — anyone connected to the server can join without a password.

```bash
xtc create:room @general
xtc create:room @announcements
```

**Private room** — requires a password to join. The room still appears in `list:rooms` but shows `LOCKED` status.

```bash
xtc create:room @engineering s3cr3t
xtc create:room @finance finance2026
```

Room passwords are stored as **bcrypt hashes** via `werkzeug.security.generate_password_hash`. The raw password is never stored.

---

### Creator Privileges

When you create a room, your hardware UUID is stored as `creator_pin` in the database. This binds the room to your specific machine.

Only the creator (verified by PIN) can:
- **Purge messages** — type `:purge` inside the chat
- Via CLI delete only the creator by username can delete

---

### Purge Messages

Wipes all messages from the server for that room. The room itself remains. Irreversible.

```bash
# Inside start:chat
:purge
```

Server validates: `requester_pin == creator_pin` (case-insensitive). If mismatch → `403 Unauthorized: Hardware ID mismatch`.

---

### Delete a Room

Permanently removes the room and all its messages from the database.

```bash
xtc delete:room @roomname
```

Confirmation prompt shown before execution. Validated by username server-side.

---

## 11. IDENTITY & SECURITY

### How CLI Identity Works

```
Your machine UUID (IOPlatformUUID on macOS, hostname fallback)
         ↓
    This is your CLI_PIN
         ↓
Sent with every message and room creation
         ↓
Server stores: username → PIN mapping in users table
         ↓
Future messages: PIN must match stored record
         ↓
Mismatch → 403 Identity mismatch. Wrong PIN.
```

Your username comes from `getpass.getuser()` — the system's current logged-in user, uppercased and max 5 characters. Example: `ketutdana` → `KETUT`.

### What the Server Validates

| Action | Validation method |
|--------|-------------------|
| Send message | `user_record['pin'] == user_pin` |
| Create room | PIN stored as `creator_pin` |
| Purge messages | `requester_pin == creator_pin` |
| Delete room | Username must match creator |
| Join private room | Room password checked via bcrypt |
| Web login | PIN must match stored record |

### What is Stored in the Database

**users table:**
```
username (TEXT, PRIMARY KEY) | pin (TEXT)
ketut                        | ABC-UUID-123...
```

**rooms table:**
```
id | name    | creator | password (hashed) | description | created_at | creator_pin
1  | general | ketut   |                   | Gen chat    | 1741234567 | ABC-UUID-123...
```

**messages table:**
```
id | room    | sender | pin          | content      | timestamp
1  | general | KETUT  | ABC-UUID-123 | Hello world  | 2026-03-14 08:30:00
```

### Network Security

Default uses **HTTP** — acceptable for:
- Private LAN networks
- Internal server-to-server over VPN
- Development and testing

For public-facing deployments → use **HTTPS** (see next section).

---

## 12. HTTPS SETUP

No code changes needed on the client. Just switch your server URL from `http://` to `https://` after setup.

### Option A — Caddy (Easiest, Recommended)

Caddy automatically handles SSL certificates from Let's Encrypt.

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy -y

# Configure
sudo nano /etc/caddy/Caddyfile
```

```
yourdomain.com {
    reverse_proxy localhost:8080
}
```

```bash
sudo systemctl reload caddy
```

Update client:
```bash
xtc disconnect @oldip:8080
xtc connect @yourdomain.com
```

Done — all traffic is now encrypted. ✅

---

### Option B — Nginx + Let's Encrypt

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com

sudo nano /etc/nginx/sites-available/xtermchat
```

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/xtermchat /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 13. SERVER MANAGEMENT

### Start / Stop

```bash
# Start in background
python3 server.py start
# [*] Server started in background (PID: 12345)

# Stop
python3 server.py stop
# [*] Server stopped.

# Restart
python3 server.py stop && python3 server.py start

# Run in foreground (for debugging)
python3 server.py
```

### Check if Running

```bash
# Method 1 — PID file
cat server.pid

# Method 2 — process list
ps aux | grep server.py

# Method 3 — HTTP check
curl http://localhost:8080
```

### View Logs

```bash
# Follow log in real-time
tail -f server.log

# Last 100 lines
tail -n 100 server.log

# Search for errors
grep "ERROR\|Exception" server.log
```

### Run as systemd Service (Auto-restart on Reboot)

```bash
sudo nano /etc/systemd/system/xtermchat.service
```

```ini
[Unit]
Description=XtermChat Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/xtc-server
ExecStart=/usr/bin/python3 /home/ubuntu/xtc-server/server.py run_internal
Restart=always
RestartSec=5
StandardOutput=append:/home/ubuntu/xtc-server/server.log
StandardError=append:/home/ubuntu/xtc-server/server.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable xtermchat
sudo systemctl start xtermchat

# Check status
sudo systemctl status xtermchat
```

Now the server starts automatically on boot and restarts if it crashes.

### Update the Server

```bash
cd xtc-server
python3 server.py stop
git pull
python3 server.py start
```

Your `xtc.db` is preserved through updates. The migration code in `db.py` handles schema changes automatically.

### Backup

The entire server state is in one file:

```bash
# Local backup
cp xtc.db xtc_backup_$(date +%Y%m%d_%H%M).db

# Remote backup
scp xtc.db user@backup-server:/backups/xtc_$(date +%Y%m%d).db
```

---

## 14. DATABASE

### Inspect with check_db.py

```bash
python3 check_db.py
```

Interactive menu:
```
XTERMCHAT DATABASE CHECKER
1. Rooms
2. Users
3. Messages
4. Exit
```

Shows formatted tables with all data. Timestamps are converted to human-readable format automatically.

### Direct SQLite Access

```bash
sqlite3 xtc.db

# Useful queries:
.tables                          -- list all tables
SELECT * FROM rooms;             -- all rooms
SELECT * FROM users;             -- all registered users
SELECT * FROM messages LIMIT 20; -- last messages
SELECT COUNT(*) FROM messages WHERE room='general'; -- message count
.quit
```

### Reset / Wipe Everything

```bash
python3 server.py stop
rm xtc.db
python3 server.py start
# Fresh database created on startup
```

---

## 15. API REFERENCE

All endpoints accept and return JSON. Base URL: `http://YOUR_SERVER:8080`

---

### `GET /`
Health check.

**Response 200:**
```json
{"status": "online", "service": "XtermChat Gateway", "version": "1.1"}
```

---

### `POST /login`
Register or verify user identity. Used by the web client on login.

**Request:**
```json
{"user": "ketut", "pin": "12345"}
```

**Response 200** — existing user, PIN matches:
```json
{"status": "success", "message": "Welcome back"}
```

**Response 201** — new user registered:
```json
{"status": "success", "message": "New identity registered"}
```

**Response 403** — PIN mismatch:
```json
{"status": "failed", "message": "Identity locked to another device/PIN."}
```

---

### `GET /rooms`
List all rooms (without passwords or creator PINs).

**Response 200:**
```json
{
  "status": "success",
  "count": 2,
  "rooms": [
    {
      "name": "general",
      "has_password": false,
      "creator": "KETUT",
      "description": "General chat",
      "created_at": 1741234567
    }
  ]
}
```

---

### `POST /create-room`
Create a new room.

**Request:**
```json
{
  "room": "general",
  "user": "ketut",
  "password": "",
  "description": "General discussion",
  "created_at": 1741234567,
  "pin": "HARDWARE-UUID-OR-5-DIGIT-PIN"
}
```

**Response 201:**
```json
{"status": "success", "message": "Room @general created."}
```

**Response 400** — room already exists:
```json
{"status": "failed", "message": "Room already exists or invalid data schema."}
```

---

### `POST /verify-room`
Check if a room exists and verify its password.

**Request:**
```json
{"room": "general", "password": ""}
```

**Response 200:** `{"status": "success"}`

**Response 404:** `{"status": "failed", "message": "room_not_found"}`

**Response 403:** `{"status": "failed", "message": "wrong_password"}`

---

### `POST /send`
Send a message to a room.

**Request:**
```json
{
  "room": "general",
  "password": "",
  "user": "KETUT",
  "content": "Hello world",
  "pin": "HARDWARE-UUID"
}
```

**Response 201:** `{"status": "success"}`

**Response 403** — PIN mismatch:
```json
{"status": "failed", "message": "Identity mismatch. Wrong PIN."}
```

---

### `GET /messages/<room_name>`
Get all messages for a room, ordered oldest first.

```
GET /messages/general?password=
GET /messages/team?password=secretpassword
```

**Response 200:**
```json
[
  {
    "sender": "KETUT",
    "content": "Hello world",
    "pin": "HARDWARE-UUID",
    "timestamp": "2026-03-14 08:30:00"
  }
]
```

**Response 401** — wrong/missing password:
```json
{"status": "failed", "message": "password_required"}
```

---

### `POST /delete-room`
Delete a room and all its messages. Creator only (validated by username).

**Request:**
```json
{"room": "general", "user": "ketut"}
```

**Response 200:** `{"status": "success", "message": "Room @general deleted."}`

**Response 403:**
```json
{"status": "failed", "message": "Unauthorized. Only 'ketut' can delete this room."}
```

---

### `POST /purge-chat`
Delete all messages in a room. Creator only (validated by hardware PIN).

**Request:**
```json
{"room": "general", "user": "ketut", "pin": "HARDWARE-UUID"}
```

**Response 200:** `{"status": "success", "message": "History cleared successfully."}`

**Response 403:** `{"status": "error", "message": "Unauthorized: Hardware ID mismatch."}`

---

## 16. TROUBLESHOOTING

### Server won't start

```bash
# Check if something is already on port 8080
sudo lsof -i :8080

# Kill it
sudo kill -9 <PID>

# Remove stale PID file
rm server.pid

# Start again
python3 server.py start
```

---

### `[!] CONNECTION FAILED` on client

```bash
# 1. Check server is running
curl http://YOUR_IP:8080

# 2. Check firewall
sudo ufw status
sudo ufw allow 8080

# 3. Check VPS provider panel — open port 8080 there too

# 4. Re-check your saved config
cat ~/.xtc_config.json
```

---

### `Room not found`

```bash
# Check available rooms
xtc list:rooms

# Room names are case-sensitive
# '@' prefix is stripped automatically — @general and general are the same
```

---

### `Identity locked to another device/PIN`

Your username is already registered from a different machine or with a different PIN.

Options:
1. Use a different username
2. Connect from the original machine
3. Admin can delete the entry from the database:
```bash
sqlite3 xtc.db "DELETE FROM users WHERE username='ketut';"
```

---

### `Access Denied` on purge

You must be on the **same machine** that created the room. The hardware PIN is device-specific and cannot be transferred.

---

### Server crashed / not responding

```bash
# Check for errors in log
tail -50 server.log

# Clean up and restart
rm server.pid
python3 server.py start
```

---

### Web client can't connect — CORS error

The server already has CORS enabled for all origins in `server.py`:
```python
CORS(app, resources={r"/*": {"origins": "*", ...}})
```

If you still get CORS errors, check that you're connecting to the correct IP and port, and that the server is actually running.

---

### Chat scroll not working

- Make sure your terminal is at least 80×24 characters
- Press `Tab` to enter CHAT MODE first
- Then use `↑`/`↓` or `PageUp`/`PageDown`

---

### Copy not working on Linux

Install clipboard utility:
```bash
sudo apt install xclip
# or
sudo apt install xsel
```

---

## 17. FAQ

**Q: Can multiple people be in the same room at the same time?**

Yes. Messages are polled every 2 seconds by each client. All connected users see new messages automatically.

---

**Q: Are messages stored permanently?**

Yes, until you `:purge` them (wipes messages, keeps room) or `xtc delete:room` (wipes everything). You can also manually delete `xtc.db` to reset completely.

---

**Q: Can I run the server and client on the same machine?**

Yes. Just connect to `@localhost:8080` or `@127.0.0.1:8080`.

---

**Q: Can I connect to multiple servers?**

Currently one server is saved at a time in `~/.xtc_config.json`. To switch servers, run `xtc connect @newserver` — it overwrites the previous config.

---

**Q: What happens when I reinstall my OS or switch machines?**

Your hardware PIN changes. Your old username on the server is locked to the old PIN. A server admin can reset it:

```bash
sqlite3 xtc.db "DELETE FROM users WHERE username='yourname';"
```

Then reconnect and your username will be re-registered with the new PIN.

---

**Q: How do I update?**

**Server:**
```bash
cd xtc-server && python3 server.py stop && git pull && python3 server.py start
```

**Client:**
```bash
cd xtc-client && git pull && make install
```

Database and config are preserved through updates.

---

**Q: Is there a message length limit?**

No hard limit is enforced by default. A practical limit of ~2000 characters per message is recommended for clean display in the terminal.

---

**Q: Can I use this on Windows?**

The server runs on Windows (Python + Flask are cross-platform). The CLI client is optimized for macOS and Linux. Windows is not officially tested.

---

**Q: How many users / rooms / messages can it handle?**

SQLite handles millions of rows comfortably. For a team of 2–50 people with normal usage, performance will be fine on even the cheapest VPS. For very high traffic, you would want to migrate to PostgreSQL, but that requires modifying `db.py`.

---

**Q: Can the web client and CLI client be in the same room?**

Yes. Both connect to the same server API and see each other's messages in real time.

---

*XtermChat — For Those Who Speak Terminal.*
*MIT License — https://github.com/dnysaz/xtc-server*