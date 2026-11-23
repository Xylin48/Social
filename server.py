"""Social public API server. Requires Flask and psycopg (see requirements.txt)."""
import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, g
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL to a hosted PostgreSQL connection string")


def connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users(
          username TEXT PRIMARY KEY, salt BYTEA NOT NULL, password_hash BYTEA NOT NULL,
          bio TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        db.execute("""CREATE TABLE IF NOT EXISTS posts(
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          username TEXT NOT NULL REFERENCES users(username),
          body TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        db.execute("CREATE INDEX IF NOT EXISTS posts_user_idx ON posts(username,id DESC)")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_lower_unique ON users(lower(username))")
        db.execute("""CREATE TABLE IF NOT EXISTS sessions(
          token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES users(username)
          ON DELETE CASCADE, expires_at TIMESTAMPTZ NOT NULL)""")

def hashed(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
        if not token:
            return jsonify(error="Unauthorized"), 401
        with connection() as db:
            session = db.execute("SELECT username FROM sessions WHERE token_hash=%s AND expires_at>now()",
                                 (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not session:
            return jsonify(error="Unauthorized"), 401
        g.username = session["username"]
        return fn(*args, **kwargs)
    return wrapper

@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username, password = str(data.get("username", "")).strip(), str(data.get("password", ""))
    if not 3 <= len(username) <= 32 or not all(c.isascii() and (c.isalnum() or c == "_") for c in username):
        return jsonify(error="Username must be 3-32 ASCII letters, digits or underscores"), 400
    if len(password) < 8 or len(password) > 1024:
        return jsonify(error="Password must be 8-1024 characters"), 400
    salt = secrets.token_bytes(16)
    try:
        with connection() as db:
            db.execute("INSERT INTO users(username,salt,password_hash) VALUES(%s,%s,%s)",
                       (username, salt, hashed(password, salt)))
    except psycopg.errors.UniqueViolation:
        return jsonify(error="Username taken"), 409
    return jsonify(username=username), 201

@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username, password = str(data.get("username", "")), str(data.get("password", ""))
    with connection() as db:
        row = db.execute("SELECT username,salt,password_hash FROM users WHERE lower(username)=lower(%s)", (username,)).fetchone()
    if not row or not hmac.compare_digest(hashed(password, bytes(row["salt"])), bytes(row["password_hash"])):
        return jsonify(error="Invalid credentials"), 401
    token = secrets.token_urlsafe(40)
    with connection() as db:
        db.execute("INSERT INTO sessions(token_hash,username,expires_at) VALUES(%s,%s,%s)",
                   (hashlib.sha256(token.encode()).hexdigest(), row["username"],
                    datetime.now(timezone.utc) + timedelta(hours=12)))
    return jsonify(token=token, username=row["username"])

@app.post("/logout")
@auth_required
def logout():
    token = request.headers["Authorization"].replace("Bearer ", "", 1).strip()
    with connection() as db:
        db.execute("DELETE FROM sessions WHERE token_hash=%s",
                   (hashlib.sha256(token.encode()).hexdigest(),))
    return jsonify(status="okay")

@app.get("/feed")
@auth_required
def feed():
    username = request.args.get("username")
    with connection() as db:
        if username:
            rows = db.execute("SELECT id,username,body,created_at FROM posts WHERE lower(username)=lower(%s) ORDER BY id DESC LIMIT 30", (username,)).fetchall()
        else:
            rows = db.execute("SELECT id,username,body,created_at FROM posts ORDER BY id DESC LIMIT 30").fetchall()
    return jsonify(posts=[dict(row, created_at=row["created_at"].isoformat()) for row in rows])

@app.post("/posts")
@auth_required
def post():
    body = str((request.get_json(silent=True) or {}).get("body", "")).strip()
    if not 1 <= len(body) <= 2000:
        return jsonify(error="Post must contain 1-2000 characters"), 400
    with connection() as db:
        row = db.execute("INSERT INTO posts(username,body) VALUES(%s,%s) RETURNING id", (g.username, body)).fetchone()
    return jsonify(id=row["id"]), 201

@app.get("/users")
@auth_required
def search():
    q = request.args.get("q", "")[:32]
    with connection() as db:
        rows = db.execute("SELECT username FROM users WHERE username ILIKE %s ORDER BY username LIMIT 30",
                          ("%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%",)).fetchall()
    return jsonify(users=[row["username"] for row in rows])

@app.get("/users/<username>")
@auth_required
def profile(username):
    with connection() as db:
        row = db.execute("SELECT username,bio,created_at FROM users WHERE lower(username)=lower(%s)", (username,)).fetchone()
    if not row:
        return jsonify(error="User not found"), 404
    return jsonify(username=row["username"], bio=row["bio"], created_at=row["created_at"].isoformat())

@app.patch("/me")
@auth_required
def settings():
    bio = str((request.get_json(silent=True) or {}).get("bio", ""))
    if len(bio) > 160:
        return jsonify(error="Bio too long"), 400
    with connection() as db:
        db.execute("UPDATE users SET bio=%s WHERE username=%s", (bio, g.username))
    return jsonify(status="okay")

@app.post("/me/password")
@auth_required
def change_password():
    data = request.get_json(silent=True) or {}
    old = str(data.get("current_password", ""))
    new = str(data.get("new_password", ""))
    if not 8 <= len(new) <= 1024:
        return jsonify(error="New password must be 8-1024 characters"), 400
    with connection() as db:
        row = db.execute("SELECT salt,password_hash FROM users WHERE username=%s",
                         (g.username,)).fetchone()
        if not row or not hmac.compare_digest(hashed(old, bytes(row["salt"])),
                                               bytes(row["password_hash"])):
            return jsonify(error="Current password is incorrect"), 403
        salt = secrets.token_bytes(16)
        db.execute("UPDATE users SET salt=%s,password_hash=%s WHERE username=%s",
                   (salt, hashed(new, salt), g.username))
        token = request.headers["Authorization"].replace("Bearer ", "", 1).strip()
        db.execute("DELETE FROM sessions WHERE username=%s AND token_hash<>%s",
                   (g.username, hashlib.sha256(token.encode()).hexdigest()))
    return jsonify(status="okay")

@app.get("/health")
def health():
    return jsonify(status="okay")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
