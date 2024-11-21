from atproto import Client
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve credentials from the environment
USERNAME = os.getenv("IDENTIFIER")
PASSWORD = os.getenv("PASSWORD")


def fetch_post_details(post_uri):
    """
    Fetch and display details of a Bluesky post using its AT-URI.

    Args:
        post_uri (str): The AT-URI of the post to fetch.

    Returns:
        dict: A dictionary containing the post details or None if not found.
    """
    try:
        # Initialize and log in to the client
        client = Client()
        client.login(USERNAME, PASSWORD)

        # Fetch the post details
        data = client.get_posts([post_uri])  # Pass the AT-URI as a list

        # Iterate over the list of posts
        for post in data.posts:
            if post.uri == post_uri:  # Match the post based on the AT-URI
                post_details = {
                    "author": post.author.handle,
                    "content": post.record.text,
                    "created_at": post.record.created_at,
                }
                return post_details

        print("Post not found in the response.")
        return None

    except Exception as e:
        print("Error:", e)
        return None

