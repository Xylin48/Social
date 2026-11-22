# Social

A standalone, text-based social network extracted and rebuilt from the original `PyOs/Home/social.py`.

## Run

Requires Python 3.9 or newer. No third-party packages or Replit account needed.

```bash
python social.py
```

Choose `register` to make an account or `login` to sign in. Use `help` to see commands.

Commands: `post`, `feed`, `search USER`, `profile [USER]`, `settings`, `clear`, `help`, `logout`.

Accounts, password hashes and posts are saved in `~/.social/social.db` by default. Set `SOCIAL_DB` to customize the path.

**Note:** This is a local, single-computer application. Users share a feed when using the same database file; it is **not** an internet-connected multi-user service. Do not expose the SQLite database or terminal to untrusted network users.

## Origins

`original/social.py` preserves the PyOs version. The standalone version replaces Replit DB with SQLite, fixes account creation and login, and makes posts persistent. The original `book` command depended on an unrelated PyOs file and is not bundled.

## Test

```bash
python -m unittest discover -s tests -v
```
