import json
import logging
import os
import joblib
from kafka import KafkaConsumer
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('MLKafkaTrain')

# Kafka configurations
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'defillama_apy')
MODEL_PATH = "/mnt/data/model.pkl"

# Initialize Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Prepare data storage
data = []

# Train model once and save
def train_and_save_model(data):
    df = pd.DataFrame(data)
    if len(df) < 50:
        logger.info("Insufficient data to train model.")
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

    # Save the trained model
    joblib.dump((model, scaler), MODEL_PATH)
    logger.info(f"Model trained and saved at {MODEL_PATH}")

# Consume messages and store data
for message in consumer:
    try:
        pool = message.value
        logger.info(f"Received data: {pool}")
        data.append(pool)

        # Train and save the model after collecting enough data
        if len(data) >= 50:
            train_and_save_model(data)
            break
    except Exception as e:
        logger.error(f"Error processing message: {e}")
