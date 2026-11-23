"""Shelf: posts from accounts the signed-in user follows."""
from urllib.parse import urlencode
from posts import display, interact
from notifi import open_notifications


def open_shelf(api):
    print("\nSHELF — Posts from people you follow")
    before = None

    def show_page():
        params = {"before": before} if before else {}
        result = api.request("/shelf" + ("?" + urlencode(params) if params else ""))
        if not result["posts"] and before is None:
            print("Your shelf is empty. Follow someone to fill it.")
        else:
            display(result["posts"])
        return result.get("next_before")

    next_before = show_page()
    while True:
        print("[1. refresh] [2. next] [3. following] [4. back]")
        command = input("shelf>>> ").strip()
        command = {"1": "refresh", "2": "next", "3": "following", "4": "back"}.get(command, command)
        if command in ("back", "exit", "quit"):
            return
        if command in ("help", "?"):
            print("refresh, next, following, view ID, like ID, unlike ID, repost ID, unrepost ID, notifications, back")
        elif command in ("refresh", ""):
            before = None
            next_before = show_page()
        elif command == "next":
            if next_before is None:
                print("End of posts.")
            else:
                before = next_before
                next_before = show_page()
        elif command == "following":
            users = api.request("/me/following")["users"]
            print("\n".join(users) if users else "You aren't following anyone yet.")
        elif action in ("notifications", "notifi"):
            open_notifications(api)
        elif command.lower() in ("notifications", "notifi"):
            open_notifications(api)
        elif interact(api, command):
            pass
        else:
            print("Unknown Shelf command. Type help.")
