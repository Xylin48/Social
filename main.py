"""Social's vestibule: connect, sign in, then enter the living room."""
from api import SocialAPI
from accounts import sign_in
from social import living_room


def main():
    api = SocialAPI()
    try:
        username = sign_in(api)
        if username is not None:
            living_room(api, username)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
