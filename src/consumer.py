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


# # Example usage:
# if __name__ == "__main__":
#     post_uri = "at://did:plc:cijycuyjpwzsyttamjy5fkkb/app.bsky.feed.post/3lbdmd624h22b"
#     details = fetch_post_details(post_uri)
#     if details:
#         print("Post Details:")
#         print("Author:", details["author"])
#         print("Content:", details["content"])
#         print("Posted At:", details["created_at"])

def at_uri_to_web_url(at_uri):
    """
    Converts an AT URI to a web URL for viewing on bsky.app.

    Args:
        at_uri (str): The AT URI of the record, e.g., 'at://<DID>/<COLLECTION>/<RKEY>'.

    Returns:
        str: The corresponding web URL for bsky.app or None if the input format is invalid.
    """
    try:
        # Validate and parse the AT URI
        if not at_uri.startswith("at://"):
            raise ValueError("Invalid AT URI format")

        parts = at_uri[5:].split("/")  # Remove 'at://' and split
        if len(parts) != 3:
            raise ValueError("AT URI must have three parts: DID, COLLECTION, and RKEY")

        did, collection, rkey = parts

        # Check if the collection matches app.bsky.feed.post
        if collection != "app.bsky.feed.post":
            raise ValueError("Unsupported collection for web URL conversion")

        # Construct the web URL
        web_url = f"https://bsky.app/profile/{did}/post/{rkey}"
        return web_url

    except ValueError as e:
        print(f"Error: {e}")
        return None
