# consume data from topic (investment_scores) and save to db
from kafka import KafkaConsumer
import couchdb
import json
import time

# Kafka config
KAFKA_BROKER = 'kafka:9092'
TOPIC = 'investment_scores'

# CouchDB config
COUCHDB_SERVER = 'http://admin:password@couchdb-service:5984/'
DB_NAME = 'investment_scores'

# Initialize CouchDB client
couch = couchdb.Server(COUCHDB_SERVER)

# Create database if it doesn't exist
if DB_NAME not in couch:
    couch.create(DB_NAME)
    print(f"Database '{DB_NAME}' created.")
else:
    print(f"Database '{DB_NAME}' already exists.")

db = couch[DB_NAME]

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='investment-score-consumer-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# Consume messages and store in CouchDB
try:
    print(f"Consuming from Kafka topic '{TOPIC}' and storing into CouchDB '{DB_NAME}'...")
    for message in consumer:
        data = message.value
        data['timestamp'] = data.get('timestamp', int(time.time()))  # Add timestamp if missing
        db.save(data)
        print(f"Saved to CouchDB: {data}")
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    print("Consumer stopped.")
