import json
import logging
import os
import joblib
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('MLKafkaInferenceRanked')

# Kafka configurations
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC_UI = os.getenv('KAFKA_TOPIC_UI', 'defillama_apy_ui')
KAFKA_TOPIC_RESPONSE = os.getenv('KAFKA_TOPIC_RESPONSE', 'defillama_apy_response')
MODEL_PATH = "/mnt/data/model.pkl"
COMBINATIONS_PATH = "/mnt/data/combinations.csv"

# Load the trained model and scaler
def load_model():
    try:
        model, scaler = joblib.load(MODEL_PATH)
        logger.info(f"Model loaded from {MODEL_PATH}")
        return model, scaler
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None, None

# Initialize Kafka consumer for UI requests
consumer = KafkaConsumer(
    KAFKA_TOPIC_UI,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Initialize Kafka producer for sending recommendations
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Load model
model, scaler = load_model()

# Listen to UI requests and send ranked recommendations
for message in consumer:
    try:
        request = message.value
        logger.info(f"Received UI request: {request}")

        # Load the data for all combinations
        df = pd.read_csv(COMBINATIONS_PATH)
        features = df[['apy_mean_30d', 'apy_change_1d', 'apy_change_30d', 'tvlUsd']]
        scaled_features = scaler.transform(features)

        # Predict earnings for all combinations
        df['predicted_earning'] = model.predict(scaled_features)

        # Rank the combinations by predicted earning
        ranked_combinations = df[['symbol', 'project', 'predicted_earning']].sort_values(by='predicted_earning', ascending=False)
        response = ranked_combinations.head(10).to_dict(orient='records')
        logger.info(f"Top 10 recommendations: {response}")

        # Send the ranked list as the response
        producer.send(KAFKA_TOPIC_RESPONSE, value={'recommendations': response})
        logger.info(f"Ranked recommendation sent to topic {KAFKA_TOPIC_RESPONSE}")
    except Exception as e:
        logger.error(f"Error processing UI request: {e}")
