"""
Test suite for UTXO and UTXOSet implementation.
"""

import pytest
from decimal import Decimal
from src.utxo import UTXO, UTXOSet
from src.wallet import Wallet

def test_utxo_creation():
    """Test basic UTXO creation."""
    # Create wallet for address
    wallet = Wallet.generate()
    
    # Create UTXO
    amount = Decimal('1.0')
    utxo = UTXO(wallet.address, amount)
    
    assert utxo.address == wallet.address
    assert utxo.amount == amount
    assert not utxo.spent
    assert utxo.txid is None

def test_utxo_with_txid():
    """Test UTXO creation with transaction ID."""
    wallet = Wallet.generate()
    amount = Decimal('1.0')
    txid = "test_transaction_hash"
    
    utxo = UTXO(wallet.address, amount, txid)
    
    assert utxo.address == wallet.address
    assert utxo.amount == amount
    assert utxo.txid == txid
    assert not utxo.spent

def test_utxo_decimal_handling():
    """Test UTXO handles decimal amounts correctly."""
    wallet = Wallet.generate()
    
    # Test various decimal formats
    amounts = [
        ('1.0', Decimal('1.0')),
        ('0.12345678', Decimal('0.12345678')),
        (Decimal('1.23456789'), Decimal('1.23456789')),
        ('10', Decimal('10'))
    ]
    
    for input_amount, expected_amount in amounts:
        utxo = UTXO(wallet.address, input_amount)
        assert utxo.amount == expected_amount
        assert isinstance(utxo.amount, Decimal)

def test_utxo_serialization():
    """Test UTXO serialization and deserialization."""
    wallet = Wallet.generate()
    amount = Decimal('1.23456789')
    txid = "test_transaction_hash"
    
    # Create original UTXO
    original_utxo = UTXO(wallet.address, amount, txid)
    original_utxo.spent = True
    
    # Convert to dict and back
    utxo_dict = original_utxo.to_dict()
    loaded_utxo = UTXO.from_dict(utxo_dict)
    
    # Verify all attributes match
    assert loaded_utxo.address == original_utxo.address
    assert loaded_utxo.amount == original_utxo.amount
    assert loaded_utxo.txid == original_utxo.txid
    assert loaded_utxo.spent == original_utxo.spent

def test_utxo_string_representation():
    """Test UTXO string representation."""
    wallet = Wallet.generate()
    amount = Decimal('1.0')
    txid = "test_txid"
    
    utxo = UTXO(wallet.address, amount, txid)
    str_rep = str(utxo)
    
    # Verify all important info is in string representation
    assert wallet.address in str_rep
    assert str(amount) in str_rep
    assert txid in str_rep
    assert 'spent=False' in str_rep

def test_utxo_spending():
    """Test UTXO spending flag."""
    wallet = Wallet.generate()
    amount = Decimal('1.0')
    
    utxo = UTXO(wallet.address, amount)
    assert not utxo.spent
    
    # Mark as spent
    utxo.spent = True
    assert utxo.spent
    
    # Verify spent status persists through serialization
    loaded_utxo = UTXO.from_dict(utxo.to_dict())
    assert loaded_utxo.spent

# UTXOSet Tests

def test_utxo_set_creation():
    """Test UTXOSet initialization."""
    utxo_set = UTXOSet()
    assert len(utxo_set.utxos) == 0

def test_utxo_set_add_remove():
    """Test adding and removing UTXOs from set."""
    utxo_set = UTXOSet()
    wallet = Wallet.generate()
    
    # Create and add UTXO
    utxo = UTXO(wallet.address, Decimal('1.0'), "test_txid")
    utxo_set.add_utxo(utxo)
    
    # Verify UTXO was added
    assert "test_txid" in utxo_set.utxos
    assert utxo_set.get_utxo("test_txid") == utxo
    
    # Remove UTXO
    utxo_set.remove_utxo("test_txid")
    assert "test_txid" not in utxo_set.utxos

def test_utxo_set_get_balance():
    """Test balance calculation for address."""
    utxo_set = UTXOSet()
    wallet = Wallet.generate()
    
    # Add multiple UTXOs
    amounts = [Decimal('1.0'), Decimal('2.5'), Decimal('0.75')]
    for i, amount in enumerate(amounts):
        utxo = UTXO(wallet.address, amount, f"txid_{i}")
        utxo_set.add_utxo(utxo)
    
    # Verify total balance
    expected_balance = sum(amounts)
    assert utxo_set.get_balance(wallet.address) == expected_balance
    
    # Mark one UTXO as spent
    utxo_set.mark_as_spent("txid_0")
    expected_balance -= amounts[0]
    assert utxo_set.get_balance(wallet.address) == expected_balance

def test_utxo_set_get_utxos_for_address():
    """Test retrieving UTXOs for specific address."""
    utxo_set = UTXOSet()
    wallet1 = Wallet.generate()
    wallet2 = Wallet.generate()
    
    # Add UTXOs for both addresses
    utxo1 = UTXO(wallet1.address, Decimal('1.0'), "txid_1")
    utxo2 = UTXO(wallet1.address, Decimal('2.0'), "txid_2")
    utxo3 = UTXO(wallet2.address, Decimal('3.0'), "txid_3")
    
    utxo_set.add_utxo(utxo1)
    utxo_set.add_utxo(utxo2)
    utxo_set.add_utxo(utxo3)
    
    # Verify UTXOs for wallet1
    wallet1_utxos = utxo_set.get_utxos_for_address(wallet1.address)
    assert len(wallet1_utxos) == 2
    assert all(utxo.address == wallet1.address for utxo in wallet1_utxos)
    
    # Mark one UTXO as spent
    utxo_set.mark_as_spent("txid_1")
    wallet1_utxos = utxo_set.get_utxos_for_address(wallet1.address)
    assert len(wallet1_utxos) == 1
    assert wallet1_utxos[0].txid == "txid_2"

def test_utxo_set_serialization():
    """Test UTXOSet serialization and deserialization."""
    utxo_set = UTXOSet()
    wallet = Wallet.generate()
    
    # Add multiple UTXOs
    for i in range(3):
        utxo = UTXO(wallet.address, Decimal(f'{i+1}.0'), f"txid_{i}")
        if i == 1:  # Mark one as spent
            utxo.spent = True
        utxo_set.add_utxo(utxo)
    
    # Convert to dict and back
    utxo_set_dict = utxo_set.to_dict()
    loaded_set = UTXOSet.from_dict(utxo_set_dict)
    
    # Verify UTXOs match
    assert len(loaded_set.utxos) == len(utxo_set.utxos)
    for txid, utxo in utxo_set.utxos.items():
        loaded_utxo = loaded_set.utxos[txid]
        assert loaded_utxo.address == utxo.address
        assert loaded_utxo.amount == utxo.amount
        assert loaded_utxo.spent == utxo.spent

if __name__ == '__main__':
    pytest.main([__file__])
