"""
Test suite for the updated Wallet implementation with hybrid signatures.
Tests both Ed25519 and SPHINCS+ functionality.
"""

import pytest
import os
from src.wallet import Wallet
from src.quantum_sig import HybridSigner, KeyPair
from cryptography.hazmat.primitives.asymmetric import ed25519

def test_wallet_creation():
    """Test creating a new wallet with hybrid signatures."""
    # Create new wallet
    wallet = Wallet.generate()
    
    # Verify wallet properties
    assert wallet.address is not None
    assert len(wallet.address) == 40
    assert wallet.ed25519_public is not None
    assert wallet.sphincs_public is not None
    
    # Verify quantum readiness
    wallet_dict = wallet.to_dict()
    assert wallet_dict['quantum_ready'] is True
    assert 'ed25519_public' in wallet_dict
    assert 'sphincs_public' in wallet_dict

def test_legacy_wallet_upgrade():
    """Test creating a wallet from legacy Ed25519 key."""
    # Create legacy private key
    legacy_key = ed25519.Ed25519PrivateKey.generate()
    
    # Create wallet with legacy key
    wallet = Wallet(ed25519_private=legacy_key)
    
    # Verify hybrid upgrade
    assert wallet.ed25519_public is not None
    assert wallet.sphincs_public is not None
    assert wallet.to_dict()['quantum_ready'] is True

def test_wallet_save_load():
    """Test saving and loading wallet with both key types."""
    # Create wallet
    original_wallet = Wallet.generate()
    
    # Save to temporary file
    temp_file = "temp_wallet.dat"
    original_wallet.save_to_file(temp_file)
    
    try:
        # Load wallet
        loaded_wallet = Wallet.load_from_file(temp_file)
        
        # Verify keys match
        assert loaded_wallet.ed25519_public == original_wallet.ed25519_public
        assert loaded_wallet.sphincs_public == original_wallet.sphincs_public
        assert loaded_wallet.address == original_wallet.address
        
        # Test signing with loaded wallet
        message = b"Test message"
        ed_sig1, sphincs_sig1 = original_wallet.sign_message(message)
        ed_sig2, sphincs_sig2 = loaded_wallet.sign_message(message)
        
        # Verify signatures are valid
        ed_valid1, sphincs_valid1 = original_wallet.verify_message(
            message, ed_sig1, sphincs_sig1
        )
        ed_valid2, sphincs_valid2 = loaded_wallet.verify_message(
            message, ed_sig2, sphincs_sig2
        )
        
        assert ed_valid1 and sphincs_valid1
        assert ed_valid2 and sphincs_valid2
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_legacy_wallet_load():
    """Test loading a legacy wallet file."""
    # Create legacy wallet file
    legacy_key = ed25519.Ed25519PrivateKey.generate()
    temp_file = "temp_legacy_wallet.dat"
    
    with open(temp_file, 'wb') as f:
        f.write(legacy_key.private_bytes_raw())
    
    try:
        # Load legacy wallet
        wallet = Wallet.load_from_file(temp_file)
        
        # Verify upgrade to hybrid
        assert wallet.ed25519_public is not None
        assert wallet.sphincs_public is not None
        assert wallet.to_dict()['quantum_ready'] is True
        
        # Test signing
        message = b"Test message"
        ed_sig, sphincs_sig = wallet.sign_message(message)
        ed_valid, sphincs_valid = wallet.verify_message(message, ed_sig, sphincs_sig)
        
        assert ed_valid and sphincs_valid
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_message_signing():
    """Test message signing and verification with hybrid signatures."""
    wallet = Wallet.generate()
    message = b"Test message for hybrid signing"
    
    # Sign message
    ed_sig, sphincs_sig = wallet.sign_message(message)
    
    # Verify valid signatures
    ed_valid, sphincs_valid = wallet.verify_message(message, ed_sig, sphincs_sig)
    assert ed_valid
    assert sphincs_valid
    
    # Test invalid signatures
    invalid_ed = bytearray(ed_sig)
    invalid_ed[0] ^= 1
    invalid_sphincs = bytearray(sphincs_sig)
    invalid_sphincs[0] ^= 1
    
    # Verify invalid signatures fail
    ed_valid, sphincs_valid = wallet.verify_message(
        message, bytes(invalid_ed), sphincs_sig
    )
    assert not ed_valid
    assert sphincs_valid
    
    ed_valid, sphincs_valid = wallet.verify_message(
        message, ed_sig, bytes(invalid_sphincs)
    )
    assert ed_valid
    assert not sphincs_valid

def test_large_message():
    """Test signing and verifying a large message."""
    wallet = Wallet.generate()
    large_message = os.urandom(1024 * 1024)  # 1MB message
    
    # Sign large message
    ed_sig, sphincs_sig = wallet.sign_message(large_message)
    
    # Verify signatures
    ed_valid, sphincs_valid = wallet.verify_message(large_message, ed_sig, sphincs_sig)
    assert ed_valid
    assert sphincs_valid

if __name__ == '__main__':
    pytest.main([__file__])
