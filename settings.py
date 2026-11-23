"""Account settings: bio, timed status, description, and password."""
import getpass


def read_description():
    print("Enter description lines. Type a single '.' to finish.")
    lines = []
    while True:
        line = input("description> ")
        if line == ".":
            break
        if sum(len(item) + 1 for item in lines) + len(line) > 10000:
            print("Description limit is 10000 characters.")
            continue
        lines.append(line)
    return "\n".join(lines)


def menu(api):
    while True:
        print("\nACCOUNT SETTINGS")
        print("1. Edit bio  2. Edit status  3. Edit description")
        print("4. Change password  5. Back")
        choice = input("settings>>> ").strip().lower()
        if choice in ("5", "back", "exit", "quit"):
            return
        if choice in ("1", "bio", "edit bio"):
            bio = input("New bio (160 characters max): ")
            if len(bio) > 160:
                print("Bio too long.")
                continue
            api.request("/me", "PATCH", {"bio": bio})
            print("Bio saved.")
        elif choice in ("2", "status", "edit status"):
            status = input("New status (280 characters max; blank clears): ")
            if len(status) > 280:
                print("Status too long.")
                continue
            if status:
                print("1. 48 hours (default)  2. save infinite  3. Cancel")
                duration = input(">>> ").strip()
                if duration in ("3", "cancel"):
                    continue
                if duration not in ("", "1", "2", "save infinite"):
                    print("Unknown duration.")
                    continue
                infinite = duration in ("2", "save infinite")
            else:
                infinite = False
            api.request("/me", "PATCH", {"status": status, "status_infinite": infinite})
            print("Status saved indefinitely." if infinite else
                  "Status cleared." if not status else "Status saved for 48 hours.")
        elif choice in ("3", "description", "edit description"):
            description = read_description()
            api.request("/me", "PATCH", {"description": description})
            print("Description saved.")
        elif choice in ("4", "password", "change password"):
            old = getpass.getpass("Current password: ")
            new = getpass.getpass("New password: ")
            if new != getpass.getpass("Confirm new password: "):
                print("Passwords do not match.")
            else:
                api.request("/me/password", "POST",
                            {"current_password": old, "new_password": new})
                print("Password changed.")
        else:
            print("Unknown setting.")
