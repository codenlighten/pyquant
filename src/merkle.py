"""
Merkle tree implementation for transaction verification.
"""

import json
import hashlib
from typing import List, Dict, Optional
from decimal import Decimal
from .transaction import Transaction

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, Transaction):
            return obj.to_dict()
        return super().default(obj)

class MerkleNode:
    """Node in a Merkle tree."""
    
    def __init__(self, hash_value: str):
        """
        Initialize a Merkle node.
        
        Args:
            hash_value: Hash value for this node
        """
        self.hash = hash_value
        self.left = None
        self.right = None

class MerkleTree:
    """
    Merkle tree implementation for transaction verification.
    Supports both Ed25519 and SPHINCS+ signed transactions.
    """
    
    def __init__(self, transactions: List[Transaction]):
        """
        Initialize Merkle tree with list of transactions.
        
        Args:
            transactions: List of transactions to include in tree
        """
        if not transactions:
            raise ValueError("Cannot create Merkle tree with no transactions")
        
        self.transactions = transactions
        self.leaves = []
        self.root = None
        self.root_hash = None
        
        # Build the tree
        self.build_tree(transactions)
    
    @staticmethod
    def hash_data(data) -> str:
        """Hash data for Merkle tree."""
        data_string = json.dumps(data, sort_keys=True, cls=DecimalEncoder)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    @staticmethod
    def hash_transaction(tx: Transaction) -> str:
        """Hash a transaction for Merkle tree."""
        return MerkleTree.hash_data(tx.to_dict())
    
    def build_tree(self, transactions: List[Transaction]) -> None:
        """Build Merkle tree from transactions."""
        # Create leaf nodes
        self.leaves = [
            MerkleNode(self.hash_transaction(tx))
            for tx in transactions
        ]
        
        # Build tree from leaves
        nodes = self.leaves
        while len(nodes) > 1:
            temp = []
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else left
                
                parent = MerkleNode(
                    hashlib.sha256(
                        (left.hash + right.hash).encode()
                    ).hexdigest()
                )
                parent.left = left
                parent.right = right
                temp.append(parent)
            nodes = temp
        
        self.root = nodes[0]
        self.root_hash = self.root.hash
    
    def get_proof(self, tx: Transaction) -> List[Dict[str, str]]:
        """
        Get Merkle proof for transaction.
        
        Args:
            tx: Transaction to get proof for
            
        Returns:
            List of proof elements (each containing sibling hash and position)
        """
        tx_hash = self.hash_transaction(tx)
        proof = []
        nodes = self.leaves
        
        # Find transaction index
        tx_index = None
        for i, node in enumerate(nodes):
            if node.hash == tx_hash:
                tx_index = i
                break
        
        if tx_index is None:
            return []
        
        # Build proof
        current_index = tx_index
        while len(nodes) > 1:
            temp = []
            for i in range(0, len(nodes), 2):
                if i == current_index or i + 1 == current_index:
                    # Add sibling to proof
                    is_right = current_index % 2 == 0
                    sibling_index = i + 1 if is_right else i
                    if sibling_index < len(nodes):
                        proof.append({
                            'hash': nodes[sibling_index].hash,
                            'position': 'right' if is_right else 'left'
                        })
                
                # Create parent node
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else left
                parent = MerkleNode(
                    hashlib.sha256(
                        (left.hash + right.hash).encode()
                    ).hexdigest()
                )
                parent.left = left
                parent.right = right
                temp.append(parent)
            
            # Update current index for next level
            current_index = current_index // 2
            nodes = temp
        
        return proof
    
    def verify_proof(self, tx: Transaction, proof: List[Dict[str, str]]) -> bool:
        """
        Verify Merkle proof for transaction.
        
        Args:
            tx: Transaction to verify
            proof: Merkle proof from get_proof
            
        Returns:
            bool: True if proof is valid
        """
        if not proof:
            return False
        
        current_hash = self.hash_transaction(tx)
        
        for element in proof:
            sibling_hash = element['hash']
            if element['position'] == 'right':
                current_hash = hashlib.sha256(
                    (current_hash + sibling_hash).encode()
                ).hexdigest()
            else:
                current_hash = hashlib.sha256(
                    (sibling_hash + current_hash).encode()
                ).hexdigest()
        
        return current_hash == self.root_hash
