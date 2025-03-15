"""
Test suite for quantum-resistant signature implementation.
Tests both standalone SPHINCS+ and hybrid signature functionality.
"""

import pytest
from src.quantum_sig import QuantumSigner, HybridSigner, KeyPair
import json
from decimal import Decimal

def test_sphincs_key_generation():
    """Test SPHINCS+ key generation and sizes."""
    # Generate keypair
    keypair = QuantumSigner.generate_keypair()
    
    # Get expected sizes
    sizes = QuantumSigner.get_key_sizes()
    
    # Verify key sizes
    assert len(keypair.public_key) == sizes['public_key']
    assert len(keypair.private_key) == sizes['private_key']
    assert len(keypair.seed) == sizes['seed']

def test_sphincs_sign_verify():
    """Test SPHINCS+ signing and verification."""
    # Generate keypair
    keypair = QuantumSigner.generate_keypair()
    
    # Test message
    message = b"Test message for SPHINCS+ signature"
    
    # Sign message
    signature = QuantumSigner.sign(message, keypair.private_key)
    
    # Verify signature
    assert QuantumSigner.verify(message, signature, keypair.public_key)
    
    # Test invalid signature
    invalid_sig = bytearray(signature)
    invalid_sig[0] ^= 1  # Flip one bit
    assert not QuantumSigner.verify(message, bytes(invalid_sig), keypair.public_key)

def test_hybrid_signature():
    """Test hybrid Ed25519 + SPHINCS+ signing."""
    # Create hybrid signer
    signer = HybridSigner()
    
    # Test message
    message = b"Test message for hybrid signature"
    
    # Sign with both algorithms
    ed_sig, sphincs_sig = signer.sign_hybrid(message)
    
    # Verify both signatures
    ed_valid, sphincs_valid = signer.verify_hybrid(message, ed_sig, sphincs_sig)
    assert ed_valid
    assert sphincs_valid
    
    # Test invalid signatures
    invalid_ed = bytearray(ed_sig)
    invalid_ed[0] ^= 1
    invalid_sphincs = bytearray(sphincs_sig)
    invalid_sphincs[0] ^= 1
    
    # Both should fail
    ed_valid, sphincs_valid = signer.verify_hybrid(
        message, 
        bytes(invalid_ed), 
        bytes(invalid_sphincs)
    )
    assert not ed_valid
    assert not sphincs_valid

def test_json_serialization():
    """Test JSON serialization with Decimal values."""
    data = {
        'amount': Decimal('123.45678'),
        'fee': Decimal('0.001')
    }
    
    # Test serialization
    from src.quantum_sig import DecimalEncoder
    json_str = json.dumps(data, cls=DecimalEncoder)
    
    # Test deserialization
    decoded = json.loads(json_str)
    assert decoded['amount'] == '123.45678'
    assert decoded['fee'] == '0.001'

def test_key_export():
    """Test public key export functionality."""
    signer = HybridSigner()
    ed_pub, sphincs_pub = signer.export_public_keys()
    
    # Verify key types and sizes
    assert isinstance(ed_pub, bytes)
    assert isinstance(sphincs_pub, bytes)
    assert len(ed_pub) == 32  # Ed25519 public key size
    assert len(sphincs_pub) == QuantumSigner.get_key_sizes()['public_key']

def test_large_message():
    """Test signing and verifying a large message."""
    # Generate 1MB of random data
    import os
    large_message = os.urandom(1024 * 1024)
    
    # Create signer
    signer = HybridSigner()
    
    # Sign and verify
    ed_sig, sphincs_sig = signer.sign_hybrid(large_message)
    ed_valid, sphincs_valid = signer.verify_hybrid(large_message, ed_sig, sphincs_sig)
    
    assert ed_valid
    assert sphincs_valid

if __name__ == '__main__':
    pytest.main([__file__])
