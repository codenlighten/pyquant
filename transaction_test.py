from src.blockchain import Blockchain
from src.wallet import Wallet
from src.transaction import Transaction
from src.utxo import UTXO, UTXOSet
import time
import pytest
from decimal import Decimal

def print_balances(blockchain, wallets):
    """Print current balances of all wallets"""
    print("\nCurrent Balances:")
    for name, wallet in wallets.items():
        balance = blockchain.get_balance(wallet.address)
        print(f"{name}: {balance} coins")
    print()

def test_transaction_creation():
    """Test basic transaction creation."""
    # Create sender and recipient wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO
    input_amount = Decimal('1.0')
    input_utxo = UTXO(sender_wallet.address, input_amount, "previous_tx_hash")
    
    # Create transaction
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    
    assert tx.sender == sender_wallet.address
    assert tx.recipient == recipient_wallet.address
    assert tx.amount == Decimal('0.5')
    assert tx.fee == Decimal('0.001')
    assert len(tx.inputs) == 1
    assert len(tx.outputs) == 2  # Main output + change

def test_transaction_signing():
    """Test transaction signing with hybrid signatures."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO
    input_utxo = UTXO(sender_wallet.address, Decimal('1.0'), "test_utxo_hash")
    
    # Create and sign transaction
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    tx.sign(sender_wallet)
    
    # Verify signatures exist
    assert tx.ed25519_signature is not None
    assert tx.sphincs_signature is not None
    assert tx.txid is not None

def test_transaction_verification():
    """Test transaction verification with hybrid signatures."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO and add to UTXO set
    input_utxo = UTXO(sender_wallet.address, Decimal('1.0'), "test_utxo_hash")
    utxo_set = UTXOSet()
    utxo_set.add_utxo(input_utxo)
    
    # Create and sign transaction
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    tx.sign(sender_wallet)
    
    # Verify transaction
    assert tx.verify(utxo_set, sender_wallet)

def test_invalid_signatures():
    """Test transaction with invalid signatures."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO
    input_utxo = UTXO(sender_wallet.address, Decimal('1.0'), "test_utxo_hash")
    utxo_set = UTXOSet()
    utxo_set.add_utxo(input_utxo)
    
    # Create and sign transaction
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    tx.sign(sender_wallet)
    
    # Modify signatures
    tx.ed25519_signature = bytearray(tx.ed25519_signature)
    tx.ed25519_signature[0] ^= 1
    tx.sphincs_signature = bytearray(tx.sphincs_signature)
    tx.sphincs_signature[0] ^= 1
    
    # Verify transaction fails
    assert not tx.verify(utxo_set, sender_wallet)

def test_coinbase_transaction():
    """Test coinbase transaction (no signatures needed)."""
    recipient_wallet = Wallet.generate()
    
    # Create coinbase transaction
    tx = Transaction(
        sender=None,
        recipient=recipient_wallet.address,
        amount=Decimal('10.0'),  # Mining reward
        fee=Decimal('0'),
        inputs=[]
    )
    
    # Verify coinbase transaction
    utxo_set = UTXOSet()
    assert tx.verify(utxo_set, recipient_wallet)

def test_change_calculation():
    """Test change calculation and output creation."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO with excess amount
    input_utxo = UTXO(sender_wallet.address, Decimal('1.0'), "test_utxo_hash")
    
    # Create transaction with change
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    
    # Verify outputs
    assert len(tx.outputs) == 2  # Main output + change
    
    # Find change output
    change_output = next(
        out for out in tx.outputs if out.address == sender_wallet.address
    )
    assert change_output.amount == Decimal('0.499')  # 1.0 - 0.5 - 0.001

def test_insufficient_inputs():
    """Test transaction with insufficient inputs."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO with insufficient amount
    input_utxo = UTXO(sender_wallet.address, Decimal('0.4'), "test_utxo_hash")
    utxo_set = UTXOSet()
    utxo_set.add_utxo(input_utxo)
    
    # Create transaction
    tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    tx.sign(sender_wallet)
    
    # Verify transaction fails
    assert not tx.verify(utxo_set, sender_wallet)

def test_serialization():
    """Test transaction serialization and deserialization."""
    # Create wallets
    sender_wallet = Wallet.generate()
    recipient_wallet = Wallet.generate()
    
    # Create input UTXO
    input_utxo = UTXO(sender_wallet.address, Decimal('1.0'), "test_utxo_hash")
    
    # Create and sign original transaction
    original_tx = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_wallet.address,
        amount=Decimal('0.5'),
        fee=Decimal('0.001'),
        inputs=[input_utxo]
    )
    original_tx.sign(sender_wallet)
    
    # Convert to dict and back
    tx_dict = original_tx.to_dict()
    loaded_tx = Transaction.from_dict(tx_dict)
    
    # Verify transaction data matches
    assert loaded_tx.sender == original_tx.sender
    assert loaded_tx.recipient == original_tx.recipient
    assert loaded_tx.amount == original_tx.amount
    assert loaded_tx.fee == original_tx.fee
    assert loaded_tx.ed25519_signature == original_tx.ed25519_signature
    assert loaded_tx.sphincs_signature == original_tx.sphincs_signature
    assert loaded_tx.txid == original_tx.txid

def main():
    # Initialize blockchain with lower difficulty for faster testing
    print("Initializing blockchain...")
    blockchain = Blockchain(difficulty=2)
    
    # Create test wallets
    print("Creating test wallets...")
    wallets = {
        "Alice": Wallet.generate(),
        "Bob": Wallet.generate(),
        "Charlie": Wallet.generate()
    }
    
    # Register all wallets
    for name, wallet in wallets.items():
        blockchain.register_wallet(wallet)
        print(f"{name}'s address: {wallet.address}")
    
    # Initial mining to give Alice some coins
    print("\nMining initial block to give Alice some coins...")
    blockchain.mine_pending_transactions(wallets["Alice"].address)
    print_balances(blockchain, wallets)
    
    # Run transaction tests
    print("\nRunning transaction tests...")
    test_transaction_creation()
    test_transaction_signing()
    test_transaction_verification()
    test_invalid_signatures()
    test_coinbase_transaction()
    test_change_calculation()
    test_insufficient_inputs()
    test_serialization()
    
    # Verify final blockchain state
    print("Verifying final blockchain state...")
    is_valid = blockchain.is_chain_valid()
    print(f"Blockchain is {'valid' if is_valid else 'invalid'}!")

if __name__ == "__main__":
    main()
