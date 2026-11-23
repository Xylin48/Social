"""Social terminal client for the shared public server."""
import getpass
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote

API = os.environ.get("SOCIAL_API_URL", "https://social.xylin48.site").rstrip("/")
token = None

def call(path, method="GET", payload=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None if payload is None else json.dumps(payload).encode()
    if data is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(API + path, data=data, headers=headers, method=method), timeout=15) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            message = json.load(exc).get("error", str(exc))
        except Exception:
            message = str(exc)
        raise ValueError(message) from exc
    except URLError as exc:
        raise ValueError("Cannot connect to Social server: " + str(exc.reason)) from exc

def display(posts):
    if not posts:
        print("No posts yet.")
    for post in posts:
        print("\n#{id}  {username}  ·  {created_at}\n{body}".format(**post))

def book():
    print("\nBOOK — The public message collection")
    display(call("/feed")["posts"])
    while True:
        cmd = input("book>>> ").strip()
        action, _, arg = cmd.partition(" ")
        if action in ("back", "exit", "quit"):
            return
        if action in ("help", "?"):
            print("feed, user USERNAME, back")
        elif action in ("feed", ""):
            display(call("/feed")["posts"])
        elif action == "user" and arg:
            display(call("/feed?" + urlencode({"username": arg}))["posts"])
        else:
            print("Unknown command. Type help.")

def main():
    global token
    print("Social — connected terminal social network")
    username = None
    while not username:
        try:
            cmd = input("\n[login] [register] [quit]\n>>> ").strip().lower()
            if cmd == "quit":
                return
            if cmd not in ("login", "register"):
                continue
            name = input("Username: ").strip()
            password = getpass.getpass("Password: ")
            if cmd == "register":
                call("/register", "POST", {"username": name, "password": password})
            result = call("/login", "POST", {"username": name, "password": password})
            username, token = result["username"], result["token"]
            print("Welcome back, " + username + "!")
        except ValueError as exc:
            print(exc)
    print("Type help for commands.")
    while True:
        try:
            cmd = input(">>> ").strip()
            action, _, arg = cmd.partition(" ")
            action = action.lower()
            if action in ("quit", "logout", "exit"):
                try:
                    call("/logout", "POST", {})
                except ValueError:
                    pass
                return
            elif action == "help":
                print("post, book, feed, search USER, profile [USER], settings, password, clear, logout")
            elif action == "post":
                call("/posts", "POST", {"body": arg or input("Write your post: ")})
                print("Post saved.")
            elif action == "book":
                book()
            elif action == "feed":
                display(call("/feed")["posts"])
            elif action == "search":
                users = call("/users?" + urlencode({"q": arg or input("Username: ")}))["users"]
                print("\n".join(users) if users else "User not found.")
            elif action == "profile":
                target = arg or username
                profile = call("/users/" + quote(target, safe=""))
                print(profile["username"] + " — " + (profile["bio"] or "(no bio)"))
                display(call("/feed?" + urlencode({"username": target}))["posts"])
            elif action == "password":
                old = getpass.getpass("Current password: ")
                new = getpass.getpass("New password: ")
                if new != getpass.getpass("Confirm new password: "):
                    print("Passwords do not match.")
                else:
                    call("/me/password", "POST", {"current_password": old, "new_password": new})
                    print("Password changed.")
            elif action == "settings":
                bio = input("New bio: ")
                call("/me", "PATCH", {"bio": bio})
                print("Bio saved.")
            elif action == "clear":
                print("\033[2J\033[H", end="")
            elif cmd:
                print("Unknown command. Type help.")
        except ValueError as exc:
            print(exc)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            return

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")
