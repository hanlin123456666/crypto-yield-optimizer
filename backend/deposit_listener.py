import json
import asyncio
from web3 import Web3
from web3.middleware import async_filter_middleware
import couchdb
from protocol_operator import get_protocol_operator

# Configuration
RPC_URL = "YOUR_RPC_URL"
ZAPVAULT_ADDRESS = "YOUR_ZAPVAULT_ADDRESS"
COUCHDB_URL = "http://admin:password@localhost:5984"  # Update with your CouchDB credentials

# ZapVault ABI - only the events we need
ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "user",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "Deposited",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "user",
                "type": "address"
            },
            {
                "indexed": True,
                "name": "token",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "TokenDeposited",
        "type": "event"
    }
]

class DepositListener:
    def __init__(self):
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(ZAPVAULT_ADDRESS),
            abi=ABI
        )

        # Initialize CouchDB
        self.couch = couchdb.Server(COUCHDB_URL)
        self.db = self.couch['your_database_name']  # Replace with your database name

    async def get_latest_strategy(self):
        """
        Get the latest lending strategy from CouchDB
        Returns: (protocol, apy)
        """
        # View query to get the latest entry
        # Assuming you have a view set up in CouchDB that sorts by timestamp
        result = self.db.view('lending_strategies/by_timestamp', 
                            descending=True, 
                            limit=1)
        
        if len(result.rows) > 0:
            strategy = result.rows[0].value
            return strategy['protocol'], strategy['apy']
        return None, None

    async def handle_eth_deposit(self, event):
        """Handle ETH deposit events"""
        try:
            # Extract event data
            user = event.args.user
            amount = self.w3.from_wei(event.args.amount, 'ether')
            
            print(f"ETH Deposit detected: {amount} ETH from {user}")

            # Get latest lending strategy from CouchDB
            protocol, apy = await self.get_latest_strategy()
            
            if not protocol:
                print("No lending strategy found in CouchDB")
                return

            print(f"Selected protocol: {protocol} with APY: {apy}%")

            # Initialize protocol operator
            operator = get_protocol_operator('Ethereum', protocol)
            
            # Execute lending
            tx_hash = operator.supply('ETH', float(amount))
            
            # Store the lending operation in CouchDB
            doc = {
                'type': 'lending_operation',
                'user': user,
                'amount': float(amount),
                'token': 'ETH',
                'protocol': protocol,
                'apy': apy,
                'tx_hash': tx_hash,
                'timestamp': self.w3.eth.get_block('latest').timestamp
            }
            
            self.db.save(doc)
            print(f"Lending operation recorded: {tx_hash}")

        except Exception as e:
            print(f"Error handling ETH deposit: {str(e)}")

    async def handle_token_deposit(self, event):
        """Handle token deposit events"""
        try:
            user = event.args.user
            token = event.args.token
            amount = event.args.amount
            
            print(f"Token Deposit detected: {amount} of token {token} from {user}")
            
            # Similar logic as ETH deposit but for tokens
            protocol, apy = await self.get_latest_strategy()
            
            if not protocol:
                return

            operator = get_protocol_operator('Ethereum', protocol)
            tx_hash = operator.supply(token, float(amount))
            
            doc = {
                'type': 'lending_operation',
                'user': user,
                'amount': float(amount),
                'token': token,
                'protocol': protocol,
                'apy': apy,
                'tx_hash': tx_hash,
                'timestamp': self.w3.eth.get_block('latest').timestamp
            }
            
            self.db.save(doc)

        except Exception as e:
            print(f"Error handling token deposit: {str(e)}")

    async def listen_for_deposits(self):
        """Listen for both ETH and token deposit events"""
        eth_filter = self.contract.events.Deposited.create_filter(fromBlock='latest')
        token_filter = self.contract.events.TokenDeposited.create_filter(fromBlock='latest')
        
        print("Starting to listen for deposit events...")
        
        while True:
            try:
                # Check for new ETH deposits
                eth_events = eth_filter.get_new_entries()
                for event in eth_events:
                    await self.handle_eth_deposit(event)

                # Check for new token deposits
                token_events = token_filter.get_new_entries()
                for event in token_events:
                    await self.handle_token_deposit(event)

                # Small delay to prevent too many RPC calls
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error in event loop: {str(e)}")
                await asyncio.sleep(5)  # Longer delay on error

async def main():
    listener = DepositListener()
    await listener.listen_for_deposits()

if __name__ == "__main__":
    asyncio.run(main()) 