import sqlite3
import os
import datetime

DB_NAME = "xtc.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def print_header(text, color_code):
    print(f"\n\033[{color_code}m" + "="*95)
    print(f"  {text.upper()}")
    print("="*95 + "\033[0m")

def inspect_table(table_name):
    if not os.path.exists(DB_NAME):
        print(f"\033[31m[!] Error: {DB_NAME} tidak ditemukan!\033[0m")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Struktur Kolom
        print_header(f"Structure: {table_name}", "34")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f" - {col['name']:15} | Type: {col['type']}")

        # 2. Data Tabel
        print_header(f"Data: {table_name}", "32")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(" (Table is empty)")
        else:
            # Konfigurasi lebar kolom yang dioptimalkan
            col_widths = {
                "id": 4, 
                "name": 10, 
                "room": 10,
                "creator": 12, 
                "sender": 12,
                "password": 10, 
                "description": 15, 
                "created_at": 18,     # Diperlebar untuk format tanggal
                "timestamp": 18,      # Diperlebar untuk format waktu
                "creator_pin": 15, 
                "pin": 15,
                "content": 25,
                "username": 12
            }

            col_names = [col['name'] for col in columns]
            
            # Render Header
            headers = []
            for name in col_names:
                w = col_widths.get(name, 12)
                headers.append(f"{name.upper():<{w}}")
            
            header_str = " | ".join(headers)
            print(f"\033[1;37m{header_str}\033[0m")
            print("-" * len(header_str))

            # Render Baris Data
            for row in rows:
                row_parts = []
                for name in col_names:
                    w = col_widths.get(name, 12)
                    val = row[name]
                    
                    # LOGIKA KHUSUS: Konversi Unix Timestamp (Integer) ke Tanggal
                    if name == "created_at" and isinstance(val, int) and val > 0:
                        try:
                            val = datetime.datetime.fromtimestamp(val).strftime('%d/%m/%y %H:%M')
                        except:
                            val = str(val)
                    else:
                        val = str(val) if val is not None else "-"
                    
                    # Truncate logic jika teks melebihi lebar kolom
                    display_val = (val[:w-3] + '..') if len(val) > w else val
                    
                    # Pewarnaan untuk data penting (ID atau Creator)
                    if name == "id":
                        row_parts.append(f"\033[33m{display_val:<{w}}\033[0m")
                    else:
                        row_parts.append(f"{display_val:<{w}}")
                
                print(" | ".join(row_parts))

    except Exception as e:
        print(f"\033[31m[!] Error: {e}\033[0m")
    finally:
        conn.close()

def main():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n\033[1;36mXTERMCHAT DATABASE CHECKER\033[0m")
        print("1. Rooms")
        print("2. Users")
        print("3. Messages")
        print("4. Exit\033[0m")
        
        choice = input("\n\033[1mSelect option (1-4): \033[0m").strip()
        if choice == '1': inspect_table("rooms")
        elif choice == '2': inspect_table("users")
        elif choice == '3': inspect_table("messages")
        elif choice == '4': break
        else: print("\033[31mInvalid option.\033[0m")
        
        input("\n\033[2mPress Enter to return to menu...\033[0m")

if __name__ == "__main__":
    main()