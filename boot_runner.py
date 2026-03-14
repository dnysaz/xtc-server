#!/usr/bin/env python3
"""
bot_runner.py — XtermChat Bot Background Runner
Dijalankan sebagai background process oleh bot.py.
Mengambil konfigurasi dari server, lalu menjalankan semua task terjadwal.

Usage (internal, jangan jalankan manual):
  python3 bot_runner.py --bot-id 1 --server http://ip:8080
                        --room alerts --bot-name MONITOR --pin UUID
"""

import argparse
import os
import sys
import time
import socket
import subprocess
import threading
import requests
import ssl
import json
from datetime import datetime, timedelta

# ─── CLI Args ─────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--bot-id",   required=True)
parser.add_argument("--server",   required=True)
parser.add_argument("--room",     required=True)
parser.add_argument("--bot-name", required=True)
parser.add_argument("--pin",      required=True)
args = parser.parse_args()

SERVER   = args.server.rstrip("/")
ROOM     = args.room
BOT_NAME = args.bot_name
PIN      = args.pin
BOT_ID   = args.bot_id

# ─── Core: kirim pesan ke room ────────────────────────────────────────────────

def send(content: str):
    try:
        requests.post(f"{SERVER}/send", json={
            "room":     ROOM,
            "user":     BOT_NAME,
            "pin":      PIN,
            "content":  content,
            "password": "",
        }, timeout=8)
    except Exception as e:
        log(f"[send error] {e}")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def now_str():
    return datetime.now().strftime("%d %b %Y %H:%M:%S")

def hostname():
    return socket.gethostname()

# ─── Ambil config dari server ─────────────────────────────────────────────────

