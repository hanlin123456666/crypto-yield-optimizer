import json
import logging
import os
from kafka import KafkaConsumer
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('MLKafkaConsumer')

# Kafka configurations
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'defillama_apy')

# Initialize Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Prepare data storage
data = []
model = None

# Function to calculate earnings for all combinations
def calculate_all_combinations(data):
    df = pd.DataFrame(data)
    if len(df) < 50:
        logger.info("Insufficient data to calculate combinations.")
        return None

    # Features and target
    X = df[['apy_mean_30d', 'apy_change_1d', 'apy_change_30d', 'tvlUsd']]
    y = df['apy_mean_30d']

    # Data preprocessing
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Model training
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)

    # Predict earnings for all combinations
    df['predicted_earning'] = model.predict(X_scaled)

    # Sort combinations by predicted earning
    ranked_combinations = df[['symbol', 'project', 'predicted_earning']].sort_values(by='predicted_earning', ascending=False)
    logger.info("All possible combinations ranked by estimated earning:")
    logger.info(ranked_combinations.head(10))

    # Recommendation
    best_row = ranked_combinations.iloc[0]
    recommendation = {
        'protocol': best_row['project'],
        'token': best_row['symbol'],
        'estimated_earning': best_row['predicted_earning']
    }
    logger.info(f"Best recommendation: {recommendation['protocol']} with {recommendation['token']} - Estimated earning: {recommendation['estimated_earning']}")
    return ranked_combinations

# Consume messages and store data
for message in consumer:
    try:
        pool = message.value
        logger.info(f"Received data: {pool}")
        data.append(pool)

        # Calculate combinations after collecting enough data
        if len(data) % 50 == 0:
            ranked_combinations = calculate_all_combinations(data)
            if ranked_combinations is not None:
                logger.info("Top 5 combinations:")
                logger.info(ranked_combinations.head(5).to_string(index=False))
    except Exception as e:
        logger.error(f"Error processing message: {e}")
