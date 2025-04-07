from kafka import KafkaConsumer
import couchdb
import json

# Kafka config
KAFKA_BROKER = 'kafka:9092'
TOPICS = ['defillama_apy']

# CouchDB config
COUCHDB_SERVER = 'http://admin:password@couchdb:5984/'  # CouchDB address
DBS = {'defillama_apy': 'defillama_pools'}

# Initialize CouchDB client
couch = couchdb.Server(COUCHDB_SERVER)

# Create database if it doesn't exist
for topic, db_name in DBS.items():
    if db_name not in couch:
        couch.create(db_name)
        print(f"Database '{db_name}' created.")
    else:
        print(f"Database '{db_name}' already exists.")

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    *TOPICS,  # Subscribe to Topics
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='defillama-db-consumer-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# Consume messages from Kafka and save to CouchDB
try:
    print("Starting to consume messages from Kafka topic 'defillama_apy' and store into CouchDB...")
    for message in consumer:
        topic = message.topic  # Topic name
        data = message.value

        db_name = DBS[topic]
        db = couch[db_name]

        db.save(data)
        print(f"Saved data to CouchDB (Database: {db_name}): {data}")
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    print("Consumer stopped.")
