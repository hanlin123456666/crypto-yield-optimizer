import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from enum import Enum
from web3 import Web3
from web3.contract import Contract
import time

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from utils import get_token_address
from config import (PRIVATE_KEY, RPC_URLS, STABLECOINS, 
                     SUPPORTED_PROTOCOLS, BLOCK_EXPLORERS, WETH_ADDRESS)

# from src.analytics.analyzer import get_recommendations, format_recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ABI_DIR = Path(__file__).parent.parent / "abi"

no_reserve_data_protocols = ['uniswap-v3', 'rho-markets']

class BaseProtocolOperator:
    """Base class for interacting with DeFi protocols"""
    
    def __init__(self, network: str, protocol: str):
        self.network = network
        self.protocol = protocol
        self.w3 = Web3(Web3.HTTPProvider(RPC_URLS.get(network)))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {network} RPC")
            
        try:
            self.contract_address = SUPPORTED_PROTOCOLS[protocol][network]
        except KeyError:
            available_networks = list(SUPPORTED_PROTOCOLS[protocol].keys())
            raise ValueError(f"{protocol} contracts not found on {network}. Available on: {', '.join(available_networks)}")
        
        self.contract = self._load_contract()
        self.account = self.w3.eth.account.from_key(PRIVATE_KEY)
        self.explorer_url = BLOCK_EXPLORERS.get(self.network)
        
    def _load_contract(self) -> Contract:
        """Load ABI based on protocol"""
        try:
            abi_map = {
                'aave-v3': 'AaveV3Pool.json',
                'uniswap-v3': 'UniswapV3Router.json',
                'compound-v3': 'CompoundComet.json',
                'weth': 'BasicWETHABI.json',
            }
            
            
            if self.protocol not in abi_map:
                raise ValueError(f"Unsupported protocol: {self.protocol}")
            
            abi_path = ABI_DIR / abi_map[self.protocol]
            
            # Check possible alternative paths
            if not os.path.exists(abi_path):
                alt_path = os.path.join(os.path.dirname(__file__), f"../common/abi/{self.protocol}.json")
                if os.path.exists(alt_path):
                    abi_path = alt_path
                else:
                    raise FileNotFoundError(f"ABI file not found: {abi_path}")
            
            with open(abi_path) as f:
                abi = json.load(f)
                logger.info(f"ABI loaded: {abi_path}")
            
            # Check if contract address is valid
            if not Web3.is_checksum_address(self.contract_address):
                self.contract_address = Web3.to_checksum_address(self.contract_address)
            
            # Create contract
            contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=abi
            )
            
            # Check if contract is accessible
            try:
                # Try calling a view method, but only for protocols that support it
                if self.protocol not in no_reserve_data_protocols:
                    contract.functions.getReserveData(
                        self.w3.to_checksum_address(
                            STABLECOINS['USDT'][self.network]
                        )
                    ).call()
                    contract.functions.getApy("test").call()
                elif self.protocol == 'uniswap-v3':
                    if self.w3.eth.get_code(self.contract_address) == b'':
                        raise ValueError(f"No contract at address {self.contract_address}")
            except Exception as e:
                logger.warning(f"Contract verification warning: {str(e)}")
            
            return contract
            
        except Exception as e:
            logger.error(f"Error loading contract for {self.protocol} on {self.network}: {str(e)}")
            raise
        
    def _get_gas_params(self) -> Dict[str, Any]:
        """Get gas parameters optimized for L2 networks"""
        base_params = {
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id
        }

        # For EVM-networks use EIP-1559 with base parameters
        try:
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']
            priority_fee = self.w3.eth.max_priority_fee or self.w3.to_wei(1, 'gwei')
            
            base_params['maxFeePerGas'] = base_fee + priority_fee
            base_params['maxPriorityFeePerGas'] = priority_fee
        except:
            base_params['gasPrice'] = self.w3.eth.gas_price

        return base_params

    def _send_transaction(self, tx_function) -> str:
        """Universal method for sending transactions"""
        try:
            tx_params = self._get_gas_params()
            
            # Base gas estimation with fixed multiplier
            estimated_gas = tx_function.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * 1.3)  # 30% buffer
            
            # Try to send transaction, with up to 3 attempts with increased gas price
            max_attempts = 3
            attempt = 1
            
            while attempt <= max_attempts:
                try:
                    signed_tx = self.account.sign_transaction(
                        tx_function.build_transaction(tx_params)
                    )
                    
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    if receipt.status != 1:
                        raise Exception("Transaction reverted")
                        
                    tx_hash_hex = tx_hash.hex()
                    logger.info(f'Transaction successful: {self.explorer_url}/tx/0x{tx_hash_hex}')
                    
                    return f'{self.explorer_url}/tx/0x{tx_hash_hex}'
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if error is "transaction underpriced"
                    if "underpriced" in error_msg.lower() and attempt < max_attempts:
                        # Increase gas price by 30% for each retry
                        if 'gasPrice' in tx_params:
                            tx_params['gasPrice'] = int(tx_params['gasPrice'] * 1.3)
                            logger.warning(f"Transaction underpriced. Increasing gas price to {tx_params['gasPrice']} (attempt {attempt}/{max_attempts})")
                        else:
                            # If using EIP-1559, increase both maxFeePerGas and maxPriorityFeePerGas
                            if 'maxFeePerGas' in tx_params:
                                tx_params['maxFeePerGas'] = int(tx_params['maxFeePerGas'] * 1.3)
                                tx_params['maxPriorityFeePerGas'] = int(tx_params['maxPriorityFeePerGas'] * 1.3)
                                logger.warning(f"Transaction underpriced. Increasing maxFeePerGas to {tx_params['maxFeePerGas']} (attempt {attempt}/{max_attempts})")
                            else:
                                # Fallback to standard gasPrice if neither is set
                                tx_params['gasPrice'] = int(self.w3.eth.gas_price * (1.3 ** attempt))
                                logger.warning(f"Transaction underpriced. Setting gasPrice to {tx_params['gasPrice']} (attempt {attempt}/{max_attempts})")
                                
                        # Update nonce in case it's changed
                        tx_params['nonce'] = self.w3.eth.get_transaction_count(self.account.address)
                        attempt += 1
                        continue
                    else:
                        # For other errors or if max attempts reached, raise the exception
                        logger.error(f"Transaction error: {error_msg}")
                        raise
            
            # If we've reached here, all attempts failed
            raise Exception(f"Failed to send transaction after {max_attempts} attempts")
            
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            return None

    def _call_contract(self, function) -> Any:
        """Execute contract call with proper gas estimation"""
        try:
            params = {
                'from': self.account.address,
                'chainId': self.w3.eth.chain_id,
            }
            gas_estimate = function.estimate_gas(params)
            params['gas'] = int(gas_estimate * 1.5)
            
            return function.call(params)
            
        except Exception as e:
            logger.error(f"Contract call failed: {str(e)}")
            raise

    def _convert_to_wei(self, token_address: str, amount: float) -> int:
        """Convert amount to wei based on token decimals"""
        try:
            if not Web3.is_checksum_address(token_address):
                token_address = Web3.to_checksum_address(token_address)
            
            if not self.w3.is_connected():
                raise ConnectionError(f"Not connected to {self.network}")
                
            if self.w3.eth.get_code(token_address) == b'':
                raise ValueError(f"No contract at address {token_address}")
            
            with open(ABI_DIR / 'ERC20.json') as f:
                abi = json.load(f)
            
            erc20 = self.w3.eth.contract(address=token_address, abi=abi)
            
            try:
                # Use _call_contract for decimals
                decimals = erc20.functions.decimals().call()
                logger.info(f"Got decimals for {token_address}: {decimals}")
            except Exception as e:
                logger.warning(f"Failed to get decimals, using default (18): {str(e)}")
                decimals = 18
            
            return int(amount * 10 ** decimals)
            
        except Exception as e:
            logger.error(f"Error in _convert_to_wei: {str(e)}")
            raise

    def _check_token_support(self, token_address: str) -> bool:
        """Check if token is supported in the pool"""
        try:
            # Use _call_contract instead of direct call
            reserve_data = self._call_contract(
                self.contract.functions.getReserveData(token_address)
            )
            
            configuration = reserve_data[0]
            is_active = (configuration >> 56) & 1
            is_frozen = (configuration >> 57) & 1
            
            if not is_active:
                raise ValueError(f"Token {token_address} is not active in the pool")
            if is_frozen:
                raise ValueError(f"Token {token_address} is frozen in the pool")
                
            return True
            
        except Exception as e:
            logger.error(f"Token support check failed: {str(e)}")
            return False
        
        
