"""Create the first admin account (there is no public registration).

Usage:
  python seed.py admin                      # prompts for username and password
  python seed.py demo-student               # creates a test student login (student1 / Student@123)
"""
import getpass
import sys

import mysql.connector
from werkzeug.security import generate_password_hash

from config import Config


def connect():
    return mysql.connector.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME,
    )


def create_admin():
    username = input("Admin username [admin]: ").strip() or "admin"
    password = getpass.getpass("Admin password (min 8 chars): ")
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters.")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("Passwords do not match.")
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
        (username, generate_password_hash(password)),
    )
    conn.commit()
    print(f"Admin '{username}' created.")


def create_demo_student():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'student')",
        ("student1", generate_password_hash("Student@123")),
    )
    cur.execute(
        "INSERT INTO students (user_id, roll_no, full_name, email, class_level, section) "
    "VALUES (%s, %s, %s, %s, %s, %s)",
    (cur.lastrowid, "2026001", "Demo Student", "demo@example.com", 8, "A"),
    )
    conn.commit()
    print("Demo student created. Username: student1  Password: Student@123")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        {"admin": create_admin, "demo-student": create_demo_student}[action]()
    except KeyError:
        sys.exit(__doc__)
    except mysql.connector.Error as err:
        sys.exit(f"Database error: {err}")
