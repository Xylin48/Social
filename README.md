# Social — text-based public social network

Social is a terminal-based social network extracted from PyOs. Its original source files are preserved in `original/`. The modernized `post` and `book` commands work together: post publishes messages, Book reads the shared message collection.

## Public network (PostgreSQL)

The project now includes a PostgreSQL-backed API and a terminal client. **A hosted database and API deployment are still required before anyone can use the public network.** The previous local SQLite prototype (`social.py`) remains for compatibility, but it is not the public-network client.

1. Create a hosted PostgreSQL database (Neon or Supabase). Copy its connection URL securely; **never commit it to GitHub**.
2. Deploy the API to a Python web host (a database provider alone does not host this Python API). Configure environment variable `DATABASE_URL` with the PostgreSQL connection URL. Install dependencies with `pip install -r requirements.txt`.
3. Start the API with `gunicorn --bind 0.0.0.0:\$PORT server:app` (substitute the port supplied by your host). The schema initializes on startup. Configure HTTPS and keep the database credentials server-side.
4. On each user's computer, set `SOCIAL_API_URL` to the deployed HTTPS API address and run `python client.py`. The client uses only the Python standard library.

For local development you can use `python server.py` after configuring `DATABASE_URL`, and set `SOCIAL_API_URL=http://127.0.0.1:8000`. Do **not** expose the Flask development server publicly.

## Commands

`register`, `login`, `post`, `book`, `feed`, `search USER`, `profile [USER]`, `settings`, `clear`, `logout`.

Inside Book: `feed`, `user USERNAME`, `back`.

## Security and operational limitations

Passwords are PBKDF2-hashed. Tokens expire after 12 hours, but sessions are currently stored **in API process memory**, so restarting or using multiple worker processes invalidates or separates sessions. Run a single API worker until shared session storage is implemented. Add rate limits, abuse controls, backups, monitoring, and more robust session handling before inviting untrusted public traffic. The public deployment is not complete just because code is present.

## Original PyOs sources

`original/social.py`, `original/book.py`, `original/usr.py`, and `original/main.py` are preserved for reference. The original Book was a placeholder that imported Social and printed the username. The current Book reader is a new implementation based on its connection to the posting interface, not functionality that existed in the placeholder.

## Local prototype

`python social.py` runs the earlier standalone SQLite prototype. `python -m unittest discover -s tests -v` runs its tests.
