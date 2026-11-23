"""Book: the reading room for posts on the shared Social network."""
from urllib.parse import urlencode
from posts import display, interact


def open_book(api):
    print("\nBOOK — Public posts")
    before = None
    username = None

    def show_page():
        params = {}
        if username:
            params["username"] = username
        if before:
            params["before"] = before
        path = "/feed" + ("?" + urlencode(params) if params else "")
        result = api.request(path)
        display(result["posts"])
        return result.get("next_before")

    next_before = show_page()
    while True:
        print("[1. feed] [2. user] [3. next] [4. back]")
        command = input("book>>> ").strip()
        action, _, argument = command.partition(" ")
        action = {"1": "feed", "2": "user", "3": "next", "4": "back"}.get(action.lower(), action.lower())
        if action in ("back", "exit", "quit"):
            return
        if action in ("help", "?"):
            print("feed, user USERNAME, next, view ID, like ID, unlike ID, repost ID, unrepost ID, back")
        elif action in ("feed", ""):
            username, before = None, None
            next_before = show_page()
        elif action == "user":
            target = argument or input("Username: ").strip()
            if target:
                username, before = target, None
                next_before = show_page()
        elif action == "next":
            if next_before is None:
                print("End of posts.")
            else:
                before = next_before
                next_before = show_page()
        elif interact(api, command):
            pass
        else:
            print("Unknown Book command. Type help.")
