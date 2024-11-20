from atproto import FirehoseSubscribeLabelsClient, firehose_models, models, parse_subscribe_labels_message
from consumer import fetch_post_details
client = FirehoseSubscribeLabelsClient()


def on_message_handler(message: firehose_models.MessageFrame) -> None:
    labels_message = parse_subscribe_labels_message(message)
    if not isinstance(labels_message, models.ComAtprotoLabelSubscribeLabels.Labels):
        return

    for label in labels_message.labels:
        neg = '(NEG)' if label.neg else ''
        #print(f'[{label.cts}] ({label.src}) {label.uri} => {label.val} {neg}')
        post_details = fetch_post_details(label.uri)
        print(post_details["content"])


client.start(on_message_handler)