class AaveOperator(BaseProtocolOperator):
    """Class for working with AAVE across networks"""
    
    def get_protocol_balance(self, token: str) -> float:
        """
        Get user aToken balance in Aave protocol
        
        Args:
            token: Token symbol (e.g., 'USDC')
            
        Returns:
            Balance as float
        """
        try:
            if token in STABLECOINS and self.network in STABLECOINS[token]:
                token_address = self.w3.to_checksum_address(STABLECOINS[token][self.network])
            else:
                token_address = get_token_address(token, self.network)

            logger.info(f"Checking Aave protocol balance for {token} ({token_address})")

            # Get aToken address from reserve data
            reserve_data = self.contract.functions.getReserveData(token_address).call()
            atoken_address = reserve_data[8]

            if not self.w3.is_address(atoken_address):
                raise ValueError(f"Invalid aToken address for {token}: {atoken_address}")
            
            if atoken_address == '0x0000000000000000000000000000000000000000':
                logger.info("No Aave balance yet.")

            # Load aToken contract
            with open(ABI_DIR / 'ERC20.json') as f:
                atoken_contract = self.w3.eth.contract(
                    address=self.w3.to_checksum_address(atoken_address),
                    abi=json.load(f)
                )

            balance = atoken_contract.functions.balanceOf(self.account.address).call()
            decimals = atoken_contract.functions.decimals().call()
            balance_human = balance / 10**decimals

            logger.info(f"Aave aToken balance for {token}: {balance_human}")
            return balance_human

        except Exception as e:
            logger.error(f"Error getting Aave protocol balance for {token}: {e}")
            return 0.0
        
    def supply(self, token: str, amount: float) -> str:
        """Deposit funds into protocol"""
        token_address = get_token_address(token, self.network)
        amount_wei = self._convert_to_wei(token_address, amount)
        
        # Create token contract
        with open(ABI_DIR / 'ERC20.json') as f:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=json.load(f)
            )
        
        # Get and log balance
        decimals = token_contract.functions.decimals().call()
        balance = token_contract.functions.balanceOf(self.account.address).call()
        balance_human = balance / 10**decimals
        
        logger.info(f"Current wallet balance: {balance_human} {token}")
        logger.info(f"Attempting to supply: {amount} {token}")
        
        if balance < amount_wei:
            raise ValueError(f"Insufficient balance: have {balance_human}, need {amount} {token}")
        
        # Rest of the supply logic...
        allowance = token_contract.functions.allowance(
            self.account.address,
            self.contract_address
        ).call()
        
        if allowance < amount_wei:
            approve_tx = token_contract.functions.approve(
                self.contract_address,
                amount_wei
            )
            logger.info(f"Approving {token} for Aave V3")
            self._send_transaction(approve_tx)
        
        if self.protocol == 'aave-v3':
            tx_func = self.contract.functions.supply(
                token_address,
                amount_wei,
                self.account.address,
                0
            )
            
        return self._send_transaction(tx_func)
        
    def withdraw(self, token: str, amount: float) -> str:
        """Withdraw funds from protocol"""
        try:
            token_address = get_token_address(token, self.network)
            
            # Check token support in pool
            logger.info(f"Checking if token {token} ({token_address}) is supported in {self.network} pool")
            reserve_data = self.contract.functions.getReserveData(token_address).call()
            
            # Check reserve configuration
            configuration = reserve_data[0]
            is_active = (configuration >> 56) & 1
            is_frozen = (configuration >> 57) & 1
            
            if not is_active:
                raise ValueError(f"Token {token} is not active in the pool")
            if is_frozen:
                raise ValueError(f"Token {token} is frozen in the pool")
                
            atoken_address = reserve_data[8]
            if not self.w3.is_address(atoken_address) or atoken_address == '0x0000000000000000000000000000000000000000':
                raise ValueError(f"Invalid aToken address for {token}: {atoken_address}")
                
            logger.info(f"Token is supported, aToken address: {atoken_address}")
            
                
            # Create aToken contract and get balance
            atoken_contract = self.w3.eth.contract(
                address=atoken_address,
                abi=json.load(open(ABI_DIR / 'ERC20.json'))
            )
            
            # Use direct call() as in get_balance
            decimals = atoken_contract.functions.decimals().call()
            balance = atoken_contract.functions.balanceOf(self.account.address).call()
            logger.info(f"Current wallet balance: {balance/10**decimals} {token}")

            amount_wei = self._convert_to_wei(token_address, amount)
            
            if balance < amount_wei:
                raise ValueError(f"Insufficient balance: have {balance / 10 ** decimals}, need {amount_wei / 10 ** decimals}")
            
            # Execute withdrawal
            tx_func = self.contract.functions.withdraw(
                token_address,
                amount_wei,
                self.account.address
            )
            
            return self._send_transaction(tx_func)
            
        except Exception as e:
            logger.error(f"Withdrawal failed for {token} on {self.network}: {str(e)}")
            raise
    
