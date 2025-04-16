import json
from time import sleep
from protocol_operator import get_protocol_operator
import requests
from requests.auth import HTTPBasicAuth

from config import (COUCHDB_URL, DATABASE_NAME, USERNAME, PASSWORD)

POOL_PAIRS = {
    "aave-v3": ["USDC", "USDT", "DAI"],
    "compound-v3": ["USDC"],
}

AMOUNT = 0.1

last_strategy = None 

def listen_to_couchdb_changes():
    url = f"{COUCHDB_URL}/{DATABASE_NAME}/_changes?feed=continuous&include_docs=true"
    with requests.get(url, stream=True, auth=HTTPBasicAuth(USERNAME, PASSWORD)) as r:
        for line in r.iter_lines():
            if line:
                try:
                    change = json.loads(line.decode('utf-8'))
                    doc = change.get("doc")
                    if doc:
                        process_strategy(doc)
                except Exception as e:
                    print(f"Failed to process line: {e}")

def process_strategy(doc):
    global last_strategy

    protocol = doc["project"]
    symbol = doc["symbol"]
    chain = doc["chain"]

    current = (protocol, symbol)

    if last_strategy == current:
        print(f"Strategy {current} already processed. Skipping.")
        return
    
    print(f"New strategy: {protocol} | {symbol} | {chain}")
    last_strategy = current  # update last seen strategy

    global uniswap_operator
    weth_operator = get_protocol_operator(chain, 'weth')
    uniswap_operator = get_protocol_operator(chain, 'uniswap-v3')
    target_operator = get_protocol_operator(chain, protocol)

    existing_protocol, existing_token = find_existing_deposit(chain)

    if existing_protocol is None:
        print("No existing position. Supplying new funds.")
        if weth_operator.get_weth_balance() < 0.1:
            weth_operator.wrap_eth(AMOUNT)
        sleep(10)
        uniswap_operator.swap('WETH', symbol, 50)
        sleep(10)
        target_operator.supply(symbol, 50)
    else:
        print(f"Rebalancing: Moving from {existing_protocol}:{existing_token} to {protocol}:{symbol}")
        existing_operator = get_protocol_operator(chain, existing_protocol)
        withdraw_all(existing_operator, existing_token)
        sleep(10)
        uniswap_operator.swap('WETH', symbol, 50)
        sleep(10)
        target_operator.supply(symbol, 50)

def check_if_wallet_has_balance(protocol_operator, token_symbol, min_balance=0.1):
    try:
        balance = protocol_operator.get_protocol_balance(token_symbol)
        if balance >= min_balance:
            return True
        elif balance > 0:
            # Balance is too small, withdraw it
            print(f"Balance for {token_symbol} is {balance}, below threshold. Withdrawing all.")
            withdraw_all(protocol_operator, token_symbol)
        return False
    except AttributeError:
        return False

def find_existing_deposit(network):
    for proto, tokens in POOL_PAIRS.items():
        for token in tokens:
            operator = get_protocol_operator(network, proto)
            if check_if_wallet_has_balance(operator, token):
                print(f"Found sufficient balance in {proto} for {token}")
                return proto, token
    return None, None

def withdraw_all(protocol_operator, token_symbol):
    """
    Withdraws all available balance of a token from a protocol.

    Args:
        protocol_operator: Instance of the protocol operator (e.g., AaveOperator, CompoundOperator)
        token_symbol: Token symbol string (e.g., "USDT")
    """
    try:
        balance = protocol_operator.get_protocol_balance(token_symbol)
        if balance > 0:
            print(f"Withdrawing all {balance} {token_symbol} from protocol")
            protocol_operator.withdraw(token_symbol, balance)
            sleep(10)
            uniswap_operator.swap(token_symbol, 'WETH', balance)
        else:
            print(f"No {token_symbol} balance to withdraw.")
    except Exception as e:
        print(f"Failed to withdraw all {token_symbol}: {e}")


# Main backend execution
if __name__ == "__main__":
    print("Listening to CouchDB changes...")
    listen_to_couchdb_changes()


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