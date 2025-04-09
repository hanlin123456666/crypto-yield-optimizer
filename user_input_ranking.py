
from kafka import KafkaConsumer, KafkaProducer
import json
import time

# Kafka config
KAFKA_BROKER = 'kafka:9092'
INPUT_TOPIC = 'defillama_apy'
OUTPUT_TOPIC = 'investment_scores'

# Investment types and weights
investment_types = {
    'Yield maximize': {'apy_mean_30d': 0.7, 'apy_change_30d': 0.2, 'tvlUsd': 0.1},
    'Balanced investor': {'apy_mean_30d': 0.5, 'apy_change_30d': 0.3, 'tvlUsd': 0.2},
    'Conservative investor': {'apy_mean_30d': 0.4, 'apy_change_30d': 0.4, 'tvlUsd': 0.2}
}

# Helper: calculate weighted average
def weighted_average(data, weights):
    return sum(data.get(key, 0) * weight for key, weight in weights.items())

# Prompt user input
investment_type = input("Enter investment type (Yield maximize, Balanced investor, Conservative investor): ")

if investment_type not in investment_types:
    print("Invalid investment type. Choose from: Yield maximize, Balanced investor, Conservative investor.")
    exit()

weights = investment_types[investment_type]
results = []

# Set up Kafka Consumer
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='investment-score-processor',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Set up Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

# Process messages from input topic and send to output topic
print("Processing data and publishing investment scores...")
for message in consumer:
    pool = message.value
    try:
        score = weighted_average(pool, weights)
        result = {
            'project': pool.get('project'),
            'symbol': pool.get('symbol'),
            'score': round(score, 4),
            'type': investment_type,
            'timestamp': int(time.time())
        }
        producer.send(OUTPUT_TOPIC, result)
        print(f"Sent to Kafka: {result}")
    except Exception as e:
        print(f"Skipping invalid entry: {e}")
