from time import sleep
from protocol_operator import get_protocol_operator  # your existing operator loader
from utils import get_token_address
import requests
from requests.auth import HTTPBasicAuth
from web3 import Web3

from config import (COUCHDB_URL, DATABASE_NAME, USERNAME, PASSWORD)

POOL_PAIRS = {
    "aave-v3": ["USDC", "USDT", "DAI"],
    "compound-v3": ["USDC"],
}

AMOUNT = 0.1

# Fetch CouchDB's latest record
# change to listening for new entries
def fetch_latest_strategy():
    url = f"{COUCHDB_URL}/{DATABASE_NAME}/_all_docs?include_docs=true&descending=true&limit=1"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        rows = response.json().get("rows", [])
        if rows:
            return rows[0]["doc"]
    return None

# Check if wallet has funds in the specified protocol
def check_if_wallet_has_balance(protocol_operator, token_symbol):
    try:
        return protocol_operator.get_protocol_balance(token_symbol) > 0
    except AttributeError:
        # For protocols without implemented balance methods
        return False

# Check across all pool pairs for any balance
def find_existing_deposit(network):
    for proto, tokens in POOL_PAIRS.items():
        for token in tokens:
            operator = get_protocol_operator(network, proto)
            if check_if_wallet_has_balance(operator, token):
                print(f"Found balance in {proto} for {token}")
                return proto, token
    return None, None

# Main backend execution
if __name__ == "__main__":
    doc = fetch_latest_strategy()
    if not doc:
        print("No strategy found.")
        exit()

    protocol = doc["project"]         # e.g., aave-v3
    symbol = doc["symbol"]           # e.g., DAI
    chain = doc["chain"]             # e.g., Ethereum

    print(f"Strategy: {protocol} | {symbol} | {chain}")

    # Step 1: Detect existing positions
    existing_protocol, existing_token = find_existing_deposit(chain)

    weth_operator = get_protocol_operator(chain, 'weth')
    uniswap_operator = get_protocol_operator(chain, 'uniswap-v3')
    target_operator = get_protocol_operator(chain, protocol)

    if existing_protocol is None:
        print("No existing position. Supplying new funds.")
        if weth_operator.get_weth_balance() < 0.1:
            weth_operator.wrap_eth(AMOUNT)
        sleep(10)
        uniswap_operator.swap('WETH', symbol, 150)
        sleep(10)
        target_operator.supply(symbol, 150)
        sleep(10)
    else:
        print(f"Rebalancing: Moving from {existing_protocol}:{existing_token} to {protocol}:{symbol}")
        existing_operator = get_protocol_operator(chain, existing_protocol)
        existing_operator.withdraw(existing_token, 150)
        uniswap_operator.swap(existing_token, 'WETH', 150)
        uniswap_operator.swap('WETH', symbol, 150)
        target_operator.supply(symbol, 150)


# response:
# {
# '_id': 'e1cddad9e63ab72c7a288d907ffff290', 
# '_rev': '1-25dce42876f33ced358abeeb84b21d9a', 
# 'project': 'aave-v3', 
# 'symbol': 'DAI', 
# 'score': 5695911.4472, 
# 'type': 'Yield maximize', 
# 'timestamp': 1744618985, 
# 'chain': 'Ethereum', 
# 'apy_mean_30d': 2.69399, 
# 'apy_change_1d': 0.0117, 
# 'apy_change_30d': -1.69291, 
# 'tvlUsd': 56959099
#  }