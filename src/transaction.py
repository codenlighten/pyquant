"""
Transaction implementation with hybrid signature support.
"""

from decimal import Decimal
from typing import List, Dict, Optional
import json
import hashlib
from .wallet import Wallet
from .utxo import UTXO

class TransactionOutput:
    """Represents a transaction output."""
    
    def __init__(self, address: str, amount: Decimal):
        """
        Initialize a transaction output.
        
        Args:
            address: Recipient's address
            amount: Amount of coins
        """
        self.address = address
        self.amount = amount
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'address': self.address,
            'amount': str(self.amount)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TransactionOutput':
        """Create from dictionary."""
        return cls(
            address=data['address'],
            amount=Decimal(data['amount'])
        )

class Transaction:
    """
    Represents a transaction in the blockchain.
    Supports both Ed25519 and SPHINCS+ signatures.
    """
    
    def __init__(
        self,
        sender: Optional[str],
        recipient: str,
        amount: Decimal,
        fee: Decimal,
        inputs: List[UTXO]
    ):
        """
        Initialize a new transaction.
        
        Args:
            sender: Sender's address (None for coinbase)
            recipient: Recipient's address
            amount: Amount to send
            fee: Transaction fee
            inputs: List of input UTXOs
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.fee = fee
        self.inputs = inputs
        
        # Calculate change and create outputs
        self.outputs = self._create_outputs()
        
        # Generate transaction ID
        self.txid = self._calculate_txid()
        
        # Initialize signatures as None
        self.ed25519_signature = None
        self.sphincs_signature = None
    
    def _create_outputs(self) -> List[TransactionOutput]:
        """Create transaction outputs including change."""
        outputs = [
            TransactionOutput(self.recipient, self.amount)
        ]
        
        # Calculate change if not coinbase
        if self.sender:
            input_sum = sum(utxo.amount for utxo in self.inputs)
            change = input_sum - self.amount - self.fee
            if change > 0:
                outputs.append(
                    TransactionOutput(self.sender, change)
                )
        
        return outputs
    
    def _calculate_txid(self) -> str:
        """Calculate unique transaction ID."""
        tx_data = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': str(self.amount),
            'fee': str(self.fee),
            'inputs': [
                {
                    'txid': utxo.txid,
                    'address': utxo.address,
                    'amount': str(utxo.amount)
                }
                for utxo in self.inputs
            ],
            'outputs': [out.to_dict() for out in self.outputs]
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def sign(self, wallet: Wallet) -> None:
        """
        Sign transaction with both Ed25519 and SPHINCS+ keys.
        
        Args:
            wallet: Sender's wallet containing both key types
        """
        if not self.sender:  # Don't sign coinbase transactions
            return
        
        # Prepare message to sign (txid)
        message = self.txid.encode()
        
        # Sign with both key types
        self.ed25519_signature, self.sphincs_signature = wallet.signer.sign_hybrid(message)
    
    def verify(self, utxo_set, wallet: Wallet) -> bool:
        """
        Verify transaction validity including signatures.
        
        Args:
            utxo_set: Current UTXO set for input verification
            wallet: Sender's wallet for signature verification
            
        Returns:
            bool: True if transaction is valid
        """
        # Coinbase transactions are always valid
        if not self.sender:
            return True
        
        # Verify input UTXOs exist and are unspent
        input_sum = Decimal('0')
        for utxo in self.inputs:
            stored_utxo = utxo_set.get_utxo(utxo.txid)
            if not stored_utxo or stored_utxo.spent:
                return False
            input_sum += utxo.amount
        
        # Verify amount and fee
        if input_sum < (self.amount + self.fee):
            return False
        
        # Verify change calculation
        change = input_sum - self.amount - self.fee
        if change > 0:
            change_output = next(
                (out for out in self.outputs 
                 if out.address == self.sender),
                None
            )
            if not change_output or change_output.amount != change:
                return False
        
        # Verify signatures
        if not (self.ed25519_signature and self.sphincs_signature):
            return False
        
        # Get sender's public keys from first input UTXO
        # In a real implementation, we would get this from a PKI
        sender_utxo = self.inputs[0]
        if sender_utxo.address != self.sender:
            return False
        
        # Verify both signatures
        message = self.txid.encode()
        ed_valid, sphincs_valid = wallet.signer.verify_hybrid(
            message,
            self.ed25519_signature,
            self.sphincs_signature
        )
        
        return ed_valid and sphincs_valid
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary."""
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': str(self.amount),
            'fee': str(self.fee),
            'inputs': [
                {
                    'txid': utxo.txid,
                    'address': utxo.address,
                    'amount': str(utxo.amount)
                }
                for utxo in self.inputs
            ],
            'outputs': [out.to_dict() for out in self.outputs],
            'txid': self.txid,
            'ed25519_signature': self.ed25519_signature.hex() if self.ed25519_signature else None,
            'sphincs_signature': self.sphincs_signature.hex() if self.sphincs_signature else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary."""
        # Create transaction
        tx = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=Decimal(data['amount']),
            fee=Decimal(data['fee']),
            inputs=[
                UTXO(
                    address=inp['address'],
                    amount=Decimal(inp['amount']),
                    txid=inp['txid']
                )
                for inp in data['inputs']
            ]
        )
        
        # Set signatures
        if data['ed25519_signature']:
            tx.ed25519_signature = bytes.fromhex(data['ed25519_signature'])
        if data['sphincs_signature']:
            tx.sphincs_signature = bytes.fromhex(data['sphincs_signature'])
        
        return tx