class UniswapV3Operator(BaseProtocolOperator):
    """Uniswap V3 operator that supports swaps with WETH as intermediate route."""

    def __init__(self, network: str, protocol: str = 'uniswap-v3'):
        super().__init__(network, protocol)
        self.router_address = self.contract_address  # from config
        self.router = self.contract  # already loaded

    def _get_token_contract(self, token_address: str) -> Contract:
        abi = json.load(open(ABI_DIR / 'ERC20.json'))
        return self.w3.eth.contract(address=token_address, abi=abi)

    def _get_token_decimals(self, token_address: str) -> int:
        token = self._get_token_contract(token_address)
        return token.functions.decimals().call()

    def _approve(self, token_address: str, amount: int):
        token = self._get_token_contract(token_address)
        allowance = token.functions.allowance(self.account.address, self.router_address).call()

        if allowance < amount:
            logger.info(f"Approving {amount} for router")
            tx_func = token.functions.approve(self.router_address, amount)
            self._send_transaction(tx_func)

    def swap(self, token_in: str, token_out: str, amount_out: float, slippage: float = 0.1):
        token_in_addr = get_token_address(token_in, self.network)
        token_out_addr = get_token_address(token_out, self.network)
        decimals_out = self._get_token_decimals(token_out_addr)
        amount_out_wei = int(amount_out * 10**decimals_out)

        fee = 500  # 0.05%
        price_buffer = 1 + slippage
        max_in_amount = int(amount_out_wei * price_buffer)

        self._approve(token_in_addr, max_in_amount)

        tx_func = self.router.functions.exactOutputSingle([
            token_in_addr,      # tokenIn
            token_out_addr,     # tokenOut
            fee,                # uint24
            self.account.address,  # recipient
            amount_out_wei,     # amountOut
            max_in_amount,      # amountInMaximum
            0                   # sqrtPriceLimitX96
        ])

        return self._send_transaction(tx_func)


