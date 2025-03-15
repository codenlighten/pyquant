"""
Quantum-resistant signature implementation using SPHINCS+.
Currently using shake256-128f parameter set for a balance of security and performance.
"""

import os
from typing import Tuple, Optional
from dataclasses import dataclass
import json
from decimal import Decimal
import pyspx.shake_128f as sphincs

@dataclass
class KeyPair:
    """Represents a quantum-resistant key pair"""
    public_key: bytes
    private_key: bytes
    seed: bytes  # Store seed for potential key recovery

class QuantumSigner:
    """
    Quantum-resistant signer using SPHINCS+ with shake256-128f parameters.
    This implementation will eventually replace the current Ed25519 signatures.
    """
    
    @staticmethod
    def generate_keypair() -> KeyPair:
        """
        Generate a new SPHINCS+ keypair with a random seed.
        
        Returns:
            KeyPair: Contains public key, private key, and seed
        """
        seed = os.urandom(sphincs.crypto_sign_SEEDBYTES)
        public_key, private_key = sphincs.generate_keypair(seed)
        return KeyPair(public_key=public_key, private_key=private_key, seed=seed)

    @staticmethod
    def sign(message: bytes, private_key: bytes) -> bytes:
        """
        Sign a message using SPHINCS+.
        
        Args:
            message: The message to sign
            private_key: The SPHINCS+ private key
            
        Returns:
            bytes: The signature
        """
        return sphincs.sign(message, private_key)

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a SPHINCS+ signature.
        
        Args:
            message: The original message
            signature: The signature to verify
            public_key: The signer's public key
            
        Returns:
            bool: True if signature is valid
        """
        try:
            return sphincs.verify(message, signature, public_key)
        except Exception:
            return False

    @staticmethod
    def get_key_sizes() -> dict:
        """Get the byte sizes for various SPHINCS+ components."""
        return {
            'public_key': sphincs.crypto_sign_PUBLICKEYBYTES,
            'private_key': sphincs.crypto_sign_SECRETKEYBYTES,
            'signature': sphincs.crypto_sign_BYTES,
            'seed': sphincs.crypto_sign_SEEDBYTES
        }

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class HybridSigner:
    """
    Hybrid signature scheme using both Ed25519 (current) and SPHINCS+ (quantum-resistant).
    This allows for a smooth transition to quantum-resistant signatures while maintaining
    backward compatibility.
    """
    
    def __init__(self, ed25519_private=None, ed25519_public=None, 
                 sphincs_keypair: Optional[KeyPair]=None):
        """
        Initialize with existing keys or generate new ones.
        
        Args:
            ed25519_private: Existing Ed25519 private key
            ed25519_public: Existing Ed25519 public key
            sphincs_keypair: Existing SPHINCS+ keypair
        """
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Ed25519 keys
        self.ed25519_private = ed25519_private or ed25519.Ed25519PrivateKey.generate()
        self.ed25519_public = (ed25519_public or 
                             self.ed25519_private.public_key())
        
        # SPHINCS+ keys
        self.sphincs_keypair = sphincs_keypair or QuantumSigner.generate_keypair()

    def sign_hybrid(self, message: bytes) -> Tuple[bytes, bytes]:
        """
        Sign a message using both Ed25519 and SPHINCS+.
        
        Args:
            message: The message to sign
            
        Returns:
            Tuple[bytes, bytes]: (Ed25519 signature, SPHINCS+ signature)
        """
        ed_sig = self.ed25519_private.sign(message)
        sphincs_sig = QuantumSigner.sign(message, self.sphincs_keypair.private_key)
        return ed_sig, sphincs_sig

    def verify_hybrid(self, message: bytes, ed_sig: bytes, 
                     sphincs_sig: bytes) -> Tuple[bool, bool]:
        """
        Verify both Ed25519 and SPHINCS+ signatures.
        
        Args:
            message: The original message
            ed_sig: The Ed25519 signature
            sphincs_sig: The SPHINCS+ signature
            
        Returns:
            Tuple[bool, bool]: (Ed25519 valid, SPHINCS+ valid)
        """
        # Verify Ed25519
        try:
            self.ed25519_public.verify(ed_sig, message)
            ed_valid = True
        except Exception:
            ed_valid = False

        # Verify SPHINCS+
        sphincs_valid = QuantumSigner.verify(
            message, 
            sphincs_sig, 
            self.sphincs_keypair.public_key
        )

        return ed_valid, sphincs_valid

    def export_public_keys(self) -> Tuple[bytes, bytes]:
        """
        Export both public keys.
        
        Returns:
            Tuple[bytes, bytes]: (Ed25519 public key, SPHINCS+ public key)
        """
        return (
            self.ed25519_public.public_bytes_raw(),
            self.sphincs_keypair.public_key
        )