def fetch_config() -> dict:
    try:
        res = requests.get(f"{SERVER}/bot/config/{BOT_ID}", timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        log(f"[config error] {e}")
    return {}

# ─── TASK: Resource Monitor ───────────────────────────────────────────────────

def task_resource(cfg: dict):
    try:
        import psutil
    except ImportError:
        send(f":warn {BOT_NAME}: psutil not installed on {hostname()}. Run: pip install psutil")
        return

    cpu  = psutil.cpu_percent(interval=2)
    ram  = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    cpu_t  = cfg.get("cpu_threshold",  80)
    ram_t  = cfg.get("ram_threshold",  85)
    disk_t = cfg.get("disk_threshold", 90)

    alerts = []
    if cpu  >= cpu_t:  alerts.append(f"  CPU   {cpu:.0f}%  (limit {cpu_t}%)")
    if ram  >= ram_t:  alerts.append(f"  RAM   {ram:.0f}%  (limit {ram_t}%)")
    if disk >= disk_t: alerts.append(f"  DISK  {disk:.0f}%  (limit {disk_t}%)")

    if alerts:
        send(f":warn RESOURCE ALERT on {hostname()} [{now_str()}]\n" + "\n".join(alerts))
        log(f"[resource] alert sent: {alerts}")
    else:
        log(f"[resource] ok — cpu:{cpu:.0f}% ram:{ram:.0f}% disk:{disk:.0f}%")

# ─── TASK: Process Monitor ────────────────────────────────────────────────────

def task_process(cfg: dict):
    proc_name    = cfg.get("process_name", "")
    auto_restart = cfg.get("auto_restart", False)

    if not proc_name:
        return

    try:
        import psutil
        running = any(proc_name.lower() in p.name().lower() for p in psutil.process_iter(["name"]))
    except ImportError:
        # Fallback: pakai pgrep
        result  = subprocess.run(["pgrep", "-f", proc_name], capture_output=True)
        running = result.returncode == 0

    if not running:
        msg = f":skull: PROCESS DOWN on {hostname()} [{now_str()}]\n  Process: {proc_name}"

        if auto_restart:
            try:
                subprocess.Popen(["systemctl", "restart", proc_name],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                msg += f"\n  :check Auto-restart triggered via systemctl"
                log(f"[process] restarted: {proc_name}")
            except Exception as e:
                msg += f"\n  :warn Auto-restart failed: {e}"

        send(msg)
        log(f"[process] down: {proc_name}")
    else:
        log(f"[process] ok: {proc_name} is running")

# ─── TASK: Uptime Watchdog ────────────────────────────────────────────────────

def task_uptime(cfg: dict):
    target = cfg.get("target_url", "")
    if not target:
        return

    try:
        start   = time.time()
        res     = requests.get(target, timeout=10)
        latency = int((time.time() - start) * 1000)

        if res.status_code >= 400:
            send(
                f":skull: DOWN — {target} [{now_str()}]\n"
                f"  Status : HTTP {res.status_code}\n"
                f"  Host   : {hostname()}"
            )
            log(f"[uptime] down: HTTP {res.status_code}")
        else:
            log(f"[uptime] ok: {target} — {res.status_code} ({latency}ms)")

    except requests.exceptions.ConnectionError:
        send(f":skull: DOWN — {target} [{now_str()}]\n  Reason: Connection refused\n  Host: {hostname()}")
        log(f"[uptime] down: connection error")
    except requests.exceptions.Timeout:
        send(f":skull: DOWN — {target} [{now_str()}]\n  Reason: Request timeout (>10s)\n  Host: {hostname()}")
        log(f"[uptime] down: timeout")
    except Exception as e:
        log(f"[uptime] error: {e}")

# ─── TASK: Port Checker ───────────────────────────────────────────────────────

def task_port(cfg: dict):
    ports   = cfg.get("ports", [8080])
    host    = "127.0.0.1"
    closed  = []

    for port in ports:
        try:
            with socket.create_connection((host, port), timeout=3):
                log(f"[port] open: {port}")
        except (ConnectionRefusedError, OSError):
            closed.append(port)
            log(f"[port] closed: {port}")

    if closed:
        send(
            f":warn PORT ALERT on {hostname()} [{now_str()}]\n"
            f"  Closed ports: {', '.join(str(p) for p in closed)}"
        )

# ─── TASK: Traffic Monitor ────────────────────────────────────────────────────

def task_traffic(cfg: dict):
    iface = cfg.get("interface", "eth0")

    try:
        import psutil
        stats_before = psutil.net_io_counters(pernic=True).get(iface)
        time.sleep(5)
        stats_after  = psutil.net_io_counters(pernic=True).get(iface)

        if not stats_before or not stats_after:
            log(f"[traffic] interface not found: {iface}")
            return

        mb_sent = (stats_after.bytes_sent - stats_before.bytes_sent) / (1024 * 1024) * 12  # per min
        mb_recv = (stats_after.bytes_recv - stats_before.bytes_recv) / (1024 * 1024) * 12

        log(f"[traffic] {iface} — sent:{mb_sent:.1f}MB/min recv:{mb_recv:.1f}MB/min")

        # Kirim laporan traffic setiap kali (sebagai informasi, bukan alert)
        send(
            f":globe: TRAFFIC REPORT {hostname()} [{now_str()}]\n"
            f"  Interface : {iface}\n"
            f"  Outbound  : {mb_sent:.1f} MB/min\n"
            f"  Inbound   : {mb_recv:.1f} MB/min"
        )
    except ImportError:
        log("[traffic] psutil not installed")

# ─── TASK: SSL Cert Checker ───────────────────────────────────────────────────

def task_ssl(cfg: dict):
    domain    = cfg.get("ssl_domain", "")
    warn_days = cfg.get("ssl_warn_days", 30)

    if not domain:
        return

    try:
        ctx  = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(), server_hostname=domain)
        conn.settimeout(10)
        conn.connect((domain, 443))
        cert       = conn.getpeercert()
        conn.close()

        expire_str = cert["notAfter"]  # 'Mar 14 12:00:00 2027 GMT'
        expire_dt  = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
        days_left  = (expire_dt - datetime.utcnow()).days

        log(f"[ssl] {domain} — {days_left} days until expiry")

        if days_left <= warn_days:
            send(
                f":warn SSL CERT ALERT — {domain} [{now_str()}]\n"
                f"  Expires in : {days_left} days  ({expire_dt.strftime('%d %b %Y')})\n"
                f"  Action     : Renew certificate soon!"
            )
    except ssl.SSLError as e:
        send(f":skull: SSL ERROR — {domain} [{now_str()}]\n  {e}")
        log(f"[ssl] error: {e}")
    except Exception as e:
        log(f"[ssl] check failed: {e}")

# ─── TASK: Log Watcher ────────────────────────────────────────────────────────

def task_log(cfg: dict, state: dict):
    log_file = cfg.get("log_file", "")
    keyword  = cfg.get("log_keyword", "ERROR")

    if not log_file or not os.path.exists(log_file):
        log(f"[log_watcher] file not found: {log_file}")
        return

    # Track posisi terakhir yang sudah dibaca
    last_pos  = state.get("log_pos", 0)
    new_lines = []

    try:
        with open(log_file, "r", errors="replace") as f:
            f.seek(last_pos)
            for line in f:
                if keyword.lower() in line.lower():
                    new_lines.append(line.strip())
            state["log_pos"] = f.tell()
    except Exception as e:
        log(f"[log_watcher] read error: {e}")
        return

    if new_lines:
        preview = "\n".join(f"  {l[:120]}" for l in new_lines[:5])
        extra   = f"\n  ...and {len(new_lines)-5} more" if len(new_lines) > 5 else ""
        send(
            f":warn LOG ALERT on {hostname()} [{now_str()}]\n"
            f"  File    : {log_file}\n"
            f"  Keyword : {keyword}\n"
            f"  Found   : {len(new_lines)} line(s)\n"
            f"{preview}{extra}"
        )
        log(f"[log_watcher] {len(new_lines)} lines matched '{keyword}'")

# ─── TASK: Disk Cleanup Alert ────────────────────────────────────────────────

def task_disk_clean(cfg: dict):
    threshold = cfg.get("disk_threshold", 90)

    try:
        import psutil
        disk = psutil.disk_usage("/")
        pct  = disk.percent

        if pct >= threshold:
            # List top 5 direktori terbesar
            result = subprocess.run(
                ["du", "-sh", "--max-depth=1", "/"],
                capture_output=True, text=True, timeout=10
            )
            top_dirs = "\n".join(
                f"  {l}" for l in result.stdout.strip().split("\n")[:6]
            )
            send(
                f":warn DISK FULL ALERT on {hostname()} [{now_str()}]\n"
                f"  Usage  : {pct:.0f}%  ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)\n"
                f"  Largest directories:\n{top_dirs}"
            )
            log(f"[disk_clean] alert: {pct:.0f}%")
        else:
            log(f"[disk_clean] ok: {pct:.0f}%")
    except ImportError:
        log("[disk_clean] psutil not installed")

# ─── TASK: Scheduled Report ───────────────────────────────────────────────────

def task_schedule(cfg: dict, state: dict):
    report_time = cfg.get("report_time", "08:00")
    today_key   = datetime.now().strftime("%Y-%m-%d")
    last_sent   = state.get("schedule_last", "")

    current_time = datetime.now().strftime("%H:%M")

    if current_time >= report_time and last_sent != today_key:
        state["schedule_last"] = today_key

        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            uptime_sec  = time.time() - psutil.boot_time()
            uptime_str  = str(timedelta(seconds=int(uptime_sec)))
        except ImportError:
            cpu = ram = disk = 0
            uptime_str = "N/A"

        send(
            f":star: DAILY REPORT — {hostname()} [{now_str()}]\n"
            f"  CPU    : {cpu:.0f}%\n"
            f"  RAM    : {ram:.0f}%\n"
            f"  Disk   : {disk:.0f}%\n"
            f"  Uptime : {uptime_str}"
        )
        log(f"[schedule] daily report sent")

# ─── TASK: Custom Command ─────────────────────────────────────────────────────

def task_custom(cfg: dict):
    command = cfg.get("shell_command", "")
    if not command:
        return

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=30
        )
        output = (result.stdout + result.stderr).strip()[:500]
        if output:
            send(
                f":box: COMMAND OUTPUT on {hostname()} [{now_str()}]\n"
                f"  $ {command}\n"
                f"  {output}"
            )
        log(f"[custom] ran: {command}")
    except subprocess.TimeoutExpired:
        send(f":warn COMMAND TIMEOUT on {hostname()}\n  $ {command}")
        log(f"[custom] timeout: {command}")
    except Exception as e:
        log(f"[custom] error: {e}")

