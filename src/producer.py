import random
import string
import json
import time
from datetime import datetime
import requests
from boto3 import client
from dotenv import load_dotenv
import os

load_dotenv()
stream_name = os.getenv('STREAMNAME')
region = os.getenv('REGION')
partition_key = 'BlueskyMessage'

kinesis_client = client('kinesis', region_name=region)


# News API Configuration
NEWS_API_KEY = '10fb3fc6cd794d9085a56f42b506ab1b'  # Replace with your News API key
NEWS_API_URL = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'

# Generate a random author handle
def generate_author_handle():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

# Fetch a random headline from the News API
def fetch_news_headline():
    try:
        response = requests.get(NEWS_API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        articles = response.json().get('articles', [])
        if articles:
            random_article = random.choice(articles)
            return random_article.get('title')  # Return the headline
    except requests.RequestException as e:
        print(f"Error fetching news: {e}")
    return None

# Generate dummy data
def generate_dummy_data():
    headline = fetch_news_headline()
    if headline:
        post_details = {
            "author": generate_author_handle(),
            "content": headline,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        return post_details
    else:
        return {"error": "Could not fetch headline"}

if __name__ == "__main__":
    print("Generating dummy data...")
    try:
        while True:
            post_details = generate_dummy_data()
            json_post_details = json.dumps(post_details)
            response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=json_post_details,
            PartitionKey=partition_key
        )
            print(response)
            time.sleep(5)  # Wait 10 seconds before generating the next data
    except KeyboardInterrupt:
        print("Stopped data generation.")