import sqlite3
from flask import Flask, jsonify, request, send_from_directory, g

app = Flask(__name__, static_folder="static", static_url_path="")
DB = "students.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                year INTEGER NOT NULL,
                grade REAL NOT NULL DEFAULT 0
            )"""
        )


def read_payload():
    d = request.get_json(silent=True) or {}
    try:
        data = {
            "roll_no": str(d.get("roll_no", "")).strip(),
            "name": str(d.get("name", "")).strip(),
            "email": str(d.get("email", "")).strip(),
            "course": str(d.get("course", "")).strip(),
            "year": int(d.get("year", 0)),
            "grade": float(d.get("grade", 0)),
        }
    except (TypeError, ValueError):
        return None, "Year and grade must be numbers."
    if not all([data["roll_no"], data["name"], data["email"], data["course"]]):
        return None, "Roll no, name, email and course are required."
    if "@" not in data["email"]:
        return None, "Enter a valid email address."
    if not 1 <= data["year"] <= 6:
        return None, "Year must be between 1 and 6."
    if not 0 <= data["grade"] <= 100:
        return None, "Grade must be between 0 and 100."
    return data, None


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/students")
def list_students():
    rows = get_db().execute("SELECT * FROM students ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/students")
def add_student():
    data, err = read_payload()
    if err:
        return jsonify(error=err), 400
    try:
        cur = get_db().execute(
            "INSERT INTO students (roll_no,name,email,course,year,grade) VALUES (?,?,?,?,?,?)",
            tuple(data.values()),
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That roll number already exists."), 409
    return jsonify(id=cur.lastrowid, **data), 201


@app.put("/api/students/<int:sid>")
def update_student(sid):
    data, err = read_payload()
    if err:
        return jsonify(error=err), 400
    try:
        cur = get_db().execute(
            "UPDATE students SET roll_no=?,name=?,email=?,course=?,year=?,grade=? WHERE id=?",
            (*data.values(), sid),
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That roll number already exists."), 409
    if cur.rowcount == 0:
        return jsonify(error="Student not found."), 404
    return jsonify(id=sid, **data)


@app.delete("/api/students/<int:sid>")
def delete_student(sid):
    cur = get_db().execute("DELETE FROM students WHERE id=?", (sid,))
    get_db().commit()
    if cur.rowcount == 0:
        return jsonify(error="Student not found."), 404
    return jsonify(deleted=sid)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)