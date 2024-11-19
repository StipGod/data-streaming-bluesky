from atproto import Client
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve credentials from the environment
USERNAME = os.getenv("IDENTIFIER")
PASSWORD = os.getenv("PASSWORD")

try:
    # Initialize and log in to the client
    client = Client()
    client.login(USERNAME, PASSWORD)

    # Fetch the timeline
    data = client.get_timeline(cursor='', limit=1)

    # Extract the feed and cursor for pagination
    feed = data.feed
    next_page = data.cursor

    print(feed)

except Exception as e:
    print("Error:", e)