from atproto import Client
try:
    client = Client()
    client.login('sgomeza13.bsky.social', 'rdH38zx+')

    data = client.get_timeline(cursor='', limit=1)

    feed = data.feed
    next_page = data.cursor

    print(feed)

except Exception as e:
    print(e)