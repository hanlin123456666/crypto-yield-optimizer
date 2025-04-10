from kafka import KafkaConsumer, KafkaProducer
import json
import time
import numpy as np

# Kafka configuration details
KAFKA_BROKER = 'kafka:9092'
INPUT_TOPIC = 'defillama_apy'
OUTPUT_TOPIC = 'investment_scores'

# Definitions for the types of investments and their respective weights
investment_types = {
    'Yield maximize': {'apy_mean_30d': 0.7, 'apy_change_30d': 0.2, 'tvlUsd': 0.1},
    'Balanced investor': {'apy_mean_30d': 0.5, 'apy_change_30d': 0.3, 'tvlUsd': 0.2},
    'Conservative investor': {'apy_mean_30d': 0.4, 'apy_change_30d': 0.4, 'tvlUsd': 0.2}
}

# Protocols and tokens allowed for processing
combinations = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]

# Helper function to apply logarithmic scaling to tvlUsd
def log_scale(value):
    return np.log1p(max(0, value))

# Function to calculate weighted average using scaled tvlUsd for scoring
def weighted_average(data, weights):
    # Creating a copy of the data to avoid modifying the original input
    modified_data = data.copy()
    if 'tvlUsd' in modified_data:
        modified_data['tvlUsd'] = log_scale(modified_data['tvlUsd'])
    return sum(modified_data.get(key, 0) * weight for key, weight in weights.items())

# Setting up the Kafka consumer
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='investment-score-processor',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Setting up the Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

print("Processing data and publishing scores for all investment types...")

# Main loop to process messages from the input topic and send results to the output topic
for message in consumer:
    pool = message.value
    project = pool.get('project')
    symbol = pool.get('symbol')

    # Check if the combination of project and symbol is allowed
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
                'tvlUsd': pool['tvlUsd']  # Ensures the original tvlUsd is sent
            }
            producer.send(OUTPUT_TOPIC, result)
            print(f"Sent to Kafka: {result}")
    except Exception as e:
        print(f"Skipping invalid entry: {e}")
