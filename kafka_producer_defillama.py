import json
import logging
import os
import time
from kafka import KafkaProducer
import requests
from typing import Dict, List, Tuple

# Configure logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('DefiLlamaKafkaProducer')

# Kafka configurations
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'defillama_apy')

# DeFiLlama API endpoint
DEFILLAMA_API = "https://yields.llama.fi/pools"

# Explicit whitelist of (protocol, token) pairs
ALLOWED_PAIRS: List[Tuple[str, str]] = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_pools() -> List[Dict]:
    """Fetch pools data from DeFiLlama API"""
    try:
        logger.info("Starting to fetch pools from DeFiLlama API...")
        response = requests.get(DEFILLAMA_API)
        response.raise_for_status()
        data = response.json().get('data', [])
        logger.info(f"Successfully fetched {len(data)} pools from DeFiLlama")

        filtered_pools = [
            {
                "symbol": pool['symbol'],
                "project": pool['project'],
                "chain": pool['chain'],
                "apy_mean_30d": pool.get('apyMean30d', 0),
                "apy_change_1d": pool.get('apyPct1D', 0),
                "apy_change_30d": pool.get('apyPct30D', 0),
                "tvlUsd": pool.get('tvlUsd', 0)
            }
            for pool in data
            if (pool['project'], pool['symbol']) in ALLOWED_PAIRS
        ]

        logger.info(f"Filtered to {len(filtered_pools)} specific pools")
        for pool in filtered_pools:
            logger.info(f"Pool: {pool['symbol']} on {pool['chain']} in {pool['project']} "
                        f"(Mean APY: {pool['apy_mean_30d']}%, 1-Day Change: {pool['apy_change_1d']}%, "
                        f"30-Day Change: {pool['apy_change_30d']}%, TVL: ${pool['tvlUsd']:,.2f})")

        return filtered_pools
    except requests.RequestException as e:
        logger.error(f"Network error while fetching pools: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while fetching pools: {e}", exc_info=True)
        return []

def produce_pools(pools: List[Dict]):
    """Send filtered pool data to Kafka topic"""
    for pool in pools:
        try:
            producer.send(KAFKA_TOPIC, value=pool)
            logger.info(f"Sent pool data to Kafka topic {KAFKA_TOPIC}: {pool['symbol']} - {pool['project']}")
        except Exception as e:
            logger.error(f"Failed to send data to Kafka: {e}")

if __name__ == '__main__':
    while True:
        pools = fetch_pools()
        if pools:
            produce_pools(pools)
        time.sleep(3600)  # Fetch every 1 hour
