"""Display Social posts in the terminal."""


def display(posts):
    if not posts:
        print("No posts yet.")
    for post in posts:
        print("\n#{id}  {username}  ·  {created_at}\n{body}".format(**post))


def publish(api, body):
    api.request("/posts", "POST", {"body": body})
    print("Post saved.")
