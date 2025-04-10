from web3 import Web3
from config import STABLECOINS

def get_token_address(token: str, chain: str) -> str:
    """Safe retrieval of token address"""
    address = STABLECOINS.get(token.upper(), {}).get(chain)
    if not address:
        raise ValueError(f"Token {token} not supported on {chain}")
    
    # Check address format
    try:
        return Web3.to_checksum_address(address)
    except ValueError as e:
        raise ValueError(f"Invalid address for {token} on {chain}: {address}") 