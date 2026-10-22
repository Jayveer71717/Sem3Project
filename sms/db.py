"""MySQL access via mysql-connector-python.

One connection per request, stored on flask.g and closed automatically.
All queries must use %s placeholders (never string formatting).
"""
from contextlib import contextmanager

import mysql.connector
from flask import current_app, g


def _connect():
    cfg = current_app.config
    return mysql.connector.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        charset="utf8mb4",
        connection_timeout=5,
    )


def get_db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def fetch_one(sql, params=()):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()


def fetch_all(sql, params=()):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def execute(sql, params=()):
    """Run INSERT/UPDATE/DELETE, commit, and return the last inserted id."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


@contextmanager
def transaction():
    """Run several statements as one unit: all are saved, or none are.

        with db.transaction() as cur:
            cur.execute(...)
            cur.execute(...)
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_app(app):
    app.teardown_appcontext(close_db)