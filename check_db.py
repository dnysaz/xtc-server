import sqlite3
import os

DB_NAME = "xtc.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def print_header(text, color_code):
    print(f"\n\033[{color_code}m" + "="*60)
    print(f"  {text.upper()}")
    print("="*60 + "\033[0m")

def inspect_table(table_name):
    """Membaca struktur dan data tabel secara dinamis."""
    if not os.path.exists(DB_NAME):
        print(f"\033[31m[!] Error: {DB_NAME} tidak ditemukan!\033[0m")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Cek Struktur Kolom
        print_header(f"Structure: {table_name}", "34")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        column_names = []
        for col in columns:
            column_names.append(col['name'])
            print(f" - {col['name']:15} | Type: {col['type']}")

        # 2. Cek Isi Data
        print_header(f"Data: {table_name}", "32")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(" (Table is empty)")
        else:
            # Print header tabel otomatis berdasarkan nama kolom
            header_str = " | ".join([f"{name.upper():12}" for name in column_names])
            print(f"\033[1m{header_str}\033[0m")
            print("-" * len(header_str))

            for row in rows:
                row_data = []
                for name in column_names:
                    val = str(row[name])
                    # Potong teks jika terlalu panjang agar tidak berantakan di terminal
                    display_val = (val[:10] + '..') if len(val) > 12 else val
                    row_data.append(f"{display_val:12}")
                print(" | ".join(row_data))

    except Exception as e:
        print(f"\033[31m[!] Error inspecting {table_name}: {e}\033[0m")
    finally:
        conn.close()

def main():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n\033[1mXTERMCHAT DATABASE INSPECTOR\033[0m")
        print("1. View Rooms (Gateways)")
        print("2. View Users (Identity Lock)")
        print("3. View Messages (Chat Logs)")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            inspect_table("rooms")
        elif choice == '2':
            inspect_table("users")
        elif choice == '3':
            inspect_table("messages")
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid option.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()