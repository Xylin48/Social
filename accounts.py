"""Account entry and profile commands."""
import getpass
from urllib.parse import quote, urlencode
from posts import display
from status import visible_status


def sign_in(api):
    print("Social — connected terminal social network")
    while True:
        action = input("\n[login] [register] [quit]\n>>> ").strip().lower()
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
    data = api.request("/users/" + quote(username, safe=""))
    print(data["username"] + " — " + (data["bio"] or "(no bio)"))
    status = visible_status(data)
    if status:
        print("Status: " + status)
    if data.get("description"):
        print("Description:\n" + data["description"])
    if "followers" in data:
        print("Followers: {} | Following: {}".format(data["followers"], data["following_count"]))
        if not data.get("is_self"):
            print("You follow this user." if data.get("is_following") else "You do not follow this user.")
            print("Use 'follow {}' or 'unfollow {}' in Social.".format(data["username"], data["username"]))
    display(api.request("/feed?" + urlencode({"username": username}))["posts"])
