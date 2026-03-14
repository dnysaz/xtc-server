import sqlite3
import os
import datetime

DB_NAME = "xtc.db"

# ─── Colors (black/white + blue only) ────────────────────────────────────────

def B(t):  return f"\033[1;34m{t}\033[0m"   # Bold blue
def b(t):  return f"\033[34m{t}\033[0m"     # Blue
def W(t):  return f"\033[1m{t}\033[0m"      # Bold white
def D(t):  return f"\033[2m{t}\033[0m"      # Dim
def R(t):  return f"\033[31m{t}\033[0m"     # Red — errors only

# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ─── Format Helpers ───────────────────────────────────────────────────────────

def fmt_val(name, val):
    """Format nilai kolom: timestamp → tanggal, None → dash, truncate panjang."""
    if val is None:
        return D("—")

    # Unix timestamp → human readable
    if name == "created_at" and isinstance(val, int) and val > 0:
        try:
            return datetime.datetime.fromtimestamp(val).strftime("%d %b %Y  %H:%M")
        except:
            pass

    # String timestamp
    if name == "timestamp" and isinstance(val, str) and val:
        return val

    val = str(val)
    return val


def truncate(val, width):
    """Truncate teks dan hapus warna ANSI saat hitung panjang."""
    import re
    clean = re.sub(r'\033\[[0-9;]*m', '', val)
    if len(clean) > width:
        return val[:width - 2] + D("..")
    return val


def col_width(name, rows, col_names):
    """
    Hitung lebar kolom secara dinamis berdasarkan:
    - panjang nama kolom
    - panjang nilai terpanjang di kolom itu
    - batas max per kolom
    """
    MAX = {
        "id": 4, "pin": 20, "creator_pin": 20,
        "password": 14, "content": 35, "description": 28,
    }
    import re

    header_len = len(name)
    max_val    = max(
        (len(re.sub(r'\033\[[0-9;]*m', '', fmt_val(name, row[name]))) for row in rows),
        default=0
    )
    natural = max(header_len, max_val) + 2
    return min(natural, MAX.get(name, 40))


# ─── Inspect ──────────────────────────────────────────────────────────────────

def inspect_table(table_name):
    if not os.path.exists(DB_NAME):
        print(R(f"\n  [!] Database not found: {DB_NAME}\n"))
        return

    conn    = get_db_connection()
    cursor  = conn.cursor()

    try:
        # ── Schema ──────────────────────────────────────────────────────────
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns   = cursor.fetchall()
        col_names = [col['name'] for col in columns]

        # ── Rows ────────────────────────────────────────────────────────────
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        total = len(rows)

        # ── Header ──────────────────────────────────────────────────────────
        print()
        print(f"  {B('▸')} {W(table_name.upper())}  {D(f'{total} record(s)')}")
        print()

        if not rows:
            print(f"  {D('No records found.')}\n")
            return

        # ── Column widths (dynamic) ──────────────────────────────────────────
        widths = {name: col_width(name, rows, col_names) for name in col_names}

        # ── Top border ────────────────────────────────────────────────────────
        def border_top():
            parts = ["┌"]
            for i, name in enumerate(col_names):
                parts.append("─" * (widths[name] + 2))
                parts.append("┬" if i < len(col_names) - 1 else "┐")
            return "  " + "".join(parts)

        def border_mid():
            parts = ["├"]
            for i, name in enumerate(col_names):
                parts.append("─" * (widths[name] + 2))
                parts.append("┼" if i < len(col_names) - 1 else "┤")
            return "  " + "".join(parts)

        def border_bot():
            parts = ["└"]
            for i, name in enumerate(col_names):
                parts.append("─" * (widths[name] + 2))
                parts.append("┴" if i < len(col_names) - 1 else "┘")
            return "  " + "".join(parts)

        def render_row(cells, styled=False):
            parts = [b("│")]
            for i, (name, cell) in enumerate(zip(col_names, cells)):
                w   = widths[name]
                txt = truncate(cell, w)
                import re
                pad = w - len(re.sub(r'\033\[[0-9;]*m', '', txt))
                parts.append(f" {txt}{' ' * pad} ")
                parts.append(b("│"))
            return "  " + "".join(parts)

        # ── Print table ───────────────────────────────────────────────────────
        print(b(border_top()))

        # Column headers
        header_cells = [B(name.upper()) for name in col_names]
        print(render_row(header_cells))
        print(b(border_mid()))

        # Data rows
        for idx, row in enumerate(rows):
            cells = []
            for name in col_names:
                raw = fmt_val(name, row[name])
                # ID column → blue bold
                if name == "id":
                    cells.append(B(str(row[name])))
                # PIN columns → dim (sensitive)
                elif name in ("pin", "creator_pin", "password"):
                    import re
                    clean = re.sub(r'\033\[[0-9;]*m', '', raw)
                    cells.append(D(clean[:18] + "…" if len(clean) > 18 else clean))
                else:
                    cells.append(raw)
            print(render_row(cells))

            # Mid border every 5 rows untuk readability
            if (idx + 1) % 5 == 0 and (idx + 1) < total:
                print(b(border_mid()))

        print(b(border_bot()))
        print(f"\n  {D(f'Total: {total} row(s) in')} {b(table_name)}\n")

    except Exception as e:
        print(R(f"\n  [!] Error: {e}\n"))
    finally:
        conn.close()