class CompoundOperator(BaseProtocolOperator):
    """Class for working with Compound v3 protocol"""
    
    def get_protocol_balance(self, token: str) -> float:
        """
        Get user balance for a specific token in Compound V3 (Comet) protocol.

        Args:
            token: Token symbol (e.g., 'USDC')

        Returns:
            Balance as float
        """
        try:
            if token in STABLECOINS and self.network in STABLECOINS[token]:
                token_address = Web3.to_checksum_address(STABLECOINS[token][self.network])
            else:
                token_address = get_token_address(token, self.network)

            logger.info(f"Checking Compound V3 balance for {token} ({token_address})")

            # Get decimals
            with open(ABI_DIR / 'ERC20.json') as f:
                erc20_abi = json.load(f)
            token_contract = self.w3.eth.contract(address=token_address, abi=erc20_abi)
            decimals = token_contract.functions.decimals().call()

            # Get balance from Comet contract
            balance_wei = self.contract.functions.balanceOf(self.account.address).call()
            balance = balance_wei / (10 ** decimals)

            logger.info(f"User balance in Compound V3: {balance} {token}")
            return balance

        except Exception as e:
            logger.error(f"Error getting Compound V3 balance for {token}: {e}")
            return 0.0

    def supply(self, token: str, amount: float) -> str:
        """Supply tokens to Compound protocol"""
        token_address = get_token_address(token, self.network)
        amount_wei = self._convert_to_wei(token_address, amount)
        
        # Create token contract
        with open(ABI_DIR / 'ERC20.json') as f:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=json.load(f)
            )
        
        decimals = token_contract.functions.decimals().call()
        balance = token_contract.functions.balanceOf(self.account.address).call()
        balance_human = balance / 10**decimals
        
        logger.info(f"Current balance of {token}: {balance_human}")
        
        if balance < amount_wei:
            logger.error(f"Insufficient {token} balance: {balance_human}, needed: {amount}")
            raise ValueError(f"Insufficient {token} balance")
        
        allowance = token_contract.functions.allowance(
            self.account.address, self.contract_address
        ).call()
        
        if allowance < amount_wei:
            approve_tx = token_contract.functions.approve(
                self.contract_address, amount_wei * 10
            )
            
            approve_hash = self._send_transaction(approve_tx)
            logger.info(f"Approved {token} for Compound: {approve_hash}")
            
            time.sleep(2)
        
        try:
            supply_tx = self.contract.functions.supply(token_address, amount_wei)
            tx_hash = self._send_transaction(supply_tx)
            logger.info(f"Supply transaction successful: {tx_hash}")
            return tx_hash
        except Exception as e:
            logger.error(f"Supply transaction failed: {str(e)}")
            current_allowance = token_contract.functions.allowance(
                self.account.address, self.contract_address
            ).call()
            logger.error(f"Current allowance after error: {current_allowance}")
            raise
    
    def withdraw(self, token: str, amount: float) -> str:
        """Withdraw tokens from Compound protocol"""

        token_address = get_token_address(token, self.network)
        amount_wei = self._convert_to_wei(token_address, amount)
        
        # Create token contract
        with open(ABI_DIR / 'ERC20.json') as f:
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=json.load(f)
            )
        
        decimals = token_contract.functions.decimals().call()
        balance = token_contract.functions.balanceOf(self.account.address).call()
        balance_human = balance / 10**decimals
        
        logger.info(f"Current {token} balance in Compound: {balance_human}")
        
        if amount <= 0 or amount > balance_human:
            amount = balance_human
            logger.info(f"Adjusting withdrawal to available balance: {amount}")
                
        withdraw_tx = self.contract.functions.withdraw(token_address, amount_wei)
        return self._send_transaction(withdraw_tx)

