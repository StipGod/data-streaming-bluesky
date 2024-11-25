import boto3
import json
import time
import logging
import uuid
from datetime import datetime

# Initialize AWS SDK clients
kinesis_client = boto3.client('kinesis', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
athena_client = boto3.client('athena', region_name='us-east-1')

# Configuration parameters
KINESIS_STREAM_NAME = 'flink-dynamodb'  # Replace with your Kinesis stream name
S3_BUCKET_NAME = 'st163-sentiment-analysis-bucket'  # Replace with your S3 bucket name
ATHENA_DATABASE = 'processed_data'  # Replace with your Athena database
ATHENA_OUTPUT_BUCKET = 's3://st163-sentiment-analysis-bucket/'  # Replace with your Athena query results output bucket

# Logger setup
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

def get_kinesis_data():
    """
    Retrieve data from the Kinesis stream and return it.
    """
    shard_iterator = get_shard_iterator(KINESIS_STREAM_NAME)
    if not shard_iterator:
        logger.error("Failed to get shard iterator. Exiting.")
        return

    while True:
        # Get records from the stream
        records_response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=100)
        records = records_response.get('Records', [])
        
        if records:
            for record in records:
                payload = json.loads(record['Data'])
                logger.info(f"Received record: {payload}")
                process_and_store_data(payload)

        # Get the next shard iterator to continue reading from Kinesis
        shard_iterator = records_response['NextShardIterator']
        time.sleep(1)  # Avoid rate-limiting

def get_shard_iterator(stream_name):
    """
    Get the shard iterator to start consuming records from the Kinesis stream.
    """
    response = kinesis_client.describe_stream(StreamName=stream_name)
    shards = response['StreamDescription']['Shards']
    
    if not shards:
        logger.error("No shards found in the stream.")
        return None
    
    # Use the first shard in the list
    shard_id = shards[0]['ShardId']
    
    # Get the shard iterator
    shard_iterator_response = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='LATEST'  # 'LATEST' to start consuming from the latest record
    )
    return shard_iterator_response['ShardIterator']

def process_and_store_data(payload):
    """
    Process the data and store it in S3.
    Here we assume the data is in JSON format, adjust if needed.
    """
    # Example: Adding a timestamp for when the record is processed
    payload['processed_at'] = datetime.utcnow().isoformat()
    
    # Store data in S3
    file_name = f"data/{uuid.uuid4()}.json"  # Unique filename per record
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=file_name,
        Body=json.dumps(payload),
        ContentType='application/json'
    )
    logger.info(f"Stored data in S3: {file_name}")

def query_athena():
    """
    Run an Athena query to process the data stored in S3.
    """
    query = f"""
    SELECT * FROM {ATHENA_DATABASE}.your_table
    WHERE processed_at > '2024-01-01'
    """

    # Start the Athena query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': ATHENA_DATABASE},
        ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_BUCKET}
    )

    # Get the query execution ID
    query_execution_id = response['QueryExecutionId']
    logger.info(f"Query started with execution ID: {query_execution_id}")
    
    # Wait for the query to complete
    while True:
        result = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = result['QueryExecution']['Status']['State']
        
        if status in ['SUCCEEDED', 'FAILED']:
            logger.info(f"Query execution status: {status}")
            break
        
        time.sleep(5)

    # Check results
    if status == 'SUCCEEDED':
        result_output = f"{ATHENA_OUTPUT_BUCKET}{query_execution_id}.csv"
        logger.info(f"Query results available at: {result_output}")
    else:
        logger.error("Query execution failed.")

if __name__ == "__main__":
    logger.info("Starting the Kinesis to S3 and Athena pipeline.")

    # Start consuming data from Kinesis and send to S3
    get_kinesis_data()
    
    # Optionally, run an Athena query
    query_athena()
