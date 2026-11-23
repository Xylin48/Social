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
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT ''")
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT ''")
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_set_at TIMESTAMPTZ")
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_infinite BOOLEAN NOT NULL DEFAULT FALSE")
        db.execute("CREATE INDEX IF NOT EXISTS posts_user_idx ON posts(username,id DESC)")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_lower_unique ON users(lower(username))")
        db.execute("""CREATE TABLE IF NOT EXISTS follows(
          follower TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
          followed TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          PRIMARY KEY(follower, followed),
          CHECK (follower <> followed))""")
        db.execute("CREATE INDEX IF NOT EXISTS follows_followed_idx ON follows(followed)")
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
    try:
        before = int(request.args.get("before", "0"))
        limit = int(request.args.get("limit", "30"))
        if before < 0 or not 1 <= limit <= 100:
            raise ValueError()
    except ValueError:
        return jsonify(error="Invalid pagination"), 400
    with connection() as db:
        if username:
            rows = db.execute(
                "SELECT id,username,body,created_at FROM posts WHERE lower(username)=lower(%s) AND (%s=0 OR id<%s) ORDER BY id DESC LIMIT %s",
                (username, before, before, limit + 1)).fetchall()
        else:
            rows = db.execute(
                "SELECT id,username,body,created_at FROM posts WHERE (%s=0 OR id<%s) ORDER BY id DESC LIMIT %s",
                (before, before, limit + 1)).fetchall()
    has_more = len(rows) > limit
    page = rows[:limit]
    return jsonify(posts=[dict(row, created_at=row["created_at"].isoformat()) for row in page],
                   next_before=page[-1]["id"] if has_more else None)


@app.get("/shelf")
@auth_required
def shelf():
    try:
        before = int(request.args.get("before", "0"))
        limit = int(request.args.get("limit", "30"))
        if before < 0 or not 1 <= limit <= 100:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify(error="Invalid pagination"), 400
    with connection() as db:
        rows = db.execute("""
            SELECT p.id,p.username,p.body,p.created_at FROM posts p
            JOIN follows f ON f.followed=p.username
            WHERE f.follower=%s AND (%s=0 OR p.id<%s)
            ORDER BY p.id DESC LIMIT %s
        """, (g.username, before, before, limit + 1)).fetchall()
    page = rows[:limit]
    return jsonify(posts=[dict(row, created_at=row["created_at"].isoformat()) for row in page],
                   next_before=page[-1]["id"] if len(rows)>limit else None)


@app.get("/me/following")
@auth_required
def following():
    with connection() as db:
        rows = db.execute("SELECT followed FROM follows WHERE follower=%s ORDER BY followed",
                          (g.username,)).fetchall()
    return jsonify(users=[row["followed"] for row in rows])


@app.post("/users/<username>/follow")
@auth_required
def follow(username):
    with connection() as db:
        user = db.execute("SELECT username FROM users WHERE lower(username)=lower(%s)",
                          (username,)).fetchone()
        if not user:
            return jsonify(error="User not found"), 404
        target = user["username"]
        if target == g.username:
            return jsonify(error="Cannot follow yourself"), 400
        db.execute("INSERT INTO follows(follower,followed) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                   (g.username, target))
    return jsonify(status="okay", following=True)


@app.delete("/users/<username>/follow")
@auth_required
def unfollow(username):
    with connection() as db:
        user = db.execute("SELECT username FROM users WHERE lower(username)=lower(%s)",
                          (username,)).fetchone()
        if not user:
            return jsonify(error="User not found"), 404
        db.execute("DELETE FROM follows WHERE follower=%s AND followed=%s",
                   (g.username, user["username"]))
    return jsonify(status="okay", following=False)


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
        row = db.execute("SELECT username,bio,description,status,status_set_at,status_infinite,created_at FROM users WHERE lower(username)=lower(%s)", (username,)).fetchone()
    if not row:
        return jsonify(error="User not found"), 404
    with connection() as db:
        stats = db.execute("""SELECT
          (SELECT count(*) FROM follows WHERE followed=%s) AS followers,
          (SELECT count(*) FROM follows WHERE follower=%s) AS following_count,
          EXISTS(SELECT 1 FROM follows WHERE follower=%s AND followed=%s) AS is_following""",
          (row["username"], row["username"], g.username, row["username"])).fetchone()
    return jsonify(username=row["username"], bio=row["bio"], description=row["description"],\n                   status=row["status"], status_set_at=row["status_set_at"].isoformat() if row["status_set_at"] else None,\n                   status_infinite=row["status_infinite"],
                   created_at=row["created_at"].isoformat(),
                   followers=stats["followers"], following_count=stats["following_count"],
                   is_following=stats["is_following"], is_self=(row["username"]==g.username))

@app.patch("/me")
@auth_required
def settings():
    data = request.get_json(silent=True) or {}
    allowed = {"bio", "description", "status", "status_infinite"}
    if not isinstance(data, dict) or not data or set(data) - allowed:
        return jsonify(error="Invalid settings"), 400
    if "status_infinite" in data and "status" not in data:
        return jsonify(error="Status duration requires a status"), 400
    limits = {"bio": 160, "description": 10000, "status": 280}
    for key, maximum in limits.items():
        if key in data and (not isinstance(data[key], str) or len(data[key]) > maximum):
            return jsonify(error="Invalid " + key), 400
    if "status_infinite" in data and not isinstance(data["status_infinite"], bool):
        return jsonify(error="Invalid status duration"), 400
    with connection() as db:
        if "bio" in data:
            db.execute("UPDATE users SET bio=%s WHERE username=%s", (data["bio"], g.username))
        if "description" in data:
            db.execute("UPDATE users SET description=%s WHERE username=%s", (data["description"], g.username))
        if "status" in data:
            db.execute("""UPDATE users SET status=%s,status_infinite=%s,
                       status_set_at=CASE WHEN %s='' THEN NULL ELSE now() END WHERE username=%s""",
                       (data["status"], data.get("status_infinite", False), data["status"], g.username))
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
