"""Post rendering and interactions for Book and Shelf."""


def display(posts):
    if not posts:
        print("No posts yet.")
    for post in posts:
        if post.get("reposted_by"):
            print("\n↻ {} reposted".format(post["reposted_by"]))
        print("\n#{id}  @{username}  ·  {created_at}\n{body}".format(**post))
        print("{} {} likes    ↻ {} reposts".format(
            "♥" if post.get("liked_by_me") else "♡",
            post.get("like_count", 0), post.get("repost_count", 0)))


def interact(api, command):
    """Handle like/unlike/repost/unrepost and show a specific post."""
    action, _, argument = command.strip().partition(" ")
    action = action.lower()
    if action not in ("like", "unlike", "repost", "unrepost", "view"):
        return False
    try:
        post_id = int(argument.strip())
        if post_id <= 0:
            raise ValueError()
    except ValueError:
        print("Usage: {} POST_ID".format(action))
        return True
    path = "/posts/{}".format(post_id)
    if action == "view":
        display([api.request(path)])
    else:
        resource = "like" if action in ("like", "unlike") else "repost"
        method = "DELETE" if action in ("unlike", "unrepost") else "POST"
        api.request(path + "/" + resource, method)
        display([api.request(path)])
    return True


def publish(api, body):
    api.request("/posts", "POST", {"body": body})
    print("Post saved.")
