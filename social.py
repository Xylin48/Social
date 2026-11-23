"""Social's living room: the central interface for the public network."""
from urllib.parse import urlencode

from accounts import profile
from book import open_book
from shelf import open_shelf
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
                print("post, book, shelf, feed, search USER, profile [USER], follow USER, unfollow USER, following, settings, clear, logout")
            elif action == "post":
                publish(api, argument or input("Write your post: "))
            elif action == "book":
                open_book(api)
            elif action == "shelf":
                open_shelf(api)
            elif action in ("follow", "unfollow"):
                if not argument:
                    print("Usage: {} USERNAME".format(action))
                else:
                    from urllib.parse import quote
                    api.request("/users/" + quote(argument, safe="") + "/follow",
                                "POST" if action == "follow" else "DELETE")
                    print("Following updated.")
            elif action == "following":
                users = api.request("/me/following")["users"]
                print("\n".join(users) if users else "You aren't following anyone yet.")
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