class WETHOperator(BaseProtocolOperator):
    """Operator to wrap and unwrap ETH using the WETH contract"""

    def __init__(self, network: str):
        super().__init__(network=network, protocol='weth')
        self.weth_address = Web3.to_checksum_address(WETH_ADDRESS[self.network])
        self.weth = self._load_weth_contract()

    def _load_weth_contract(self) -> Contract:
        """Load the WETH contract"""
        with open(ABI_DIR / 'BasicWETHABI.json') as f:
            abi = json.load(f)
        return self.w3.eth.contract(address=self.weth_address, abi=abi)

    def get_weth_balance(self) -> float:
        """Get the user's current WETH balance in ETH"""
        balance_wei = self.weth.functions.balanceOf(self.account.address).call()
        return balance_wei / 1e18

    def wrap_eth(self, amount_eth: float) -> str:
        """Wrap ETH into WETH"""
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        tx = self.weth.functions.deposit()
        tx_params = self._get_gas_params()
        tx_params['value'] = amount_wei
        return self._send_transaction(tx.build_transaction(tx_params))

    def unwrap_eth(self, amount_eth: float) -> str:
        """Unwrap WETH into ETH"""
        amount_wei = self.w3.to_wei(amount_eth, 'ether')

        balance = self.weth.functions.balanceOf(self.account.address).call()
        if balance < amount_wei:
            raise ValueError(f"Not enough WETH to unwrap: have {balance / 1e18} ETH")

        allowance = self.weth.functions.allowance(self.account.address, self.weth_address).call()
        if allowance < amount_wei:
            approve_tx = self.weth.functions.approve(self.weth_address, amount_wei)
            self._send_transaction(approve_tx)

        tx = self.weth.functions.withdraw(amount_wei)
        return self._send_transaction(tx)   

