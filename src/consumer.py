from atproto import FirehoseSubscribeLabelsClient


def fetch_post_details(client: FirehoseSubscribeLabelsClient, post_uri: str) -> dict:
    """
    Fetch and display details of a Bluesky post using its AT-URI.

    Args:
        client: The initialized ATProto Client.
        post_uri (str): The AT-URI of the post to fetch.

    Returns:
        dict: A dictionary containing the post details or None if not found.
    """
    try:
        data = client.get_posts([post_uri])  # Fetch post details
        for post in data.posts:
            if post.uri == post_uri:
                return {
                    "author": post.author.handle,
                    "content": post.record.text,
                    "created_at": post.record.created_at,
                }
        print("Post not found in the response.")
        return None
    except Exception as e:
        print(f"Error fetching post details: {e}")
        return None