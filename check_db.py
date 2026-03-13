import sqlite3
import os

DB_NAME = "xtc.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def print_header(text, color_code):
    print(f"\n\033[{color_code}m" + "="*85)
    print(f"  {text.upper()}")
    print("="*85 + "\033[0m")

def inspect_table(table_name):
    if not os.path.exists(DB_NAME):
        print(f"\033[31m[!] Error: {DB_NAME} tidak ditemukan!\033[0m")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Struktur
        print_header(f"Structure: {table_name}", "34")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f" - {col['name']:15} | Type: {col['type']}")

        # 2. Data
        print_header(f"Data: {table_name}", "32")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(" (Table is empty)")
        else:
            # Pengaturan lebar kolom custom agar lebih lega
            # id:4, room:10, sender:10, pin:15, content:20, timestamp:20
            col_widths = {
                "id": 4, "room": 8, "sender": 10, 
                "pin": 12, "content": 20, "timestamp": 20,
                "name": 10, "creator": 10, "creator_pin": 12, "password": 10
            }

            # Ambil nama kolom
            col_names = [col['name'] for col in columns]
            
            # Buat Header
            headers = []
            for name in col_names:
                w = col_widths.get(name, 10)
                headers.append(f"{name.upper():<{w}}")
            
            header_str = " | ".join(headers)
            print(f"\033[1m{header_str}\033[0m")
            print("-" * len(header_str))

            # Buat Baris Data
            for row in rows:
                row_parts = []
                for name in col_names:
                    w = col_widths.get(name, 10)
                    val = str(row[name]) if row[name] is not None else "-"
                    
                    # Truncate logic yang lebih cerdas
                    display_val = (val[:w-3] + '..') if len(val) > w else val
                    row_parts.append(f"{display_val:<{w}}")
                
                print(" | ".join(row_parts))

    except Exception as e:
        print(f"\033[31m[!] Error: {e}\033[0m")
    finally:
        conn.close()

def main():
    while True:
        # Gunakan clear agar terminal rapi setiap kali pindah menu
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n\033[1mXTERMCHAT DATABASE INSPECTOR v2.0\033[0m")
        print("1. View Rooms (Gateways)")
        print("2. View Users (Identity Lock)")
        print("3. View Messages (Chat Logs)")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        if choice == '1': inspect_table("rooms")
        elif choice == '2': inspect_table("users")
        elif choice == '3': inspect_table("messages")
        elif choice == '4': break
        else: print("Invalid option.")
        
        input("\n\033[2mPress Enter to return to menu...\033[0m")

if __name__ == "__main__":
    main()