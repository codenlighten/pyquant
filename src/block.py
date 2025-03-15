from typing import List
import time
from cryptography.hazmat.primitives import hashes
import json
from .transaction import Transaction
from .merkle import MerkleTree

class Block:
    def __init__(self, timestamp: float, transactions: List[Transaction], previous_hash: str):
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.merkle_tree = self._create_merkle_tree()
        self.hash = self.calculate_hash()

    def _create_merkle_tree(self) -> MerkleTree:
        """Create Merkle tree from block's transactions"""
        # Convert transactions to dictionaries for hashing
        tx_dicts = [tx.to_dict() for tx in self.transactions]
        if not tx_dicts:
            # Create a dummy transaction for empty blocks
            tx_dicts = [{"type": "empty_block"}]
        return MerkleTree(tx_dicts)

    def calculate_hash(self) -> str:
        """Calculate block hash including merkle root"""
        block_header = {
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_tree.get_root_hash(),
            'nonce': self.nonce
        }
        header_string = json.dumps(block_header, sort_keys=True)
        digest = hashes.Hash(hashes.SHA256())
        digest.update(header_string.encode())
        return digest.finalize().hex()

    def mine_block(self, difficulty: int):
        """Mine the block with proof of work"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def verify_transaction(self, transaction: Transaction, index: int) -> bool:
        """Verify a transaction is included in the block using Merkle proof"""
        if index < 0 or index >= len(self.transactions):
            return False
        
        # Verify transaction matches the one at the given index
        if transaction != self.transactions[index]:
            return False
        
        # Get and verify Merkle proof
        proof = self.merkle_tree.get_proof(index)
        return self.merkle_tree.verify_proof(transaction.to_dict(), proof)

    def get_transaction_proof(self, index: int) -> List[dict]:
        """Get Merkle proof for a transaction at given index"""
        return self.merkle_tree.get_proof(index)

    def to_dict(self) -> dict:
        """Convert block to dictionary format"""
        return {
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_tree.get_root_hash(),
            'hash': self.hash
        }