def get_protocol_operator(network: str, protocol: str, **kwargs):
    """
    Factory function to get the appropriate protocol operator
    """
    try:
        if protocol == 'aave-v3':
            return AaveOperator(network, protocol)
        elif protocol == 'compound-v3':
            return CompoundOperator(network, protocol)
        elif protocol == 'uniswap-v3':
            return UniswapV3Operator(network, protocol)
        elif protocol == 'weth':
            return WETHOperator(network)
        else:
            available_protocols = list(SUPPORTED_PROTOCOLS.keys())
            raise ValueError(f"Unknown protocol: {protocol}. Available: {', '.join(available_protocols)}")
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Error initializing {protocol} on {network}: {str(e)}")


def main():

    # uniswap_operator = get_protocol_operator('Ethereum', 'uniswap-v3')
    # print(uniswap_operator.swap('WETH', 'DAI', 1))

    # weth_operator = get_protocol_operator('Ethereum', 'weth')
    # print(weth_operator.wrap_eth(0.1))
    # time.sleep(10)
    # print(weth_operator.unwrap_eth(0.1))

    compoud_operator = get_protocol_operator('Ethereum', 'compound-v3')
    # compoud_operator.supply('USDC', 10)
    # print(compoud_operator.get_protocol_balance('USDC'))
    # time.sleep(10)
    compoud_operator.withdraw('USDC', 10)

    # aave_operator = get_protocol_operator('Ethereum', 'aave-v3')
    # # print(aave_operator.supply('USDC', 10))
    # # time.sleep(10)
    # print(aave_operator.get_protocol_balance('USDT'))
    # time.sleep(10)
    # aave_operator.withdraw('USDT', 5)

    # aave_operator = get_protocol_operator('Scroll', 'aave-v3')
    # print(aave_operator)
    # aave_operator.supply('USDC', 10)

    # recommendations = get_recommendations(chain='Scroll', same_asset_only=True, min_profit=0.5, debug=False)
    # print(format_recommendations(recommendations))

    # workflow
    # 1. pull latest from couchdb
    # 2. get protocol operator for protocol/token from pulled data
    # 3. execute lend

if __name__ == "__main__":
    sys.exit(main())