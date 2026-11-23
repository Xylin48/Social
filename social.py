"""Social's living room: the central interface for the public network."""
from urllib.parse import urlencode

from accounts import profile
from book import open_book
from shelf import open_shelf
from posts import display, publish, identity
from settings import menu as settings_menu
from notifi import announce, open_notifications


def living_room(api, username):
    print("\nWelcome to Social, {}. Type help to explore.".format(identity(username, getattr(api, "is_dev", False))))
    while True:
        try:
            announce(api)
            print("[1. book] [2. shelf] [3. post] [4. profile] [5. settings] [6. help] [7. logout]")
            command = input("social>>> ").strip()
            action, _, argument = command.partition(" ")
            action = {"1": "book", "2": "shelf", "3": "post", "4": "profile",
                      "5": "settings", "6": "help", "7": "logout"}.get(action.lower(), action.lower())
            if action in ("logout", "exit", "quit"):
                try:
                    api.request("/logout", "POST", {})
                except ValueError:
                    pass
                finally:
                    api.token = None
                    api.is_dev = False
                print("Goodbye.")
                return
            if action in ("help", "?"):
                print("post, book, shelf, feed, search USER, profile [USER], follow USER, unfollow USER, following, notifications, settings, clear, logout")
            elif action in ("notifications", "notifi"):
                open_notifications(api)
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
                result = api.request("/me/following")
                users = result["users"]
                print("\n".join(identity(u, result.get("user_badges", {}).get(u)) for u in users) if users else "You aren\'t following anyone yet.")
            elif action == "feed":
                display(api.request("/feed")["posts"])
            elif action == "search":
                result = api.request("/users?" + urlencode({"q": argument or input("Username: ")}))
                users = result["users"]
                print("\n".join(identity(u, result.get("user_badges", {}).get(u)) for u in users) if users else "User not found.")
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
