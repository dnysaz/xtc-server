# ⬤ XTERMCHAT
### For Those Who Speak Terminal.

XtermChat is a lightweight self-hosted chat system built for the terminal. No GUIs, no bloat, no third-party servers — just pure command-line communication that runs on your own infrastructure.

> Your server. Your data. Your rules.

---

## 🚀 QUICK START

### Server (Your VPS / Ubuntu)

```bash
# 1. Clone the server repo
git clone https://github.com/dnysaz/xtc-server.git
cd xtc-server

# 2. Install dependencies
pip install flask flask-cors

# 3. Open port 8080
sudo ufw allow 8080

# 4. Start the server
python3 server.py start
# [*] Server started in background (PID: XXXXX)
```

Done. Your private chat server is running. ✅

---

### Client (Your Mac / Linux)

```bash
# 1. Clone the client repo
git clone https://github.com/dnysaz/xtc-client.git
cd xtc-client

# 2. Install
make install

# 3. Run
xtc
```

---

## CORE COMMANDS

| Command | Description |
|---------|-------------|
| `connect` | Pair your client with a server. Provide the server IP and port. |
| `disconnect` | Clear current server configuration from local client. |
| `status` | Check connection status and server availability. |
| `list:rooms` | List all public rooms on the connected server. |
| `create:room` | Create a new room. Optionally set a password for private access. |
| `delete:room` | Permanently delete a room. Only the room creator can do this. |
| `start:chat` | Open interactive terminal chat UI. |

---

## USAGE EXAMPLES

### 1. Connect to Your Server

```bash
# Connect client to your VPS
xtc connect @123.123.123.123:8080

# Check connection
xtc status

# Disconnect
xtc disconnect @123.123.123.123:8080
```

### 2. Room Management

```bash
# List all public rooms
xtc list:rooms

# Create a public room
xtc create:room @lobby

# Create a password-protected private room
xtc create:room @private P@ssw0rd123

# Delete a room (creator only)
xtc delete:room @lobby
```

### 3. Start Chatting

```bash
# Join a public room
xtc start:chat @lobby

# Join a private room
xtc start:chat @private
# You will be prompted for the room password
```

### 4. In-Chat Controls

Once inside `start:chat`, use these keyboard shortcuts:

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Tab` | Switch focus between chat and input |
| `PageUp / PageDown` | Scroll chat history |
| `↑ ↓` | Scroll line by line (in chat mode) |
| `Home / End` | Jump to top / bottom of chat |
| `Shift + ←→` | Select text character by character |
| `Ctrl + Shift + ←→` | Select text word by word |
| `Ctrl + C` | Copy selected text to clipboard |
| `Ctrl + L` | Open link under cursor in browser |
| `Ctrl + X` | Exit chat |
| `:clear` | Clear local chat display |
| `:purge` | Delete all room history from server (creator only) |
| `:e` | Show all emoji shortcuts |
| `:q` | Quit chat |

### 5. Emoji Shortcuts

Type these inside a message and they auto-convert on send:

| Shortcut | Emoji | Shortcut | Emoji |
|----------|-------|----------|-------|
| `:fire` | 🔥 | `:check` | ✅ |
| `:rocket` | 🚀 | `:warn` | ⚠️ |
| `:nice` | 👍 | `:heart` | ❤️ |
| `:cool` | 😎 | `:star` | ⭐ |
| `:laugh` | 😂 | `:ghost` | 👻 |
| `:robot` | 🤖 | `:bug` | 🪲 |
| `:coffee` | ☕ | `:beer` | 🍺 |

Type `:e` inside chat to view all available shortcuts.

---

## 🛠 TECH STACK

```
Backend:    Python + Flask
Database:   SQLite3 (local, no external DB required)
Interface:  prompt_toolkit (Terminal UI)
Protocol:   REST API over HTTP/HTTPS
Transport:  JSON payloads
Port:       8080 (default, configurable)
```

---

## ⚠️ SECURITY

### Authentication
- Each user is identified by **username + hardware PIN** (device UUID)
- PIN is bound to the device — the same username cannot be used from a different machine
- Room passwords are validated server-side on every connection

### Room Security
- Public rooms: open access, no password required
- Private rooms: password required to join
- **Only the room creator** can delete a room or purge its history
- All permission checks are enforced on the server, not the client

### Network
- Default setup uses **HTTP** — sufficient for private/internal networks
- For production or public-facing deployments, **HTTPS is strongly recommended**
- With HTTPS, all traffic (messages, passwords, PINs) is encrypted in transit
- No client code changes needed to switch from HTTP to HTTPS

### Recommended HTTPS setup (with Caddy):
```bash
# Auto SSL with Let's Encrypt — replace with your domain
caddy reverse-proxy --from yourdomain.com --to localhost:8080
```

---

## ❗ TROUBLESHOOTING

**Connection refused**
```bash
# Check server is running
xtc status

# Make sure port 8080 is open on your VPS
sudo ufw allow 8080
sudo ufw status
```

**Wrong password / access denied**
```bash
# Room passwords are case-sensitive
# Re-enter password when prompted during start:chat
```

**Room creation failed**
```bash
# Check connection first
xtc status

# Room name must start with @
xtc create:room @roomname
```

**Server already running**
```bash
# Stop the server first
python3 server.py stop

# Then restart
python3 server.py start
```

---

## 📋 REQUIREMENTS

**Server**
- Python 3.6+
- pip
- Ubuntu / Debian Linux (recommended)
- Open port 8080

**Client**
- Python 3.6+
- macOS or Linux
- `make` (for install)

---

## 🤝 CONTRIBUTING

Contributions are welcome:
- Report bugs via Issues
- Submit pull requests
- Suggest features
- Improve documentation

---

## 📄 LICENSE

MIT License — free to use, modify, and distribute.

---

## 🌟 WHY XTERMCHAT?

| | XtermChat | Matrix/Synapse | Mattermost | Slack/Discord |
|--|-----------|---------------|------------|---------------|
| Self-hosted | ✅ | ✅ | ✅ | ❌ |
| Open source | ✅ | ✅ | ⚠️ partial | ❌ |
| Setup time | ~5 minutes | ~2-3 hours | ~30 minutes | instant |
| RAM usage | ~30MB | ~1-2GB | ~300MB | — |
| Terminal-first | ✅ | ❌ | ❌ | ❌ |
| Data ownership | ✅ | ✅ | ✅ | ❌ |
| No account required | ✅ | ❌ | ❌ | ❌ |

Built for developers and sysadmins who want a private, no-nonsense communication tool that runs on infrastructure they control.

---

*Version 1.0.0 — March 2026*