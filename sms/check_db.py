"""Quick connection test:  python check_db.py"""
import mysql.connector

from config import Config

try:
    conn = mysql.connector.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME, connection_timeout=5,
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Connected to '{Config.DB_NAME}'. Tables found: {len(tables)}")
    for t in tables:
        print("  -", t)
    conn.close()
except mysql.connector.Error as err:
    print("Connection failed:", err)
    print("Check that MySQL is running in XAMPP and that schema.sql has been imported.")
