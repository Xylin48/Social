"""Social's terminal command loop (legacy entry: python client.py)."""
from urllib.parse import urlencode
from api import SocialAPI
from accounts import sign_in, profile
from posts import display, publish
from network_book import open_book
from settings import menu as settings_menu


def main():
    api = SocialAPI()
    try:
        username = sign_in(api)
        if not username:
            return
        print("Type help for commands.")
        while True:
            try:
                command = input(">>> ").strip()
                action, _, argument = command.partition(" ")
                action = action.lower()
                if action in ("quit", "logout", "exit"):
                    try:
                        api.request("/logout", "POST", {})
                    except ValueError:
                        pass
                    print("Goodbye.")
                    return
                elif action == "help":
                    print("post, book, feed, search USER, profile [USER], settings, clear, logout")
                elif action == "post":
                    publish(api, argument or input("Write your post: "))
                elif action == "book":
                    open_book(api)
                elif action == "feed":
                    display(api.request("/feed")["posts"])
                elif action == "search":
                    users = api.request("/users?" + urlencode({"q": argument or input("Username: ")}))["users"]
                    print("\n".join(users) if users else "User not found.")
                elif action == "profile":
                    profile(api, argument or username)
                elif action == "settings":
                    settings_menu(api)
                elif action == "clear":
                    print("\033[2J\033[H", end="")
                elif command:
                    print("Unknown command. Type help.")
            except ValueError as exc:
                print(exc)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