# ─── Task dispatcher ─────────────────────────────────────────────────────────

TASK_HANDLERS = {
    "resource":   task_resource,
    "process":    task_process,
    "uptime":     task_uptime,
    "port":       task_port,
    "traffic":    task_traffic,
    "ssl":        task_ssl,
    "disk_clean": task_disk_clean,
    "custom":     task_custom,
    # log dan schedule butuh state, dihandle terpisah di loop
}

# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    log(f"[bot_runner] starting — bot_id:{BOT_ID} room:{ROOM} host:{hostname()}")

    config = fetch_config()
    if not config:
        log("[bot_runner] failed to fetch config from server. Exiting.")
        sys.exit(1)

    tasks = config.get("tasks", [])
    if not tasks:
        log("[bot_runner] no tasks configured. Exiting.")
        sys.exit(1)

    log(f"[bot_runner] loaded {len(tasks)} task(s): {[t['id'] for t in tasks]}")

    # Per-task state (untuk log watcher, scheduler)
    task_states = {t["id"]: {} for t in tasks}

    # Track kapan terakhir kali tiap task dijalankan
    last_run = {}

    while True:
        now_ts = time.time()

        for task in tasks:
            task_id  = task["id"]
            task_cfg = task.get("config", {})
            interval = task_cfg.get("interval", 5) * 60  # menit → detik

            # Cek apakah sudah waktunya dijalankan
            if now_ts - last_run.get(task_id, 0) < interval:
                continue

            last_run[task_id] = now_ts
            log(f"[bot_runner] running task: {task_id}")

            try:
                # Task dengan state
                if task_id == "log":
                    task_log(task_cfg, task_states[task_id])
                elif task_id == "schedule":
                    task_schedule(task_cfg, task_states[task_id])
                # Task normal
                elif task_id in TASK_HANDLERS:
                    TASK_HANDLERS[task_id](task_cfg)
                else:
                    log(f"[bot_runner] unknown task: {task_id}")
            except Exception as e:
                log(f"[bot_runner] error in task '{task_id}': {e}")

        time.sleep(30)  # cek tiap 30 detik apakah ada task yang perlu dijalankan

if __name__ == "__main__":
    main()