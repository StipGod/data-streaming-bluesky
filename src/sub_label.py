import os
import time
from queue import Queue
from threading import Thread
from dotenv import load_dotenv
from atproto import FirehoseSubscribeLabelsClient, firehose_models, parse_subscribe_labels_message, models
from proto_session import init_client
from consumer import fetch_post_details

load_dotenv()

# Constants
RATE_LIMIT = 10  # Number of posts to process per minute
PROCESSING_INTERVAL = 15  # Seconds to wait between processing batches
QUEUE_SIZE = 100  # Maximum size of the queue

# Initialize the queue for post URIs
uri_queue = Queue(maxsize=QUEUE_SIZE)


def on_message_handler(message: firehose_models.MessageFrame) -> None:
    """Handle incoming messages and add AT-URIs to the queue."""
    labels_message = parse_subscribe_labels_message(message)
    if not isinstance(labels_message, models.ComAtprotoLabelSubscribeLabels.Labels):
        return

    for label in labels_message.labels:
        if uri_queue.full():
            print("Queue is full. Skipping new URIs.")
        else:
            uri_queue.put(label.uri)
            print(f"Added AT-URI to queue: {label.uri}")


def process_queue():
    """Fetch and print post details from the queue."""
    client = init_client()  # Use session-managed Client
    while True:
        if uri_queue.empty():
            time.sleep(PROCESSING_INTERVAL)
            continue

        uris_to_process = []
        while not uri_queue.empty() and len(uris_to_process) < RATE_LIMIT:
            uris_to_process.append(uri_queue.get())

        for post_uri in uris_to_process:
            #print(f"Processing AT-URI: {post_uri}")
            try:
                post_details = fetch_post_details(client, post_uri)
                if post_details:
                    #print(f"Post Content: {post_details['content']}")
                    print(post_details)
                else:
                    print("Failed to fetch post details.")
            except Exception as e:
                print(f"Error processing AT-URI {post_uri}: {e}")

        # Throttle API requests
        time.sleep(60 / RATE_LIMIT)


if __name__ == "__main__":
    print("Starting ATProto queue processor...")

    # Start Firehose listener in a separate thread
    firehose_client = FirehoseSubscribeLabelsClient()
    listener_thread = Thread(target=firehose_client.start, args=(on_message_handler,))
    listener_thread.start()

    # Start the post processing queue
    processor_thread = Thread(target=process_queue)
    processor_thread.start()

    # Join threads
    listener_thread.join()
    processor_thread.join()