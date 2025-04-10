import os
import json
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PROVIDER = os.getenv("PROVIDER")
WALLET_ADDRESS = os.getenv("ADDRESS")

# User parameters
OUT_AMOUNT_READABLE = 10
MAX_SLIPPAGE = 0.1

# Contract Addresses (Sepolia)
WETH_ADDRESS = Web3.to_checksum_address("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14")
USDC_ADDRESS = Web3.to_checksum_address("0x1c7d4b196cb0c7b01d743fbc6116a902379c7238")
USDT_ADDRESS = Web3.to_checksum_address("0xaa8e23fb1079ea71e0a56f48a2aa51851d8433d0")
DAI_ADDRESS = Web3.to_checksum_address("0xff34b3d4aee8ddcd6f9afffb6fe49bd371b8a357")

USDC_WETH_POOL_ADDRESS = Web3.to_checksum_address("0xcdf1597a0c2dda04e80e135351831b7a6af1f86d")  # USDC/WETH
USDT_WETH_POOL_ADDRESS = Web3.to_checksum_address("0x58d850667c47981a1b6e7ca0b8dc2eb937cd4119")  # USDT/WETH
DAI_WETH_POOL_ADDRESS = Web3.to_checksum_address("0x60439363146fc0f633388b4402082cd673906d2c")  # DAI/WETH

QUOTER_ADDRESS = Web3.to_checksum_address("0xEd1f6473345F45b75F8179591dd5bA1888cf2FB3")
ROUTER_ADDRESS = Web3.to_checksum_address("0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E")

# ABI Paths
POOL_ABI_PATH = "UniswapV3PoolABI.json"
QUOTER_ABI_PATH = "UniswapV3QuoterV2ABI.json"
ROUTER_ABI_PATH = "UniswapV3SwapRouter02ABI.json"
ERC20_ABI_PATH = "ERC20ABI.json"
WETH_ABI_PATH = "BasicWETHABI.json"

# Load ABI from file
def load_abi(path):
    with open(path, "r") as file:
        return json.load(file)

# Check transaction status
def success_status(receipt):
    return "successful" if receipt.status == 1 else "failed"

# Wrap ETH into WETH
def wrap_eth(w3, amount):
    weth = w3.eth.contract(address=WETH_ADDRESS, abi=load_abi(WETH_ABI_PATH))
    eth_amount = w3.to_wei(amount, "ether")

    tx = weth.functions.deposit().build_transaction({
        "from": WALLET_ADDRESS,
        "value": eth_amount,
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(WALLET_ADDRESS),
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"WETH wrap tx: {receipt.transactionHash.hex()} ({success_status(receipt)})")

def unwrap_eth(w3, amount):
    # Load the WETH contract using its address and ABI.
    weth = w3.eth.contract(address=WETH_ADDRESS, abi=load_abi(WETH_ABI_PATH))
    # Convert the amount from ETH to Wei.
    weth_amount = w3.to_wei(amount, "ether")
    # Build the transaction for the withdraw (unwrap) function.
    tx = weth.functions.withdraw(weth_amount).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(WALLET_ADDRESS),
    })
    # Sign the transaction with your private key.
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    # Send the signed transaction and wait for its receipt.
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"WETH unwrap tx: {receipt.transactionHash.hex()} ({success_status(receipt)})")


# Get quote from Quoter
def get_quote(w3, pool_address):
    pool = w3.eth.contract(address=pool_address, abi=load_abi(POOL_ABI_PATH))
    fee = pool.functions.fee().call()
    sqrtPriceX96 = pool.functions.slot0().call()[0]

    out_token = pool.functions.token0().call()
    in_token = pool.functions.token1().call()

    out_contract = w3.eth.contract(address=out_token, abi=load_abi(ERC20_ABI_PATH))
    in_contract = w3.eth.contract(address=in_token, abi=load_abi(ERC20_ABI_PATH))

    out_symbol = out_contract.functions.symbol().call()
    out_decimals = out_contract.functions.decimals().call()
    in_symbol = in_contract.functions.symbol().call()
    in_decimals = in_contract.functions.decimals().call()

    out_amount = int(OUT_AMOUNT_READABLE * 10**out_decimals)
    out_price = (sqrtPriceX96 / (2**96)) ** 2
    in_amount_est = int(out_amount * out_price)

    print(f"Swapping {OUT_AMOUNT_READABLE} {out_symbol} ≈ {in_amount_est / 10**in_decimals:.6f} {in_symbol}")

    quoter = w3.eth.contract(address=QUOTER_ADDRESS, abi=load_abi(QUOTER_ABI_PATH))
    quote = quoter.functions.quoteExactOutputSingle(
        [in_token, out_token, out_amount, fee, 0]
    ).call()

    in_amount_expected = quote[0]
    price_impact = (in_amount_expected - in_amount_est) / in_amount_est
    max_slippage_amount = int(in_amount_est * (1 + MAX_SLIPPAGE))

    print(f"Expected cost: {in_amount_expected / 10**in_decimals:.6f} {in_symbol} (impact: {price_impact:.2%})")
    print(f"Max allowed:  {max_slippage_amount / 10**in_decimals:.6f} {in_symbol} (+{MAX_SLIPPAGE:.2%} slippage)")

    return in_token, out_token, out_amount, max_slippage_amount, in_symbol, fee

# Approve spending of token
def approve_token(w3, token_address, spender, amount):
    token = w3.eth.contract(address=token_address, abi=load_abi(ERC20_ABI_PATH))

    tx = token.functions.approve(spender, amount).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(WALLET_ADDRESS),
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Approve tx: {receipt.transactionHash.hex()} ({success_status(receipt)})")

# Perform swap
def swap_tokens(w3, in_token, out_token, out_amount, max_in_amount, fee):
    router = w3.eth.contract(address=ROUTER_ADDRESS, abi=load_abi(ROUTER_ABI_PATH))

    tx = router.functions.exactOutputSingle(
        [in_token, out_token, fee, WALLET_ADDRESS, out_amount, max_in_amount, 0]
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(WALLET_ADDRESS),
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Swap tx: {receipt.transactionHash.hex()} ({success_status(receipt)})")

# Main flow
def main():
    w3 = Web3(Web3.HTTPProvider(PROVIDER))
    if not w3.is_connected():
        raise Exception("Web3 provider not connected!")

    print("Web3 connected")

    # Step 1: Wrap ETH → WETH
    # wrap_eth(w3, 0.1)

    # Step 2: Get quote
    in_token, out_token, out_amount, max_in_amount, in_symbol, fee = get_quote(w3, USDT_WETH_POOL_ADDRESS)

    # Step 3: Approve token if needed
    approve_token(w3, in_token, ROUTER_ADDRESS, max_in_amount)

    # Step 4: Swap
    try:
        swap_tokens(w3, in_token, out_token, out_amount, max_in_amount, fee)
    except Exception as e:
        print(f"Swap failed: {e}")

if __name__ == "__main__":
    main()
