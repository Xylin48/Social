"""Book: browse the shared collection of Social posts."""
from urllib.parse import urlencode
from posts import display


def open_book(api):
    print("\nBOOK — The public message collection")
    display(api.request("/feed")["posts"])
    while True:
        command = input("book>>> ").strip()
        action, _, argument = command.partition(" ")
        action = action.lower()
        if action in ("back", "exit", "quit"):
            return
        if action in ("help", "?"):
            print("feed, user USERNAME, back")
        elif action in ("feed", ""):
            display(api.request("/feed")["posts"])
        elif action == "user" and argument:
            display(api.request("/feed?" + urlencode({"username": argument}))["posts"])
        else:
            print("Unknown Book command. Type help.")
