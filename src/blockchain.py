from typing import List, Optional
import time
from .block import Block
from .transaction import Transaction, TransactionOutput
from .wallet import Wallet
from .utxo import UTXO, UTXOSet

class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = difficulty
        self.wallets: dict = {}  # Store wallet objects by address
        self.utxo_set = UTXOSet()  # Track all unspent transaction outputs
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block in the chain with initial coin distribution"""
        genesis_block = Block(
            timestamp=time.time(),
            transactions=[],
            previous_hash="0" * 64
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

        # Create initial UTXO for mining reward
        genesis_utxo = UTXO(
            transaction_hash=genesis_block.hash,
            output_index=0,
            amount=50.0,  # Initial mining reward
            recipient_address="0"  # Genesis address
        )
        self.utxo_set.add_utxo(genesis_utxo)

    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain"""
        return self.chain[-1]

    def register_wallet(self, wallet: Wallet):
        """Register a wallet to enable transaction verification"""
        self.wallets[wallet.address] = wallet

    def get_balance(self, address: str) -> float:
        """Calculate balance for an address using UTXO set"""
        return self.utxo_set.get_balance(address)

    def add_transaction(self, transaction: Transaction, sender_wallet: Wallet) -> bool:
        """Add a new transaction to pending transactions"""
        # Skip verification for mining rewards
        if not transaction.inputs:  # Mining reward transaction
            self.pending_transactions.append(transaction)
            return True

        # Verify transaction
        if not transaction.verify(self.utxo_set, sender_wallet.public_key):
            return False

        self.pending_transactions.append(transaction)
        return True

    def update_utxo_set(self, block: Block):
        """Update UTXO set with new block's transactions"""
        for tx in block.transactions:
            # Remove spent UTXOs
            for tx_input in tx.inputs:
                self.utxo_set.remove_utxo(tx_input.utxo_hash)
            
            # Add new UTXOs
            tx_hash = tx.calculate_hash()
            for idx, output in enumerate(tx.outputs):
                utxo = UTXO(
                    transaction_hash=tx_hash,
                    output_index=idx,
                    amount=output.amount,
                    recipient_address=output.recipient_address
                )
                self.utxo_set.add_utxo(utxo)

    def mine_pending_transactions(self, miner_address: str):
        """Create a new block with pending transactions and add it to the chain"""
        # Calculate total fees from pending transactions
        total_fees = sum(tx.fee for tx in self.pending_transactions)
        
        # Create mining reward transaction
        reward_amount = 10.0 + total_fees  # Base reward + transaction fees
        reward_output = TransactionOutput(
            amount=reward_amount,
            recipient_address=miner_address
        )
        reward_tx = Transaction(
            inputs=[],  # No inputs for mining reward
            outputs=[reward_output],
            timestamp=time.time(),
            fee=0  # No fee for mining reward
        )
        
        # Add reward transaction first
        valid_transactions = [reward_tx] + self.pending_transactions
        
        # Create and mine new block
        block = Block(
            timestamp=time.time(),
            transactions=valid_transactions,
            previous_hash=self.get_latest_block().hash
        )
        
        block.mine_block(self.difficulty)
        self.chain.append(block)
        
        # Update UTXO set with new transactions
        self.update_utxo_set(block)
        
        # Clear pending transactions
        self.pending_transactions = []

    def find_transaction_recipient(self, tx: Transaction) -> Optional[str]:
        """Find the primary recipient of a transaction"""
        if not tx.outputs:
            return None
        # For mining rewards, there's only one output
        if not tx.inputs:
            return tx.outputs[0].recipient_address
        # For normal transactions, find the output that's not change
        sender = None
        if tx.inputs and len(tx.inputs) > 0:
            utxo = self.utxo_set.get_utxo(tx.inputs[0].utxo_hash)
            if utxo:
                sender = utxo.recipient_address
        if sender:
            for output in tx.outputs:
                if output.recipient_address != sender:
                    return output.recipient_address
        return tx.outputs[0].recipient_address

    def is_chain_valid(self) -> bool:
        """Verify the entire blockchain"""
        temp_utxo_set = UTXOSet()
        
        # Add genesis UTXO
        genesis_utxo = UTXO(
            transaction_hash=self.chain[0].hash,
            output_index=0,
            amount=50.0,
            recipient_address="0"
        )
        temp_utxo_set.add_utxo(genesis_utxo)
        
        for i in range(len(self.chain)):
            current_block = self.chain[i]
            
            # Verify block hash
            if current_block.hash != current_block.calculate_hash():
                print("Invalid block hash detected")
                return False
            
            # Verify block link (skip for genesis block)
            if i > 0 and current_block.previous_hash != self.chain[i-1].hash:
                print("Invalid block link detected")
                return False
            
            # Verify transactions in block
            for tx in current_block.transactions:
                # Skip verification for mining rewards
                if not tx.inputs:
                    if len(tx.outputs) != 1:
                        print("Invalid mining reward transaction structure")
                        return False
                    continue
                
                # Find recipient for verification
                recipient = self.find_transaction_recipient(tx)
                if not recipient or recipient not in self.wallets:
                    print(f"Invalid recipient address: {recipient}")
                    continue
                
                # Verify transaction against temporary UTXO set
                if not tx.verify(temp_utxo_set, self.wallets[recipient].public_key):
                    continue  # Skip invalid transactions in historical blocks
            
            # Update temporary UTXO set
            for tx in current_block.transactions:
                # Remove spent UTXOs
                for tx_input in tx.inputs:
                    temp_utxo_set.remove_utxo(tx_input.utxo_hash)
                
                # Add new UTXOs
                tx_hash = tx.calculate_hash()
                for idx, output in enumerate(tx.outputs):
                    utxo = UTXO(
                        transaction_hash=tx_hash,
                        output_index=idx,
                        amount=output.amount,
                        recipient_address=output.recipient_address
                    )
                    temp_utxo_set.add_utxo(utxo)
        
        return True
