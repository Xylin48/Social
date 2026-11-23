"""Global notification inbox and destination navigation."""
from accounts import profile
from posts import display, identity


_last_announcement = {}


def announce(api):
    """Poll at a prompt boundary; never interrupt text being typed."""
    global _last_announcement
    data=api.request("/notifications/summary")
    snapshot=(data.get("unread"),data.get("unseen_posts"),tuple(data.get("recent_post_authors", [])))
    session_id = api.token
    if snapshot == _last_announcement.get(session_id):
        return
    _last_announcement[session_id]=snapshot
    count=data.get("unseen_posts",0)
    if count>=5:
        print("[Notification] You have {} unseen posts. Check your Shelf.".format(count))
    elif count:
        authors = data.get("recent_post_authors") or []
        for author in reversed(authors[:count]):
            print("[Notification] {} made a post.".format(identity(author, data.get("recent_post_author_badges", {}).get(author))))
    elif data.get("unread",0):
        print("[Notification] You have {} unread notifications. Type notifications.".format(data["unread"]))


def open_notifications(api):
    before = None
    while True:
        path = "/notifications" + ("?before={}".format(before) if before else "")
        result = api.request(path)
        items = result.get("notifications", [])
        next_before = result.get("next_before")
        print("\nNOTIFICATIONS")
        if not items:
            print("No notifications.")
        for i,item in enumerate(items,1):
            kind=item["kind"]
            actor=identity(item["actor"], item.get("is_dev", False))
            message={"post":"{} made a post","like":"{} liked your post",
                     "repost":"{} reposted your post","follow":"{} started following you",
                     "profile":"{} updated their profile"}.get(kind,"{} activity").format(actor)
            print("{}. {}{}.".format(i,"● " if not item.get("read_at") else "",message))
        print("Type next for older notifications, or back to return." if next_before else "Type back to return.")
        choice=input("notifi>>> ").strip().lower()
        if choice == "next":
            if next_before is None:
                print("End of notifications.")
            else:
                before = next_before
            continue
        if choice == "refresh":
            before = None
            continue
        if choice in ("back","exit","quit","0",""):
            return
        if not choice.isdigit() or not 1<=int(choice)<=len(items):
            print("Select a notification number, or back.")
            continue
        item=items[int(choice)-1]
        try:
            if item.get("post_id"):
                post = api.request("/posts/{}".format(item["post_id"]))
                display([post])
                api.request("/notifications/{}/read".format(item["id"]), "POST", {})
            elif item["kind"] in ("follow", "profile"):
                profile(api, item["actor"])
                api.request("/notifications/{}/read".format(item["id"]), "POST", {})
            else:
                print("The referenced content is unavailable.")
        except ValueError as exc:
            print("Unable to open notification: {}".format(exc))
