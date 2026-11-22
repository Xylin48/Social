"""Social: standalone terminal social network, adapted from PyOs."""
import getpass
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3

DB_PATH = Path(os.environ.get('SOCIAL_DB', Path.home() / '.social' / 'social.db'))


def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      username TEXT PRIMARY KEY COLLATE NOCASE,
      salt BLOB NOT NULL, password_hash BLOB NOT NULL,
      bio TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL REFERENCES users(username),
      body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    db.commit()
    return db


def digest(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 310000)


def register(db, username, password):
    username = username.strip()
    if not (3 <= len(username) <= 32) or not all(c.isalnum() or c == '_' for c in username):
        raise ValueError('Username must be 3-32 letters, numbers, or underscores.')
    if len(password) < 8:
        raise ValueError('Password must contain at least 8 characters.')
    salt = secrets.token_bytes(16)
    try:
        db.execute('INSERT INTO users(username,salt,password_hash) VALUES(?,?,?)', (username, salt, digest(password, salt)))
        db.commit()
    except sqlite3.IntegrityError:
        raise ValueError('Username already exists.') from None


def authenticate(db, username, password):
    row = db.execute('SELECT username,salt,password_hash FROM users WHERE username=?', (username,)).fetchone()
    if row and hmac.compare_digest(digest(password, row[1]), row[2]):
        return row[0]
    return None


def create_post(db, username, body):
    body = body.strip()
    if not body or len(body) > 2000:
        raise ValueError('Post must contain 1-2000 characters.')
    db.execute('INSERT INTO posts(username,body) VALUES(?,?)', (username, body))
    db.commit()


def feed(db, username=None, limit=30):
    if username:
        return db.execute('SELECT id,username,body,created_at FROM posts WHERE username=? ORDER BY id DESC LIMIT ?', (username, limit)).fetchall()
    return db.execute('SELECT id,username,body,created_at FROM posts ORDER BY id DESC LIMIT ?', (limit,)).fetchall()


def show_posts(rows):
    if not rows:
        print('No posts yet.')
    for post_id, username, body, created in rows:
        print(f'\n#{post_id}  {username}  ·  {created}\n{body}')


def prompt_password(label='Password: '):
    return getpass.getpass(label)


def main():
    db = connect()
    print('Social — a text-based social network')
    user = None
    while user is None:
        print('\n[login] [register] [quit]')
        try:
            action = input('>>> ').strip().lower()
            if action == 'quit':
                return
            if action not in ('login', 'register'):
                print('Choose login, register, or quit.')
                continue
            username = input('Username: ').strip()
            password = prompt_password()
            if action == 'register':
                try:
                    register(db, username, password)
                    print('Account created. Welcome!')
                    user = username
                except ValueError as exc:
                    print(exc)
            else:
                user = authenticate(db, username, password)
                print(f'Welcome back, {user}!' if user else 'Invalid username or password.')
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye.')
            return
    print('Type help for commands.')
    while True:
        try:
            command = input('>>> ').strip()
            action, _, argument = command.partition(' ')
            action = action.lower()
            if action in ('quit', 'exit', 'logout'):
                print('Goodbye.')
                return
            elif action == 'help':
                print('Commands: post, feed, search USER, profile [USER], settings, clear, help, logout')
            elif action == 'clear':
                print('\033[2J\033[H', end='')
            elif action == 'post':
                body = argument or input('Write your post: ')
                try:
                    create_post(db, user, body)
                    print('Post saved.')
                except ValueError as exc:
                    print(exc)
            elif action == 'feed':
                show_posts(feed(db))
            elif action == 'search':
                query = argument or input('Search username: ')
                rows = db.execute('SELECT username FROM users WHERE username LIKE ? ORDER BY username LIMIT 30', ('%' + query.replace('%','\\%').replace('_','\\_') + '%',)).fetchall()
                print('\n'.join(row[0] for row in rows) if rows else 'User not found.')
            elif action == 'profile':
                target = argument or user
                row = db.execute('SELECT username,bio,created_at FROM users WHERE username=?', (target,)).fetchone()
                if row:
                    print(f'\n{row[0]} · Joined {row[2]}\nBio: {row[1] or "(none)"}')
                    show_posts(feed(db, row[0], 10))
                else:
                    print('User not found.')
            elif action == 'settings':
                print('1. Edit bio   2. Change password   3. Cancel')
                choice = input('>>> ').strip()
                if choice == '1':
                    bio = input('New bio (max 160 characters): ').strip()
                    if len(bio) <= 160:
                        db.execute('UPDATE users SET bio=? WHERE username=?', (bio, user)); db.commit(); print('Bio saved.')
                    else:
                        print('Bio too long.')
                elif choice == '2':
                    old = prompt_password('Current password: ')
                    if not authenticate(db, user, old):
                        print('Incorrect password.')
                    else:
                        new = prompt_password('New password: ')
                        if len(new) < 8:
                            print('Password must contain at least 8 characters.')
                        else:
                            salt = secrets.token_bytes(16)
                            db.execute('UPDATE users SET salt=?,password_hash=? WHERE username=?', (salt, digest(new,salt), user)); db.commit(); print('Password changed.')
            elif action == 'book':
                print('PyOs book integration is not included in standalone Social.')
            elif command:
                print('Unknown command. Type help.')
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye.')
            return


if __name__ == '__main__':
    main()
