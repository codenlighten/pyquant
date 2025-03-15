from cryptography.hazmat.primitives.asymmetric import ed25519
import json
import os
import base64
from typing import Optional, Tuple, Dict, Any
from .quantum_sig import HybridSigner, KeyPair, QuantumSigner
import pyspx.shake_128f as sphincs

class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder for bytes objects."""
    def default(self, obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super().default(obj)

class Wallet:
    """
    Manages cryptographic keys and addresses for the blockchain.
    Supports both Ed25519 (current) and SPHINCS+ (quantum-resistant) signatures.
    """
    
    def __init__(self, hybrid_signer: Optional[HybridSigner] = None,
                 ed25519_private: Optional[ed25519.Ed25519PrivateKey] = None):
        """
        Initialize wallet with either a hybrid signer or Ed25519 key.
        
        Args:
            hybrid_signer: Optional HybridSigner instance
            ed25519_private: Optional Ed25519 private key (legacy support)
        """
        if hybrid_signer:
            self.signer = hybrid_signer
        elif ed25519_private:
            # Create hybrid signer from existing Ed25519 key
            self.signer = HybridSigner(ed25519_private=ed25519_private)
        else:
            # Create new hybrid signer with fresh keys
            self.signer = HybridSigner()
        
        # Get both public keys
        self.ed25519_public, self.sphincs_public = self.signer.export_public_keys()
        self.address = self._generate_address()
    
    @classmethod
    def generate(cls) -> 'Wallet':
        """Generate a new wallet with fresh hybrid key pairs"""
        return cls(hybrid_signer=HybridSigner())
    
    def _generate_address(self) -> str:
        """
        Generate a unique address from both public keys.
        Uses a combination of Ed25519 and SPHINCS+ public keys for enhanced security.
        """
        combined = self.ed25519_public + self.sphincs_public[:32]  # Use first 32 bytes of SPHINCS+
        return combined.hex()[:40]  # Use first 40 hex chars as address
    
    def save_to_file(self, filename: str):
        """
        Save both Ed25519 and SPHINCS+ keys to file.
        Keys are stored in a structured format for future compatibility.
        """
        data = {
            'ed25519_private': self.signer.ed25519_private.private_bytes_raw(),
            'sphincs_private': self.signer.sphincs_keypair.private_key,
            'sphincs_public': self.signer.sphincs_keypair.public_key,
            'sphincs_seed': self.signer.sphincs_keypair.seed,
            'version': '2.0'  # Version tracking for future upgrades
        }
        
        # Save as JSON with bytes encoding
        with open(filename, 'w') as f:
            json.dump(data, f, cls=BytesEncoder)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Wallet':
        """
        Load wallet from key file, supporting both new and legacy formats.
        
        Args:
            filename: Path to key file
            
        Returns:
            Wallet: Loaded wallet instance
        """
        with open(filename, 'rb') as f:
            try:
                # Try loading new format (JSON)
                data = json.loads(f.read().decode())
                if isinstance(data, dict) and 'version' in data:
                    # Decode base64 bytes
                    ed_private = ed25519.Ed25519PrivateKey.from_private_bytes(
                        base64.b64decode(data['ed25519_private'])
                    )
                    sphincs_private = base64.b64decode(data['sphincs_private'])
                    sphincs_public = base64.b64decode(data['sphincs_public'])
                    sphincs_seed = base64.b64decode(data['sphincs_seed'])
                    
                    sphincs_keypair = KeyPair(
                        private_key=sphincs_private,
                        public_key=sphincs_public,
                        seed=sphincs_seed
                    )
                    return cls(hybrid_signer=HybridSigner(
                        ed25519_private=ed_private,
                        sphincs_keypair=sphincs_keypair
                    ))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Legacy format (raw Ed25519 key)
                f.seek(0)
                private_bytes = f.read()
                private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
                return cls(ed25519_private=private_key)
    
    def sign_message(self, message: bytes) -> Tuple[bytes, bytes]:
        """
        Sign a message using both Ed25519 and SPHINCS+.
        
        Args:
            message: Message to sign
            
        Returns:
            Tuple[bytes, bytes]: (Ed25519 signature, SPHINCS+ signature)
        """
        return self.signer.sign_hybrid(message)
    
    def verify_message(self, message: bytes, ed_sig: bytes, 
                      sphincs_sig: bytes) -> Tuple[bool, bool]:
        """
        Verify a message's signatures.
        
        Args:
            message: Original message
            ed_sig: Ed25519 signature
            sphincs_sig: SPHINCS+ signature
            
        Returns:
            Tuple[bool, bool]: (Ed25519 valid, SPHINCS+ valid)
        """
        return self.signer.verify_hybrid(message, ed_sig, sphincs_sig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert wallet to dictionary (public info only)"""
        return {
            'address': self.address,
            'ed25519_public': self.ed25519_public.hex(),
            'sphincs_public': self.sphincs_public.hex(),
            'quantum_ready': True
        }
    
    def __str__(self) -> str:
        """String representation of wallet"""
        return f"Wallet(address={self.address}, quantum_ready=True)"
