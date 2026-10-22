# Student Management System

Flask + MySQL (XAMPP) college ERP. **Module 1: setup, database connection and authentication.**

## Setup on Windows with XAMPP

1. **Install tools**: XAMPP (https://www.apachefriends.org) and Python 3.10+ (tick "Add python.exe to PATH" in the installer).
2. **Start MySQL**: open the XAMPP Control Panel and click **Start** next to **MySQL**. Apache is not needed.
3. **Create the database**: open http://localhost/phpmyadmin, go to the **Import** tab, choose `schema.sql`, click **Import**.
   (Or in a terminal: `C:\xampp\mysql\bin\mysql.exe -u root < schema.sql`)
4. **Create a virtual environment and install packages** (Command Prompt, inside the project folder):
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. **Check the connection**: `python check_db.py` should list 7 tables.
   If your MySQL root user has a password, set it first: `set DB_PASSWORD=yourpassword`
6. **Create the admin account**: `python seed.py admin`
7. *(Optional, for testing student login)*: `python seed.py demo-student` → `student1` / `Student@123`
8. **Run**: `python app.py`, then open http://127.0.0.1:5000

For anything other than local testing, set a long random `SECRET_KEY` (`set SECRET_KEY=...`).

## Structure

| File | Purpose |
|---|---|
| `app.py` | App factory, error pages, blueprint registration |
| `config.py` | Settings (DB + session), overridable via environment variables |
| `db.py` | MySQL connection per request, `fetch_one` / `fetch_all` / `execute` helpers |
| `auth.py` | Login, logout, CSRF check, `login_required`, `role_required` |
| `admin.py`, `student.py` | Role-specific blueprints (dashboards for now) |
| `seed.py`, `check_db.py` | Create first admin / demo student; test the DB connection |
| `schema.sql` | Full database schema |

## Security notes
Passwords are hashed with Werkzeug (never stored in plain text). Sessions are reset on login, cookies are HttpOnly + SameSite=Lax, every POST form carries a CSRF token, all SQL uses parameters, and disabled accounts are signed out on their next request. Student pages will always filter by the signed-in user's id, never by an id in the URL.
