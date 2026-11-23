"""Account settings for the network client."""
import getpass


def menu(api):
    print("1. Edit bio   2. Change password   3. Cancel")
    choice = input(">>> ").strip()
    if choice == "1":
        api.request("/me", "PATCH", {"bio": input("New bio: ")})
        print("Bio saved.")
    elif choice == "2":
        old = getpass.getpass("Current password: ")
        new = getpass.getpass("New password: ")
        if new != getpass.getpass("Confirm new password: "):
            print("Passwords do not match.")
        else:
            api.request("/me/password", "POST", {"current_password": old, "new_password": new})
            print("Password changed.")
