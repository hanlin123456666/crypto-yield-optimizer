import os
from dotenv import load_dotenv
import logging
import json
from pathlib import Path
from web3 import Web3

load_dotenv()

logger = logging.getLogger(__name__)

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

RPC_URLS = {
    'Ethereum': os.getenv("ETHEREUM_RPC_URL"),
    # 'Polygon': os.getenv('POLYGON_RPC_URL'),
    # 'Mantle': os.getenv('MANTLE_RPC_URL'),
    # 'Arbitrum': os.getenv("ARBITRUM_RPC_URL"),
    # 'Optimism': os.getenv("OPTIMISM_RPC_URL"),
    # 'Base': os.getenv("BASE_RPC_URL"),
    # 'Avalanche': os.getenv("AVALANCHE_RPC_URL"),
    # 'Scroll': os.getenv("SCROLL_RPC_URL"),
}

BLOCK_EXPLORERS = {
    'Ethereum': 'https://sepolia.etherscan.io',
    # 'Arbitrum': 'https://arbiscan.io',
    # 'Polygon': 'https://polygonscan.com', 
    # 'Optimism': 'https://optimistic.etherscan.io',
    # 'Mantle': 'https://explorer.mantle.xyz',
    # 'Base': 'https://basescan.org',
    # 'Avalanche': 'https://snowtrace.io',
    # 'Scroll': 'https://scrollscan.com',
}

def load_abi(contract_name: str) -> dict:
    """Load ABI from file"""
    abi_path = Path('/app/abi') / f'{contract_name}.json'
    try:
        with open(abi_path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"ABI file not found: {contract_name}.json")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in ABI file: {contract_name}.json")
        raise

def get_web3(chain: str) -> Web3:
    """Get Web3 instance for specified chain"""
    if chain not in RPC_URLS:
        raise ValueError(f"Unsupported chain: {chain}")
    
    url = RPC_URLS[chain]
    if not url:
        raise ValueError(f"Missing RPC URL for chain: {chain}")
    
    return Web3(Web3.HTTPProvider(url))

def validate_base_env_vars(require_web3: bool = False) -> bool:
    if require_web3:
        missing_rpcs = [chain for chain, url in RPC_URLS.items() if not url]
        if missing_rpcs:
            logger.error(f"Missing RPC URLs for chains: {', '.join(missing_rpcs)}")
            return False
    return True 


def validate_rpc_connection():
    """Validate RPC connections"""
    for chain, url in RPC_URLS.items():
        try:
            w3 = Web3(Web3.HTTPProvider(url))
            if not w3.is_connected():
                logger.error(f"Failed to connect to {chain} RPC")
            else:
                logger.info(f"Successfully connected to {chain}")
        except Exception as e:
            logger.error(f"Error connecting to {chain} RPC: {str(e)}")

# Validate required environment variables
def validate_env_vars(service_type="collector"):
    """Validate required environment variables"""
    required_vars = {
        'RPC_URLs': {
            'Ethereum': os.getenv('ETHEREUM_RPC_URL'),
            # 'Polygon': os.getenv('POLYGON_RPC_URL'),
            # 'Mantle': os.getenv('MANTLE_RPC_URL'),
            # 'Arbitrum': os.getenv('ARBITRUM_RPC_URL'),
            # 'Optimism': os.getenv('OPTIMISM_RPC_URL'),
            # 'Base': os.getenv('BASE_RPC_URL'),
            # 'Avalanche': os.getenv('AVALANCHE_RPC_URL'),
        }
    }
    
    missing_vars = []
    for var, value in required_vars.items():
        if isinstance(value, dict):
            for sub_var, sub_value in value.items():
                if not sub_value:
                    missing_vars.append(f"{var}[{sub_var}]")
        elif not value:
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

# Load and validate configuration
if not validate_env_vars():
    logger.warning("Required environment variables not properly configured!")
else:
    validate_rpc_connection()


WETH_ADDRESS = {
    'Ethereum': '0xfff9976782d46cc05630d1f6ebab18b2324d6b14'
}

# Configuration of addresses for all supported stablecoins
STABLECOINS = {
    'USDT': {
        'Ethereum': '0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0', # sepolia
        # 'Polygon': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        # 'Arbitrum': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        # 'Optimism': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
        # 'Base': None,  # USDC on Base, USDT not available yet
        # 'Avalanche': '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7',
        # 'Mantle': '0x201EBa5CC46D216Ce6DC03F6a759e8E766e956aE',
    },
    'USDC': {
        'Ethereum': '0x1c7d4b196cb0c7b01d743fbc6116a902379c7238', # Circle sepolia
        # 'Ethereum': '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8', # sepolia
        # 'Polygon': '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359',
        # 'Arbitrum': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        # 'Optimism': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',
        # 'Base': '0x833589fCD6eDb6E08B4DF7441424273dE8F059F7',
        # 'Avalanche': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
        # 'Ethereum': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        # 'Mantle': '0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9',
        # 'Scroll': '0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4',
    },
    'DAI': {
        'Ethereum': '0xff34b3d4aee8ddcd6f9afffb6fe49bd371b8a357', # sepolia
        # 'Polygon': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
        # 'Arbitrum': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
        # 'Optimism': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
        # 'Base': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',
        # 'Avalanche': '0xd586E7F844cEa2F87f50152665BCbc2C279D8d70',
    },
    'WETH': {
        'Ethereum': '0xfff9976782d46cc05630d1f6ebab18b2324d6b14', # sepolia
    }
}

# AAVE V3 pool addresses for different networks
AAVE_V3_ADDRESSES = {
    'Ethereum': '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951', # sepolia
    # 'Polygon': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
    # 'Arbitrum': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
    # 'Optimism': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
    # 'Base': '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
    # 'Avalanche': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
}

# LENDLE_POOL_ADDRESS = {'Mantle': '0xCFa5aE7c2CE8Fadc6426C1ff872cA45378Fb7cF3'}

UNISWAP_V3_ROUTER = {
    'Ethereum': '0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E', # sepolia
    # 'Polygon': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    # 'Arbitrum': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    # 'Optimism': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    # 'Base': '0x2626664c2603336E57B271c5C9b86f4DfA5ecA44',
}

UNISWAP_CONTRACTS = {
    'Ethereum': {
        'router': '0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E',
        'quoter': '0xEd1f6473345F45b75F8179591dd5bA1888cf2FB3'
    }
}

COMPOUND_ADDRESSES = {
    'Ethereum': '0xAec1F48e02Cfb822Be958B68C7957156EB3F0b6e', # cUSDCv3 on sepolia
}

# RHO_ADDRESSES = {
#     'Scroll': {
#         'usdc': '0xAE1846110F72f2DaaBC75B7cEEe96558289EDfc5',
#         'usdt': '0x855CEA8626Fa7b42c13e7A688b179bf61e6c1e81'
#     }
# }

SUPPORTED_PROTOCOLS = {
    'aave-v3': AAVE_V3_ADDRESSES,
    # 'lendle': LENDLE_POOL_ADDRESS,
    'uniswap-v3': UNISWAP_V3_ROUTER,
    'compound-v3': COMPOUND_ADDRESSES,
    'weth': WETH_ADDRESS,
    # 'rho': RHO_ADDRESSES,
}