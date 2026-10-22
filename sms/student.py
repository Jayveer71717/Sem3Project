from flask import Blueprint, g, render_template

import db
from auth import role_required

bp = Blueprint("student", __name__, url_prefix="/student")

from flask import Blueprint, g, render_template

import db
from auth import role_required

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/dashboard")
@role_required("student")
def dashboard():
    # Always filtered by the signed-in user's id, never by a URL parameter.
    student = db.fetch_one(
        "SELECT id, roll_no, full_name, course, semester FROM students WHERE user_id = %s",
        (g.user["id"],),
    )
    subjects, attendance, marks = [], [], []
    if student:
        subjects = db.fetch_all(
            "SELECT code, name, credits FROM subjects "
            "WHERE course = %s AND semester = %s ORDER BY code",
            (student["course"], student["semester"]),
        )
        attendance = db.fetch_all(
            "SELECT sub.code, sub.name, COUNT(a.id) AS total, "
            "COALESCE(SUM(a.status IN ('present','late')), 0) AS attended "
            "FROM subjects sub LEFT JOIN attendance a "
            "ON a.subject_id = sub.id AND a.student_id = %s "
            "WHERE sub.course = %s AND sub.semester = %s "
            "GROUP BY sub.id, sub.code, sub.name ORDER BY sub.code",
            (student["id"], student["course"], student["semester"]),
        )
        for row in attendance:
            row["attended"] = int(row["attended"])
            row["percent"] = round(100 * row["attended"] / row["total"]) if row["total"] else None
        marks = db.fetch_all(
            "SELECT sub.code, sub.name, m.exam_type, m.marks_obtained, m.max_marks "
            "FROM marks m JOIN subjects sub ON sub.id = m.subject_id "
            "WHERE m.student_id = %s "
            "ORDER BY sub.code, FIELD(m.exam_type,'internal','midterm','final','practical')",
            (student["id"],),
        )
    return render_template("student/dashboard.html", student=student,
                           subjects=subjects, attendance=attendance, marks=marks)