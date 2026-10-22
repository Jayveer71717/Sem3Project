import secrets
from functools import wraps

from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

import db

bp = Blueprint("auth", __name__)

HOME_BY_ROLE = {"admin": "admin.dashboard", "student": "student.dashboard"}

# Used to keep login timing similar when the username does not exist.
_DUMMY_HASH = "scrypt:32768:8:1$dummy$" + "0" * 128


# ---------- CSRF ----------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def check_csrf():
    sent = request.form.get("_csrf", "")
    if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
        abort(400, "Invalid or missing security token. Reload the page and try again.")


# ---------- Decorators ----------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user["role"] != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ---------- Load the signed-in user on every request ----------
@bp.before_app_request
def load_user():
    g.user = None
    if request.endpoint == "static":
        return
    user_id = session.get("user_id")
    if user_id is None:
        return
    user = db.fetch_one(
        "SELECT id, username, role, is_active FROM users WHERE id = %s", (user_id,)
    )
    if user is None or not user["is_active"]:
        session.clear()
        return
    g.user = user


# ---------- Routes ----------
@bp.route("/")
def index():
    if g.user:
        return redirect(url_for(HOME_BY_ROLE[g.user["role"]]))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for(HOME_BY_ROLE[g.user["role"]]))

    if request.method == "POST":
        check_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.fetch_one(
            "SELECT id, username, password_hash, role, is_active "
            "FROM users WHERE username = %s", (username,)
        )
        stored = user["password_hash"] if user else _DUMMY_HASH
        try:
            valid = check_password_hash(stored, password)
        except ValueError:
            valid = False

        if user and valid and user["is_active"]:
            session.clear()  # prevents session fixation
            session["user_id"] = user["id"]
            session.permanent = True
            db.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user["id"],))
            return redirect(url_for(HOME_BY_ROLE[user["role"]]))

        if user and valid and not user["is_active"]:
            flash("This account is disabled. Contact the administrator.", "error")
        else:
            flash("Incorrect username or password.", "error")
        return render_template("login.html", username=username), 401

    return render_template("login.html", username="")


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
