"""Global notification inbox and destination navigation."""
from accounts import profile
from posts import display


_last_announcement = {}


def announce(api):
    """Poll at a prompt boundary; never interrupt text being typed."""
    global _last_announcement
    data=api.request("/notifications/summary")
    snapshot=(data.get("unread"),data.get("unseen_posts"),data.get("latest_post_author"))
    identity = api.token
    if snapshot == _last_announcement.get(identity):
        return
    _last_announcement[identity]=snapshot
    count=data.get("unseen_posts",0)
    if count>=5:
        print("[Notification] You have {} unseen posts. Check your Shelf.".format(count))
    elif count:
        author=data.get("latest_post_author") or "Someone"
        if count==1:
            print("[Notification] {} made a post.".format(author))
        else:
            print("[Notification] {} new posts, latest by {}. Check your Shelf.".format(count,author))
    elif data.get("unread",0):
        print("[Notification] You have {} unread notifications. Type notifications.".format(data["unread"]))


def open_notifications(api):
    while True:
        items=api.request("/notifications").get("notifications",[])
        print("\nNOTIFICATIONS")
        if not items:
            print("No notifications.")
        for i,item in enumerate(items,1):
            kind=item["kind"]
            actor=item["actor"]
            message={"post":"{} made a post","like":"{} liked your post",
                     "repost":"{} reposted your post","follow":"{} started following you",
                     "profile":"{} updated their profile"}.get(kind,"{} activity").format(actor)
            print("{}. {}{}.".format(i,"● " if not item.get("read_at") else "",message))
        choice=input("notifi>>> ").strip().lower()
        if choice in ("back","exit","quit","0",""):
            return
        if not choice.isdigit() or not 1<=int(choice)<=len(items):
            print("Select a notification number, or back.")
            continue
        item=items[int(choice)-1]
        api.request("/notifications/{}/read".format(item["id"]),"POST",{})
        if item.get("post_id"):
            display([api.request("/posts/{}".format(item["post_id"]))])
        elif item["kind"] in ("follow","profile"):
            profile(api,item["actor"])
        else:
            print("The referenced content is unavailable.")
