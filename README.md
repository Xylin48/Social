# Social — terminal-based public social network

Social is a networked terminal social application adapted from PyOs. The original PyOs source is preserved under `original/`, and the earlier standalone SQLite prototype is archived under `legacy/`. The active application **does not use a local SQLite account or post database**.

## The house layout

- `main.py` — the vestibule: enter Social and sign in or register.
- `social.py` — the living room: central navigation after login.
- `book.py` — the public reading room: browse everyone’s posts, individual users, and older pages.
- `shelf.py` — the personal reading room: posts from followed accounts, with pagination.
- `posts.py` — write and display posts.
- `accounts.py` — login, registration, and profiles.
- `settings.py` — bio, status, description, and password changes.\n- `status.py` — client-local 48-hour status visibility clock; infinite statuses remain visible.
- `api.py` — shared HTTPS connection to the remote Social server.
- `client.py` — compatibility launcher that opens `main.py`.
- `server.py` — the separate Flask API backed by hosted Neon PostgreSQL.
- `passenger_wsgi.py` — cPanel Passenger entry point.

## Run the terminal application

Run `python main.py` on the user's machine. No third-party Python dependencies are needed for the terminal application. By default, it connects to `https://social.xylin48.site`. Set `SOCIAL_API_URL` only to point to a different API deployment for testing. The hosted server must be running; this repository does not imply that the public deployment has been verified.

The command `python client.py` is supported as an alias. `python social.py` also enters the same networked application.

In the living room: `post`, `book`, `shelf`, `feed`, `search USER`, `profile [USER]`, `follow USER`, `unfollow USER`, `following`, `settings`, `clear`, `logout`. Inside Book: `feed`, `user USERNAME`, `next`, `back`. Inside Shelf: `refresh`, `next`, `following`, `back`. Follow relationships and posts are stored centrally in Neon; Shelf queries them rather than duplicating posts.

## Deploy the server on Spaceship/cPanel

The server is distinct from the terminal application. Configure `DATABASE_URL` as a private environment variable in cPanel Setup Python App. Do not commit database credentials.

Use Python 3.9.23 (host limit), application root `social.xylin48.site`, URL `social.xylin48.site`, startup file `passenger_wsgi.py`, entry point `application`. Upload `server.py`, `passenger_wsgi.py`, and `requirements.txt` to that application root. Install requirements through cPanel and restart the application. Visit `https://social.xylin48.site/health` to check for `{"status":"okay"}`.

Python 3.9 is end-of-life. Before opening registration broadly, upgrade hosting to a supported runtime and add rate limiting, moderation/abuse controls, backups, monitoring, and deployment tests. Sessions are persisted as hashed tokens in PostgreSQL, rather than local process memory, but this is not a completed security audit.

## Tests

Run `python -m unittest discover -s tests -v`. Network room tests use a fake API; legacy SQLite tests exercise the archived prototype. Full integration tests against a disposable PostgreSQL database and the actual Spaceship deployment are still needed.

## Profile fields

Bio (160 characters) is a short permanent statement. Description (up to 10000 characters) supports multiline text, including imported plain-text profile descriptions. Status (280 characters) lasts 48 hours by default or can be set to `save infinite`. The server stores the status and creation timestamp in the shared database, while each terminal client evaluates expiry locally when viewing a profile. This needs no background timer or always-running client. The old status remains stored until replaced or cleared, but is hidden after expiration by current clients. A client with an incorrect system clock can display an incorrect result; older clients may not implement expiry.

## Numbered navigation

Login, the living room, Book, Shelf, profile pages, and Settings accept either the displayed number or its command name. Text commands with arguments such as `profile Alice`, `search Alice`, `follow Alice`, and `post Hello` remain supported. Profile pages have owner-specific actions (`edit`, `posts`, `back`) and visitor actions (`follow`, `unfollow`, `back`).

## Developer Easter egg

The server owns the global `[dev]` badge. By default the exact Social username `Xylin48` receives the badge. Set `SOCIAL_DEV_USERS` to a comma-separated list of **existing Social account usernames** (for example `SOCIAL_DEV_USERS=Xylin48` if that is your actual Social login). Matching is case-insensitive. Restart the server after changing this variable. Never grant the badge based on a client-provided flag or a password shortcut. Set `SOCIAL_DEV_USERS` to an empty string to disable all developer badges.

The server includes `is_dev` in successful login, profile, post/feed, shelf, and notification records, plus author badge mappings for username lists and recent post announcements. Updated terminal clients display `[dev]` beside developer names on the welcome screen, profile pages, posts, reposts, notifications, following lists, and search results. The marker is not part of the username and is not stored in user-submitted content. The server is authoritative, so a different client cannot assign the badge to itself.

This badge is cosmetic and **does not grant administrative permissions**. Configure the exact Social username before deployment; the repository owner name is not assumed to be the login name. Older terminal clients may not display the badge until updated.
