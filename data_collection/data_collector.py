import logging
import time
from typing import Dict, List
import os
from datetime import datetime
import sys
import json
from pathlib import Path

import requests
# from supabase import create_client

# Update imports to new structure
# CHANGE THESE TO OUR DB CONFIG
# from common.config import SUPABASE_KEY, SUPABASE_URL
# from data_collector.config import validate_env_vars

# Configure logging
LOG_DIR = "/app/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Form log filename with current date
log_filename = os.path.join(LOG_DIR, f"collector_{datetime.now().strftime('%Y%m%d')}.log")

# Configure log formatting
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Clear existing handlers
logger.handlers = []

# Handler for file only
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Disable log propagation
logger.propagate = False

# Add configuration cache
CONFIG_CACHE = {}
LAST_CONFIG_UPDATE = 0
CONFIG_UPDATE_INTERVAL = 600  # 10 minutes

CONFIG_PATH = Path('/app/config/config.json')

# Get interval from environment variable
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 300))

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'protocols': os.getenv('WHITE_LIST_PROTOCOLS', 'aave-v3,aave-v2').split(','),
            'tokens': os.getenv('WHITE_LIST_TOKENS', 'USDT,USDC').split(',')
        }

def save_config(config):
    CONFIG_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)

def get_white_lists():
    return load_config()


def fetch_pools() -> List[Dict]:
    """Fetch pools data from DeFiLlama API"""
    try:
        logger.info("Starting to fetch pools from DeFiLlama API...")
        response = requests.get("https://yields.llama.fi/pools")
        response.raise_for_status()
        data = response.json()['data']
        logger.info(f"Successfully fetched {len(data)} pools from DeFiLlama")

        white_lists = get_white_lists()
        filtered_pools = [
            pool for pool in data
            if pool['symbol'] in white_lists['tokens']
        ]
        
        # Add detailed logging for found pools
        logger.info(f"Filtered to {len(filtered_pools)} relevant pools")
        for pool in filtered_pools:
            logger.info(f"Found pool: {pool['symbol']} on {pool['chain']} in {pool['project']} "
                       f"(APY: {pool['apy']:.2f}%, TVL: ${pool['tvlUsd']:,.2f})")

        return filtered_pools
    except requests.RequestException as e:
        logger.error(f"Network error while fetching pools: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while fetching pools: {e}", exc_info=True)
        return []

def save_apy_data(pools: List[Dict]):
    """Save APY data to Supabase database"""
    try:
        logger.info("Connecting to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        records = {}
        current_time = int(time.time())
        
        for pool in pools:
            base_id = f"{pool['symbol']}_{pool['chain']}_{pool['project']}"
            pool_id = f"{base_id}_{pool['poolMeta']}" if pool.get('poolMeta') else base_id
            
            record = {
                "pool_id": pool_id,
                "asset": pool['symbol'],
                "chain": pool['chain'],
                "apy": pool.get('apy', 0),
                "tvl": pool.get('tvlUsd', 0),
                "timestamp": current_time,
                "apy_base": pool.get('apyBase', 0),
                "apy_reward": pool.get('apyReward', 0),
                "apy_mean_30d": pool.get('apyMean30d', 0),
                "apy_change_1d": pool.get('apyPct1D', 0),
                "apy_change_7d": pool.get('apyPct7D', 0),
                "apy_change_30d": pool.get('apyPct30D', 0),
                "data_source": "Defillama"
            }
            
            records[pool_id] = record
            logger.debug(f"Prepared record for {pool_id}")
        
        logger.info(f"Attempting to save {len(records)} records to database...")
        supabase.table('apy_history').upsert(
            list(records.values()),
            on_conflict='pool_id,timestamp'
        ).execute()
        logger.info(f"Successfully saved {len(records)} APY records to database")
        
    except Exception as e:
        logger.error(f"Failed to save data to Supabase: {e}", exc_info=True)
        raise

def run_data_collection():
    """Main data collection workflow"""
    try:
        if not validate_env_vars():
            logger.error("Cannot start data collection: missing required configuration")
            return None
        white_lists = get_white_lists()
        logger.info(f"Starting data collector with protocols: {white_lists['protocols']}")
        logger.info(f"Monitoring tokens: {white_lists['tokens']}")
        
        pools = fetch_pools()
        if pools:
            save_apy_data(pools)
            logger.info("Data collection cycle completed successfully")
        else:
            logger.warning("No pools were fetched, skipping database update")
        return pools
    except Exception as e:
        logger.critical(f"Data collection failed: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting data collection cycle...")
    run_data_collection()