"""Book: browse the shared collection of Social posts.

The original PyOs book.py was a placeholder that imported social.py.
This standalone implementation provides a post-reading view without
claiming the original placeholder had working reading functionality.
"""


def open_book(db, username):
    from social import feed, show_posts
    print(f'\n{username}\'s Book — recent posts')
    show_posts(feed(db))
    while True:
        command = input('book>>> ').strip()
        action, _, arg = command.partition(' ')
        if action in ('back', 'exit', 'quit'):
            return
        if action in ('help', '?'):
            print('Commands: feed, user USERNAME, back')
        elif action in ('feed', ''):
            show_posts(feed(db))
        elif action == 'user':
            if arg:
                show_posts(feed(db, arg))
            else:
                print('Usage: user USERNAME')
        else:
            print('Unknown Book command. Type help.')
