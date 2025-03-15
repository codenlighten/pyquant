"""
Test suite for Merkle tree implementation.
"""

import pytest
from decimal import Decimal
from src.transaction import Transaction, TransactionOutput
from src.utxo import UTXO
from src.merkle import MerkleTree

def test_merkle_tree():
    """Test Merkle tree functionality."""
    # Create test transactions
    tx1 = Transaction(
        sender=None,  # Coinbase
        recipient="recipient1",
        amount=Decimal('10.0'),
        fee=Decimal('0'),
        inputs=[]
    )
    
    tx2 = Transaction(
        sender="sender2",
        recipient="recipient2",
        amount=Decimal('5.0'),
        fee=Decimal('0.001'),
        inputs=[
            UTXO("sender2", Decimal('10.0'), "prev_tx_hash")
        ]
    )
    
    # Create Merkle tree
    transactions = [tx1, tx2]
    merkle_tree = MerkleTree(transactions)
    
    # Verify root hash exists
    assert merkle_tree.root_hash is not None
    assert isinstance(merkle_tree.root_hash, str)
    assert len(merkle_tree.root_hash) == 64  # SHA256 hash length

def test_empty_merkle_tree():
    """Test Merkle tree with no transactions raises error."""
    with pytest.raises(ValueError, match="Cannot create Merkle tree with no transactions"):
        MerkleTree([])

def test_single_transaction():
    """Test Merkle tree with a single transaction."""
    tx = Transaction(
        sender=None,
        recipient="recipient",
        amount=Decimal('10.0'),
        fee=Decimal('0'),
        inputs=[]
    )
    
    merkle_tree = MerkleTree([tx])
    assert merkle_tree.root_hash == MerkleTree.hash_transaction(tx)

def test_odd_number_transactions():
    """Test Merkle tree with odd number of transactions."""
    transactions = [
        Transaction(
            sender=None,
            recipient=f"recipient{i}",
            amount=Decimal('10.0'),
            fee=Decimal('0'),
            inputs=[]
        )
        for i in range(3)
    ]
    
    merkle_tree = MerkleTree(transactions)
    assert merkle_tree.root_hash is not None
    assert isinstance(merkle_tree.root_hash, str)

def test_verify_transaction():
    """Test transaction verification in Merkle tree."""
    # Create transactions
    transactions = [
        Transaction(
            sender=None,
            recipient=f"recipient{i}",
            amount=Decimal('10.0'),
            fee=Decimal('0'),
            inputs=[]
        )
        for i in range(4)
    ]
    
    # Create Merkle tree
    merkle_tree = MerkleTree(transactions)
    
    # Verify each transaction
    for tx in transactions:
        proof = merkle_tree.get_proof(tx)
        assert merkle_tree.verify_proof(tx, proof)

def test_invalid_proof():
    """Test invalid Merkle proof."""
    # Create transactions
    tx1 = Transaction(
        sender=None,
        recipient="recipient1",
        amount=Decimal('10.0'),
        fee=Decimal('0'),
        inputs=[]
    )
    
    tx2 = Transaction(
        sender=None,
        recipient="recipient2",
        amount=Decimal('10.0'),
        fee=Decimal('0'),
        inputs=[]
    )
    
    # Create Merkle tree with tx1
    merkle_tree = MerkleTree([tx1])
    
    # Try to verify tx2 with tx1's proof
    proof = merkle_tree.get_proof(tx1)
    assert not merkle_tree.verify_proof(tx2, proof)

def test_modified_transaction():
    """Test Merkle proof with modified transaction."""
    # Create original transaction
    tx = Transaction(
        sender=None,
        recipient="recipient",
        amount=Decimal('10.0'),
        fee=Decimal('0'),
        inputs=[]
    )
    
    # Create Merkle tree and get proof
    merkle_tree = MerkleTree([tx])
    proof = merkle_tree.get_proof(tx)
    
    # Modify transaction
    modified_tx = Transaction(
        sender=None,
        recipient="recipient",
        amount=Decimal('20.0'),  # Changed amount
        fee=Decimal('0'),
        inputs=[]
    )
    
    # Verify proof fails with modified transaction
    assert not merkle_tree.verify_proof(modified_tx, proof)

if __name__ == '__main__':
    pytest.main([__file__])
