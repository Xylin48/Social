# Social

A standalone, text-based social network extracted and rebuilt from the original `PyOs/Home/social.py`.

## Run

Requires Python 3.9 or newer. No third-party packages or Replit account needed.

```bash
python social.py
```

Choose `register` to make an account or `login` to sign in. Use `help` to see commands.

Commands: `post`, `book`, `feed`, `search USER`, `profile [USER]`, `settings`, `clear`, `help`, `logout`.

Accounts, password hashes and posts are saved in `~/.social/social.db` by default. Set `SOCIAL_DB` to customize the path.

**Note:** This is a local, single-computer application. Users share a feed when using the same database file; it is **not** an internet-connected multi-user service. Do not expose the SQLite database or terminal to untrusted network users.

## Origins

`original/social.py` preserves the PyOs version. The standalone version replaces Replit DB with SQLite, fixes account creation and login, and makes posts persistent. The original `book` command ran `book.py`, which imported `social.py` and displayed the current username but otherwise was a placeholder. This repository now includes both the exact original `original/book.py` and a standalone `book.py` post-reading interface. The new reading behavior is an extension, not a claim about what the original placeholder already did. Original `usr.py` and `main.py` are preserved under `original/` as additional PyOs context.

## Test

```bash
python -m unittest discover -s tests -v
```
