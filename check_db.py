import sqlite3
import os

def check_database():
    db_path = 'xtc.db' # Pastikan nama file sesuai
    
    if not os.path.exists(db_path):
        print(f"\033[31m[!] Error: File '{db_path}' tidak ditemukan!\033[0m")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n\033[34m" + "="*50)
        print("  STRUCTURE: TABLE 'rooms'")
        print("="*50 + "\033[0m")
        
        # Mengecek struktur kolom
        cursor.execute("PRAGMA table_info(rooms)")
        columns = cursor.fetchall()
        for col in columns:
            # col[1] adalah nama kolom, col[2] adalah tipe data
            print(f" - Column: {col[1]:15} | Type: {col[2]}")

        print("\n\033[32m" + "="*50)
        print("  DATA: TABLE 'rooms'")
        print("="*50 + "\033[0m")
        
        # Mengecek isi data
        cursor.execute("SELECT id, name, creator, creator_pin FROM rooms")
        rows = cursor.fetchall()
        
        if not rows:
            print(" (Table is empty)")
        for row in rows:
            print(f" ID: {row[0]} | Room: {row[1]:10} | Creator: {row[2]:10} | PIN: {row[3]}")
            
        print("\n" + "="*50)

    except Exception as e:
        print(f"\033[31m[!] Error: {e}\033[0m")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()