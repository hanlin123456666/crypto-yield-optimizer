# pull data from topic and compute scores
# then save scored results to investment_scores in couchDB

import json
import couchdb
from kafka import KafkaConsumer

# Kafka config
KAFKA_BROKER = 'kafka:9092'
TOPIC = 'defillama_apy'

# CouchDB config
COUCHDB_URL = 'http://admin:password@couchdb-service:5984/'
RESULT_DB = 'investment_scores'

# Allowed combinations
combinations = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]

# Investment strategy weights
investment_types = {
    'Yield maximize': {'apy_mean_30d': 0.7, 'apy_change_30d': 0.2, 'tvlUsd': 0.1},
    'Balanced investor': {'apy_mean_30d': 0.5, 'apy_change_30d': 0.3, 'tvlUsd': 0.2},
    'Conservative investor': {'apy_mean_30d': 0.4, 'apy_change_30d': 0.4, 'tvlUsd': 0.2}
}

# Prompt user for investment type
investment_type = input("Enter investment type (Yield maximize, Balanced investor, Conservative investor): ")
if investment_type not in investment_types:
    print("Invalid input.")
    exit()

weights = investment_types[investment_type]

# Connect to CouchDB
couch = couchdb.Server(COUCHDB_URL)
if RESULT_DB not in couch:
    couch.create(RESULT_DB)
result_db = couch[RESULT_DB]

# Connect to Kafka
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='model-consumer-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Scoring function
def weighted_score(data, weights):
    return sum(data.get(k, 0) * w for k, w in weights.items())

print("Listening for data...")

# Collect, filter, and score
try:
    for msg in consumer:
        data = msg.value
        protocol = data.get('project')
        token = data.get('symbol')
        if (protocol, token) in combinations:
            score = weighted_score(data, weights)
            result = {
                'protocol': protocol,
                'token': token,
                'score': round(score, 4),
                'chain': data.get('chain'),
                'apy_mean_30d': data.get('apy_mean_30d'),
                'apy_change_1d': data.get('apy_change_1d'),
                'apy_change_30d': data.get('apy_change_30d'),
                'tvlUsd': data.get('tvlUsd'),
                'investment_type': investment_type
            }
            result_db.save(result)
            print(f"Saved scored result to CouchDB: {result}")
except KeyboardInterrupt:
    print("Stopped by user.")
except Exception as e:
    print(f"Error: {e}")
