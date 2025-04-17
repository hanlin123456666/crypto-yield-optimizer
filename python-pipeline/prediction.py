from kafka import KafkaConsumer, KafkaProducer
import json
import time
import numpy as np

# Kafka configuration
KAFKA_BROKER = 'kafka:9092'
INPUT_TOPIC = 'defillama_apy'
OUTPUT_TOPIC = 'investment_scores'

# Log scale helper
def log_scale(value):
    return np.log1p(max(0, value))

# Allowed (project, token) combinations
combinations = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]

# Weight profiles for each investor type
investment_profiles = {
    'Yield maximize': {
        'mu': 0.4,
        'apy_mean_30d': 0.3,
        'tvl_log': 0.1,
        'sigma': -0.1
    },
    'Balanced investor': {
        'mu': 0.3,
        'apy_mean_30d': 0.2,
        'tvl_log': 0.3,
        'sigma': -0.1
    },
    'Conservative investor': {
        'mu': 0.2,
        'apy_mean_30d': 0.1,
        'tvl_log': 0.5,
        'sigma': -0.2
    }
}

# Kafka setup
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='investment-score-processor'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

print("✅ Scoring DeFi pools based on investor profiles...")

for message in consumer:
    pool = message.value
    project = pool.get('project')
    symbol = pool.get('symbol')

    if (project, symbol) not in combinations:
        continue

    try:
        # Extract features with safe defaults
        mu = float(pool.get('mu', 0))
        apy_mean = float(pool.get('apy_mean_30d', 0))
        sigma = float(pool.get('sigma', 0.0001))  # prevent division instability
        tvl_log = log_scale(pool.get('tvlUsd', 0))
        confidence = float(pool.get('predictedProbability', 50))  # default to neutral if missing

        for profile, weights in investment_profiles.items():
            score = (
                weights['mu'] * mu +
                weights['apy_mean_30d'] * apy_mean +
                weights['tvl_log'] * tvl_log +
                weights['sigma'] * sigma
            )

            confidence_boost = (1 + (confidence - 50) / 500)
            score *= confidence_boost

            result = {
                'project': project,
                'symbol': symbol,
                'type': profile,
                'score': round(score, 4),
                'timestamp': int(time.time()),
                'chain': pool.get('chain'),
                'mu': mu,
                'apy_mean_30d': apy_mean,
                'sigma': sigma,
                'tvlUsd': pool.get('tvlUsd'),
                'predictedProbability': confidence
            }

            # Send result to Kafka
            producer.send(OUTPUT_TOPIC, result)

            # Log result and formula
            print(
                f"✅ [{profile}] {symbol} - {project} | "
                f"Score = {round(score, 4)} | "
                f"Components: {weights['mu']}*{mu:.2f} + {weights['apy_mean_30d']}*{apy_mean:.2f} + "
                f"{weights['tvl_log']}*{tvl_log:.2f} + {weights['sigma']}*{sigma:.4f} | "
                f"Boost: {confidence_boost:.3f}"
            )

    except Exception as e:
        print(f"❌ Error processing {symbol} - {project}: {e}")
