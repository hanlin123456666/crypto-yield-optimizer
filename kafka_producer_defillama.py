import json
import logging
import os
import time
from kafka import KafkaProducer
import requests
from typing import Dict, List, Tuple

# ---------------------- CONFIG ---------------------- #
# Logging configuration
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

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ---------------------- FUNCTIONS ---------------------- #
def fetch_pools() -> List[Dict]:
    """Fetch and filter pool data from DeFiLlama"""
    try:
        logger.info("Starting to fetch pools from DeFiLlama API...")
        response = requests.get(DEFILLAMA_API)
        response.raise_for_status()
        data = response.json().get('data', [])
        logger.info(f"✅ Fetched {len(data)} total pools from DeFiLlama")

        # Filter to pools of interest on Ethereum
        filtered_pools = []
        for pool in data:
            project = pool.get("project")
            symbol = pool.get("symbol")
            chain = pool.get("chain")

            if (project, symbol) in ALLOWED_PAIRS and chain == "Ethereum":
                filtered_pools.append({
                    "symbol": symbol,
                    "project": project,
                    "chain": chain,
                    "apy": pool.get("apy", 0),
                    "apy_mean_30d": pool.get("apyMean30d", 0),
                    "apy_change_1d": pool.get("apyPct1D", 0),
                    "apy_change_30d": pool.get("apyPct30D", 0),
                    "mu": pool.get("mu", 0),
                    "sigma": pool.get("sigma", 0),
                    "predictedProbability": pool.get("predictions", {}).get("predictedProbability", 50),
                    "tvlUsd": pool.get("tvlUsd", 0),
                    "timestamp": int(time.time())
                })

        logger.info(f"✅ Filtered down to {len(filtered_pools)} Ethereum pools from allowed pairs")
        for pool in filtered_pools:
            logger.info(
                f"📊 Pool: {pool['symbol']} | Project: {pool['project']} | "
                f"APY: {pool['apy']} | Mean30d: {pool['apy_mean_30d']} | "
                f"mu: {pool['mu']}, σ: {pool['sigma']} | TVL: ${pool['tvlUsd']:,.2f}"
            )

        return filtered_pools

    except requests.RequestException as e:
        logger.error(f"❌ Network error while fetching pools: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error while fetching pools: {e}", exc_info=True)
        return []

def produce_pools(pools: List[Dict]):
    """Send filtered/enriched pool data to Kafka topic"""
    for pool in pools:
        try:
            producer.send(KAFKA_TOPIC, value=pool)
            logger.info(f"✅ Sent to Kafka: {pool['symbol']} - {pool['project']}")
        except Exception as e:
            logger.error(f"❌ Failed to send data to Kafka: {e}")

# ---------------------- MAIN LOOP ---------------------- #
if __name__ == '__main__':
    while True:
        pools = fetch_pools()
        if pools:
            produce_pools(pools)
        time.sleep(600)  # Repeat every 10 minutes
