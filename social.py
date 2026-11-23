"""Social's living room: the central interface for the public network."""
from urllib.parse import urlencode

from accounts import profile
from book import open_book
from posts import display, publish
from settings import menu as settings_menu


def living_room(api, username):
    print("\nWelcome to Social, {}. Type help to explore.".format(username))
    while True:
        try:
            command = input("social>>> ").strip()
            action, _, argument = command.partition(" ")
            action = action.lower()
            if action in ("logout", "exit", "quit"):
                try:
                    api.request("/logout", "POST", {})
                except ValueError:
                    pass
                print("Goodbye.")
                return
            if action in ("help", "?"):
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
            return


if __name__ == "__main__":
    from main import main
    main()
