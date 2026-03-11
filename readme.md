# ⬤ XTERMCHAT
### For Those Who Speak Terminal.

XtermChat is a lightweight, high-performance client-server communication system built for the terminal. No GUIs, no bloat—just pure command-line interaction designed for speed, privacy, and minimalist aesthetics.


---

## CORE COMMANDS

| Command | Description |
|---------|-------------|
| `connect` | Sync with central gateway. Pairs your local client with the target Ubuntu server IP address. |
| `disconnect` | Clear configuration. Purges the current server IP from your local configuration (Auto-wipe). |
| `status` | Connection diagnostic. Real-time check for gateway availability, latency, and server version. |
| `list:rooms` | Discovery. Lists all active Public Rooms that can be accessed without a password. |
| `create:room` | Deploy. Spawns a new chat room on the server. Optional passwords can be set for private access. |
| `delete:room` | Incinerate. Permanently deletes a room and securely wipes all associated message logs. |
| `start:chat` | Establish session. Launches the interactive terminal UI with emoji support and session encryption. |

---

## INSTALLATION

### Prerequisites
- Python 3.6 or higher
- pip package manager
- Ubuntu Server (for hosting) / macOS or Linux (for client)

### Quick Install
```bash
# Clone the repository
git clone https://github.com/yourusername/xtermchat.git
cd xtermchat

# Install dependencies (minimal, runs on system Python)
pip install flask prompt-toolkit requests

# Make the CLI executable
chmod +x xtc

# Optional: Add to PATH
export PATH=$PATH:$(pwd)
```
---

## USAGE EXAMPLES

Run these commands from your Mac/Linux terminal:

### 1. Networking & Sync
```bash
# Connect to your remote server (example ip)
xtc connect @123.123.123.123:8080

# Run a diagnostic check
xtc status

# Terminate connection & wipe local config
xtc disconnect @123.123.123.123:8080
```

### 2. Room Management
```bash
# Browse available public rooms
xtc list:rooms

# Deploy a public room
xtc create:room @lobby

# Deploy a secured room with a password
xtc create:room @private P@ssw0rd123
```

### 3. Encrypted Communication
```bash
# Enter an interactive chat session
xtc start:chat @lobby

# Remove a room (Only the creator has permission)
xtc delete:room @lobby
```

### 4. In-Chat Shortcuts
Once inside a chat session (start:chat), you can use emoji shortcuts that automatically convert to their corresponding symbols:

Shortcut	Emoji
:fire	     🔥
:nice	     👍
:cool	     😎
:rocket	     🚀
:laugh	     😂
:warn	     ⚠️
:check	     ✅
:heart	     ❤️
:star	     ⭐
:ghost	     👻
:e	     View all available emoji shortcuts

---

## 🛠 TECH STACK

```
Backend:    Python Flask
Database:   SQLite3 (Persistent Storage)
Interface:  prompt_toolkit (Rich Terminal UI)
Protocol:   REST API via JSON Payloads
Encryption: Session-based encryption
Port:       8080 (default)
```

---

## ⚠️ SECURITY POLICIES

### 🔒 Authentication
- **Anti-Brute Force:** 3 failed password attempts during `start:chat` triggers a Security Alert
- **Auto-Wipe:** Failed attempts result in immediate local configuration deletion
- **Session Encryption:** All messages are encrypted during transmission

### 🛡️ Best Practices
- **Dependency-Free:** Built to run directly on system Python - no venv required
- **Low Footprint:** Minimal resource usage, perfect for low-spec servers
- **Auto-Cleanup:** Messages are securely wiped when rooms are deleted
- **IP Validation:** Server connections require valid IP formatting with @ prefix

### 🔐 Room Security
- Public rooms: Open access, no password required
- Private rooms: Password-protected access
- Creator privileges: Only room creators can delete rooms
- Message persistence: SQLite with secure deletion

---

## ❗ TROUBLESHOOTING

### Common Issues

**Issue: Connection refused**
```bash
# Check if server is running
xtc status

# Ensure firewall allows port 8080
sudo ufw allow 8080
```

**Issue: Room creation failed**
```bash
# Check connection first
xtc status

# Verify room name format (must start with @)
xtc create:room @validroomname

```

---

## 🤝 Contributing
Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

---

## 📄 License
MIT License - feel free to use, modify, and distribute.

---

## 🌟 Why XtermChat?
- ✅ **No bloat** - Just pure terminal communication
- ✅ **Privacy-focused** - Self-hosted, no third parties
- ✅ **Lightweight** - Runs on Python, minimal dependencies
- ✅ **Fast** - REST API with JSON, no overhead
- ✅ **Secure** - Session encryption, auto-wipe on threats
- ✅ **Minimalist** - For developers who love the terminal

---
*Version 1.0.0 | Last Updated: March 2026*