# ─── Schema Viewer ────────────────────────────────────────────────────────────

def show_schema(table_name):
    """Tampilkan struktur kolom tabel."""
    if not os.path.exists(DB_NAME):
        print(R(f"\n  [!] Database not found: {DB_NAME}\n"))
        return

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print()
        print(f"  {B('▸')} {W('SCHEMA')}  {D(table_name.upper())}")
        print()

        for col in columns:
            pk  = B(" ◆ PK") if col['pk'] else ""
            nn  = D(" NOT NULL") if col['notnull'] else ""
            dft = D(f" DEFAULT {col['dflt_value']}") if col['dflt_value'] else ""
            print(f"  {b('│')}  {W(f'{col[1]:18}')} {b(f'{col[2]:10}')} {pk} {nn} {dft}")
        print()
    except Exception as e:
        print(R(f"\n  [!] Error: {e}\n"))
    finally:
        conn.close()


# ─── Menu ─────────────────────────────────────────────────────────────────────

def draw_menu():
    os.system('clear' if os.name == 'posix' else 'cls')

    print()
    print(f"  {B('┌─────────────────────────────────┐')}")
    print(f"  {B('│')}   {W('XTERMCHAT  DATABASE CHECKER')}   {B('│')}")
    print(f"  {B('└─────────────────────────────────┘')}")
    print()
    print(f"  {D('SELECT TABLE')}")
    print()

    items = [
        ("1", "rooms",    "Room list and config"),
        ("2", "users",    "Registered identities"),
        ("3", "messages", "Chat history"),
        ("─", "───",      ""),
        ("4", "schema",   "View table structure"),
        ("0", "exit",     "Quit"),
    ]

    for key, label, desc in items:
        if key == "─":
            print(f"  {D('  ─────────────────────────────')}")
            continue
        k    = B(f"[{key}]")
        lbl  = W(f"{label:12}")
        dsc  = D(desc)
        print(f"    {k}  {lbl}  {dsc}")

    print()


def main():
    while True:
        draw_menu()
        choice = input(f"  {b('›')} ").strip()

        if choice == '0':
            print(f"\n  {D('Goodbye.')}\n")
            break

        elif choice == '1':
            inspect_table("rooms")
            input(f"  {D('Press Enter to continue...')}")

        elif choice == '2':
            inspect_table("users")
            input(f"  {D('Press Enter to continue...')}")

        elif choice == '3':
            inspect_table("messages")
            input(f"  {D('Press Enter to continue...')}")

        elif choice == '4':
            os.system('clear' if os.name == 'posix' else 'cls')
            print()
            for tbl in ("rooms", "users", "messages"):
                show_schema(tbl)
            input(f"  {D('Press Enter to continue...')}")

        else:
            print(R(f"\n  [!] Invalid option: {choice}\n"))
            input(f"  {D('Press Enter to continue...')}")


if __name__ == "__main__":
    main()