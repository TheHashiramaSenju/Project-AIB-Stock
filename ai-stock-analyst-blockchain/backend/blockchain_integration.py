from web3 import Web3
from eth_account import Account
import json
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class BlockchainPortfolioManager:
    """Manages blockchain interactions for portfolio tracking"""
    
    def __init__(self, provider_url: str = "http://127.0.0.1:8545"):
        """
        Initialize blockchain connection
        
        Args:
            provider_url: RPC endpoint URL 
        """
        self.provider_url = provider_url
        self.w3 = None
        self.contract_address = None
        self.contract = None
        self.account = None
        self.private_key = None
        self.connected = False
        
        self._connect_to_provider()
    
    def _connect_to_provider(self) -> bool:
        """Establish connection to blockchain provider"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.provider_url))
            
            if self.w3.is_connected():
                chain_id = self.w3.eth.chain_id
                block_number = self.w3.eth.block_number
                
                print(f"✅ Connected to blockchain")
                print(f"   Chain ID: {chain_id}")
                print(f"   Block Number: {block_number}")
                print(f"   Provider: {self.provider_url}")
                
                self.connected = True
                return True
            else:
                print(f"❌ Failed to connect to {self.provider_url}")
                self.connected = False
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            self.connected = False
            return False
    
    def connect_wallet(self, private_key: str) -> Optional[str]:
        """
        Connect user wallet using private key
        
        Args:
            private_key: Ethereum private key (with or without 0x prefix)
            
        Returns:
            Wallet address if successful, None otherwise
        """
        if not self.connected:
            print("❌ Not connected to blockchain provider")
            return None
        
        try:
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            self.private_key = private_key
            self.account = Account.from_key(private_key)
            
            balance = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            
            print(f"\n✅ Wallet Connected")
            print(f"   Address: {self.account.address}")
            print(f"   Balance: {balance_eth:.6f} ETH")
            
            if balance == 0:
                print(f"   ⚠️  Warning: Zero balance - cannot send transactions")
            
            return self.account.address
            
        except Exception as e:
            print(f"❌ Wallet connection failed: {str(e)}")
            self.account = None
            self.private_key = None
            return None
    
    def load_contract(self, contract_address: str, abi_path: str = None) -> bool:
        """
        Load smart contract
        
        Args:
            contract_address: Deployed contract address
            abi_path: Path to ABI JSON file
            
        Returns:
            True if successful
        """
        if not self.connected:
            print("❌ Not connected to blockchain")
            return False
        
        try:
            self.contract_address = Web3.to_checksum_address(contract_address)
            
            if abi_path is None:
                abi_path = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
            
            if not os.path.exists(abi_path):
                print(f"❌ ABI file not found: {abi_path}")
                return False
            
            with open(abi_path, 'r') as f:
                contract_abi = json.load(f)
            
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=contract_abi
            )
            
            try:
                counter = self.contract.functions.investmentCounter().call()
                print(f"\n✅ Contract Loaded")
                print(f"   Address: {self.contract_address}")
                print(f"   Total Investments: {counter}")
            except Exception as e:
                print(f"⚠️  Contract loaded but verification failed: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Contract loading failed: {str(e)}")
            return False
    
    def add_investment_to_blockchain(
        self,
        company: str,
        symbol: str,
        shares: float,
        purchase_price: float
    ) -> Optional[Tuple[str, int]]:
        """
        Add investment to blockchain
        
        Args:
            company: Company name
            symbol: Stock symbol
            shares: Number of shares
            purchase_price: Purchase price per share
            
        Returns:
            Tuple of (transaction_hash, gas_used) if successful, None otherwise
        """
        if not self.contract or not self.account:
            print("❌ Contract or wallet not connected")
            return None
        
        try:
            shares_uint = int(shares * 100)
            price_uint = int(purchase_price * 100)
            
            print(f"\n⏳ Adding investment to blockchain...")
            print(f"   Company: {company}")
            print(f"   Symbol: {symbol}")
            print(f"   Shares: {shares}")
            print(f"   Price: ${purchase_price}")
            
            gas_estimate = self.contract.functions.addInvestment(
                company,
                symbol,
                shares_uint,
                price_uint
            ).estimate_gas({'from': self.account.address})
            
            print(f"   Estimated Gas: {gas_estimate}")
            
            transaction = self.contract.functions.addInvestment(
                company,
                symbol,
                shares_uint,
                price_uint
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                self.private_key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"   Transaction sent: {tx_hash.hex()}")
            print(f"   Waiting for confirmation...")
            
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt['status'] == 1:
                print(f"   ✅ Confirmed in block {tx_receipt['blockNumber']}")
                print(f"   Gas used: {tx_receipt['gasUsed']}")
                return (tx_hash.hex(), tx_receipt['gasUsed'])
            else:
                print(f"   ❌ Transaction failed")
                return None
                
        except Exception as e:
            print(f"❌ Blockchain transaction error: {str(e)}")
            return None
    
    def get_my_investments(self) -> List[Dict]:
        """
        Fetch all active investments from blockchain
        
        Returns:
            List of investment dictionaries
        """
        if not self.contract or not self.account:
            print("❌ Contract or wallet not connected")
            return []
        
        try:
            print(f"\n⏳ Fetching investments from blockchain...")
            
            investment_ids = self.contract.functions.getMyInvestmentIds().call({
                'from': self.account.address
            })
            
            print(f"   Found {len(investment_ids)} total investments")
            
            investments = []
            
            for inv_id in investment_ids:
                try:
                    inv_data = self.contract.functions.getInvestment(inv_id).call({
                        'from': self.account.address
                    })
                    
                    if inv_data[5]:
                        investments.append({
                            'blockchain_id': int(inv_id),
                            'company': inv_data[0],
                            'symbol': inv_data[1],
                            'shares': float(inv_data[2]) / 100,
                            'purchase_price': float(inv_data[3]) / 100,
                            'timestamp': int(inv_data[4]),
                            'purchase_date': datetime.fromtimestamp(inv_data[4]).strftime("%Y-%m-%d"),
                            'active': inv_data[5]
                        })
                
                except Exception as e:
                    print(f"   ⚠️  Error fetching investment {inv_id}: {str(e)}")
                    continue
            
            print(f"   ✅ Retrieved {len(investments)} active investments")
            return investments
            
        except Exception as e:
            print(f"❌ Error fetching investments: {str(e)}")
            return []
    
    def remove_investment_from_blockchain(self, investment_id: int) -> Optional[str]:
        """
        Remove investment from blockchain
        
        Args:
            investment_id: Blockchain investment ID
            
        Returns:
            Transaction hash if successful
        """
        if not self.contract or not self.account:
            return None
        
        try:
            print(f"\n⏳ Removing investment #{investment_id}...")
            
            transaction = self.contract.functions.removeInvestment(
                investment_id
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                self.private_key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt['status'] == 1:
                print(f"   ✅ Investment removed. TX: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                print(f"   ❌ Removal failed")
                return None
                
        except Exception as e:
            print(f"❌ Error removing investment: {str(e)}")
            return None
    
    def get_portfolio_stats(self) -> Dict:
        """Get portfolio statistics from blockchain"""
        if not self.contract or not self.account:
            return {}
        
        try:
            active_count = self.contract.functions.getActiveInvestmentCount().call({
                'from': self.account.address
            })
            
            total_invested = self.contract.functions.getTotalInvested().call({
                'from': self.account.address
            })
            
            return {
                'active_count': int(active_count),
                'total_invested': float(total_invested) / 10000,
                'wallet_address': self.account.address,
                'contract_address': self.contract_address
            }
            
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return {}
    
    def verify_transaction(self, tx_hash: str) -> Dict:
        """
        Verify blockchain transaction
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details dictionary
        """
        if not self.connected:
            return {'confirmed': False, 'error': 'Not connected'}
        
        try:
            if not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'confirmed': receipt['status'] == 1,
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': tx_hash,
                'from': receipt['from'],
                'to': receipt['to']
            }
            
        except Exception as e:
            return {'confirmed': False, 'error': str(e)}
    
    def get_connection_info(self) -> str:
        """Get formatted connection information"""
        if not self.connected:
            return "❌ Not connected to blockchain"
        
        info = f"""
🔗 **Blockchain Connection**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider: {self.provider_url}
Chain ID: {self.w3.eth.chain_id}
Block Number: {self.w3.eth.block_number}
"""
        
        if self.account:
            balance = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            info += f"""
Wallet: {self.account.address}
Balance: {balance_eth:.6f} ETH
"""
        
        if self.contract_address:
            info += f"""
Contract: {self.contract_address}
"""
        
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return info

