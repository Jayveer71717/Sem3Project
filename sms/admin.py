from datetime import date
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

import db
from auth import check_csrf, role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUSES = ("present", "absent", "late")
EXAMS = ("internal", "midterm", "final", "practical")


def _all_subjects():
    return db.fetch_all(
        "SELECT id, code, name, course, semester, credits FROM subjects "
        "ORDER BY course, semester, code"
    )


def _get_subject(subject_id):
    if not subject_id:
        return None
    return db.fetch_one(
        "SELECT id, code, name, course, semester FROM subjects WHERE id = %s",
        (subject_id,),
    )


def _dec(raw):
    try:
        d = Decimal((raw or "").strip())
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


@bp.route("/dashboard")
@role_required("admin")
def dashboard():
    counts = db.fetch_one(
        "SELECT COUNT(*) AS total, COALESCE(SUM(u.is_active), 0) AS active "
        "FROM students s JOIN users u ON u.id = s.user_id"
    )
    return render_template("admin/dashboard.html", counts=counts)


# ---------- Students (read-only list, shows course) ----------
@bp.route("/students")
@role_required("admin")
def students():
    rows = db.fetch_all(
        "SELECT s.roll_no, s.full_name, s.course, s.semester, u.is_active "
        "FROM students s JOIN users u ON u.id = s.user_id "
        "ORDER BY s.course, s.semester, s.roll_no"
    )
    return render_template("admin/students.html", students=rows)


# ---------- Subjects ----------
@bp.route("/subjects", methods=["GET", "POST"])
@role_required("admin")
def subjects():
    if request.method == "POST":
        check_csrf()
        f = request.form
        code = f.get("code", "").strip().upper()
        name = f.get("name", "").strip()
        course = f.get("course", "").strip()
        semester = f.get("semester", type=int)
        credits = f.get("credits", type=int) or 3
        if not (code and name and course and semester and 1 <= semester <= 12
                and 1 <= credits <= 20):
            flash("Fill in every field with valid values.", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO subjects (code, name, course, semester, credits) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (code, name, course, semester, credits),
                )
                flash(f"Subject {code} added.", "info")
                return redirect(url_for("admin.subjects"))
            except mysql.connector.IntegrityError:
                flash(f"Subject code {code} already exists.", "error")
    return render_template("admin/subjects.html", subjects=_all_subjects())


# ---------- Mark attendance ----------
@bp.route("/attendance", methods=["GET", "POST"])
@role_required("admin")
def attendance():
    src = request.form if request.method == "POST" else request.args
    subject = _get_subject(src.get("subject_id", type=int))
    try:
        class_date = date.fromisoformat(src.get("class_date", ""))
    except ValueError:
        class_date = date.today()

    if subject and request.method == "POST":
        check_csrf()
        if class_date > date.today():
            flash("You cannot mark attendance for a future date.", "error")
        else:
            cohort = db.fetch_all(
                "SELECT id FROM students WHERE course = %s AND semester = %s",
                (subject["course"], subject["semester"]),
            )
            conn = db.get_db()
            cur = conn.cursor()
            try:
                for s in cohort:
                    status = request.form.get(f"status_{s['id']}")
                    if status not in STATUSES:
                        continue
                    cur.execute(
                        "INSERT INTO attendance "
                        "(student_id, subject_id, class_date, status, marked_by) "
                        "VALUES (%s, %s, %s, %s, %s) "
                        "ON DUPLICATE KEY UPDATE status = VALUES(status), "
                        "marked_by = VALUES(marked_by)",
                        (s["id"], subject["id"], class_date, status, g.user["id"]),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
            flash("Attendance saved.", "info")
            return redirect(url_for("admin.attendance", subject_id=subject["id"],
                                    class_date=class_date.isoformat()))

    roster = []
    if subject:
        roster = db.fetch_all(
            "SELECT s.id, s.roll_no, s.full_name, a.status "
            "FROM students s LEFT JOIN attendance a "
            "ON a.student_id = s.id AND a.subject_id = %s AND a.class_date = %s "
            "WHERE s.course = %s AND s.semester = %s ORDER BY s.roll_no",
            (subject["id"], class_date, subject["course"], subject["semester"]),
        )
    return render_template("admin/attendance.html", subjects=_all_subjects(),
                           subject=subject, class_date=class_date.isoformat(),
                           today=date.today().isoformat(), roster=roster)


# ---------- Enter marks ----------
@bp.route("/marks", methods=["GET", "POST"])
@role_required("admin")
def marks():
    src = request.form if request.method == "POST" else request.args
    subject = _get_subject(src.get("subject_id", type=int))
    exam_type = src.get("exam_type") if src.get("exam_type") in EXAMS else "internal"

    if subject and request.method == "POST":
        check_csrf()
        max_marks = _dec(request.form.get("max_marks"))
        cohort = db.fetch_all(
            "SELECT id, roll_no FROM students WHERE course = %s AND semester = %s",
            (subject["course"], subject["semester"]),
        )
        to_save, bad = [], []
        if max_marks is None or max_marks <= 0 or max_marks > 999:
            flash("Max marks must be a positive number.", "error")
        else:
            for s in cohort:
                raw = request.form.get(f"marks_{s['id']}", "").strip()
                if not raw:
                    continue
                val = _dec(raw)
                if val is None or val < 0 or val > max_marks:
                    bad.append(s["roll_no"])
                else:
                    to_save.append((s["id"], val))
            if bad:
                flash("Invalid marks (must be between 0 and max) for: " + ", ".join(bad)
                      + ". Nothing was saved.", "error")
            else:
                conn = db.get_db()
                cur = conn.cursor()
                try:
                    for sid, val in to_save:
                        cur.execute(
                            "INSERT INTO marks (student_id, subject_id, exam_type, "
                            "marks_obtained, max_marks) VALUES (%s, %s, %s, %s, %s) "
                            "ON DUPLICATE KEY UPDATE marks_obtained = VALUES(marks_obtained), "
                            "max_marks = VALUES(max_marks)",
                            (sid, subject["id"], exam_type, val, max_marks),
                        )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    cur.close()
                flash(f"Saved marks for {len(to_save)} student(s).", "info")
                return redirect(url_for("admin.marks", subject_id=subject["id"],
                                        exam_type=exam_type))

    roster = []
    if subject:
        roster = db.fetch_all(
            "SELECT s.id, s.roll_no, s.full_name, m.marks_obtained, m.max_marks "
            "FROM students s LEFT JOIN marks m "
            "ON m.student_id = s.id AND m.subject_id = %s AND m.exam_type = %s "
            "WHERE s.course = %s AND s.semester = %s ORDER BY s.roll_no",
            (subject["id"], exam_type, subject["course"], subject["semester"]),
        )
    return render_template("admin/marks.html", subjects=_all_subjects(), subject=subject,
                           exam_type=exam_type, exams=EXAMS, roster=roster)