import json
import os
from boto3 import client
from dotenv import load_dotenv
from atproto import FirehoseSubscribeLabelsClient, firehose_models, models, parse_subscribe_labels_message
from consumer import fetch_post_details

load_dotenv()
stream_name = os.getenv('STREAMNAME')
region = os.getenv('REGION')
partition_key = 'BlueskyMessage'

kinesis_client = client('kinesis', region_name=region)

client = FirehoseSubscribeLabelsClient()


def on_message_handler(message: firehose_models.MessageFrame) -> None:
    labels_message = parse_subscribe_labels_message(message)
    if not isinstance(labels_message, models.ComAtprotoLabelSubscribeLabels.Labels):
        return

    for label in labels_message.labels:
        post_details = fetch_post_details(label.uri)
        json_post_details = json.dumps(post_details)
        
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=json_post_details,
            PartitionKey=partition_key
        )
        print(response)


client.start(on_message_handler)