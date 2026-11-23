"""Account entry and profile commands."""
import getpass
from urllib.parse import quote, urlencode
from status import visible_status


def sign_in(api):
    print("Social — connected terminal social network")
    while True:
        action = input("\n[1. login] [2. register] [3. quit]\n>>> ").strip().lower()
        action = {"1": "login", "2": "register", "3": "quit"}.get(action, action)
        if action == "quit":
            return None
        if action not in ("login", "register"):
            print("Choose login, register, or quit.")
            continue
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        try:
            if action == "register":
                api.request("/register", "POST", {"username": username, "password": password})
            response = api.request("/login", "POST", {"username": username, "password": password})
            api.token = response["token"]
            print("Welcome back, " + response["username"] + "!")
            return response["username"]
        except ValueError as exc:
            print(exc)


def profile(api, username):
    """Interactive profile room; numbers and command names are equivalent."""
    path = "/users/" + quote(username, safe="")
    while True:
        data = api.request(path)
        owner = bool(data.get("is_self"))
        print("\nSOCIAL")
        print("────────────────────────────")
        print("Welcome to {}'s profile".format(data["username"]))
        print("\nStatus: " + (visible_status(data) or "(none)"))
        print("Followers: {} | Following: {}".format(
            data.get("followers", 0), data.get("following_count", 0)))
        print("\nBio: " + (data.get("bio") or "(none)"))
        print("\nDescription:\n" + (data.get("description") or "(none)"))
        print("────────────────────────────")
        if owner:
            print("[1. edit] [2. posts] [3. back] [notifications]")
        else:
            print("[1. follow] [2. unfollow] [3. back] [notifications]")
        try:
            choice = input("profile>>> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return
        if choice in ("notifications", "notifi"):
            from notifi import open_notifications
            open_notifications(api)
            continue
        if choice in ("3", "back"):
            return
        if owner:
            if choice in ("1", "edit"):
                from settings import menu
                menu(api)
            elif choice in ("2", "posts"):
                from posts import display
                display(api.request("/feed?" + urlencode({"username": data["username"]}))["posts"])
                try:
                    input("Press Enter to return to profile... ")
                except (KeyboardInterrupt, EOFError):
                    return
            else:
                print("Unknown command.")
        else:
            if choice in ("1", "follow", "2", "unfollow"):
                following = choice in ("1", "follow")
                api.request(path + "/follow", "POST" if following else "DELETE")
                print("Following updated.")
            else:
                print("Unknown command.")
