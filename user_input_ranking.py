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

# Allowed (protocol, token) combinations
combinations = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]

# Helper: calculate weighted average
def weighted_average(data, weights):
    return sum(data.get(key, 0) * weight for key, weight in weights.items())

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

print("Processing data and publishing scores for all investment types...")

# Process messages from input topic and send results to output topic
for message in consumer:
    pool = message.value
    project = pool.get('project')
    symbol = pool.get('symbol')

    # Only process allowed combinations
    if (project, symbol) not in combinations:
        continue

    try:
        for inv_type, weights in investment_types.items():
            score = weighted_average(pool, weights)
            result = {
                'project': project,
                'symbol': symbol,
                'score': round(score, 4),
                'type': inv_type,
                'timestamp': int(time.time()),
                'chain': pool.get('chain'),
                'apy_mean_30d': pool.get('apy_mean_30d'),
                'apy_change_1d': pool.get('apy_change_1d'),
                'apy_change_30d': pool.get('apy_change_30d'),
                'tvlUsd': pool.get('tvlUsd')
            }
            producer.send(OUTPUT_TOPIC, result)
            print(f"Sent to Kafka: {result}")
    except Exception as e:
        print(f"Skipping invalid entry: {e}")
