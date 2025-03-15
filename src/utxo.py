"""
UTXO (Unspent Transaction Output) implementation.
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List

class UTXO:
    """
    Represents an Unspent Transaction Output.
    Tracks ownership and amount of coins.
    """
    
    def __init__(self, address: str, amount: Decimal, txid: Optional[str] = None):
        """
        Initialize a new UTXO.
        
        Args:
            address: Owner's address
            amount: Amount of coins
            txid: Transaction ID this UTXO belongs to
        """
        self.address = address
        self.amount = Decimal(str(amount))
        self.txid = txid
        self.spent = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UTXO to dictionary."""
        return {
            'address': self.address,
            'amount': str(self.amount),
            'txid': self.txid,
            'spent': self.spent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UTXO':
        """Create UTXO from dictionary."""
        utxo = cls(
            address=data['address'],
            amount=Decimal(data['amount']),
            txid=data['txid']
        )
        utxo.spent = data['spent']
        return utxo
    
    def __str__(self) -> str:
        """String representation of UTXO."""
        return (
            f"UTXO(address={self.address}, "
            f"amount={self.amount}, "
            f"txid={self.txid}, "
            f"spent={self.spent})"
        )

class UTXOSet:
    """
    Manages the set of all UTXOs in the blockchain.
    Provides methods for querying and updating UTXOs.
    """
    
    def __init__(self):
        """Initialize an empty UTXO set."""
        self.utxos: Dict[str, UTXO] = {}
    
    def add_utxo(self, utxo: UTXO) -> None:
        """Add a UTXO to the set."""
        if utxo.txid:
            self.utxos[utxo.txid] = utxo
    
    def remove_utxo(self, txid: str) -> None:
        """Remove a UTXO from the set."""
        if txid in self.utxos:
            del self.utxos[txid]
    
    def get_utxo(self, txid: str) -> Optional[UTXO]:
        """Get a UTXO by its transaction ID."""
        return self.utxos.get(txid)
    
    def get_utxos_for_address(self, address: str) -> List[UTXO]:
        """Get all unspent UTXOs for a specific address."""
        return [
            utxo for utxo in self.utxos.values()
            if utxo.address == address and not utxo.spent
        ]
    
    def get_balance(self, address: str) -> Decimal:
        """Calculate total unspent balance for an address."""
        return sum(
            (utxo.amount for utxo in self.get_utxos_for_address(address)),
            Decimal('0')
        )
    
    def mark_as_spent(self, txid: str) -> None:
        """Mark a UTXO as spent."""
        if txid in self.utxos:
            self.utxos[txid].spent = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UTXO set to dictionary."""
        return {
            txid: utxo.to_dict()
            for txid, utxo in self.utxos.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UTXOSet':
        """Create UTXO set from dictionary."""
        utxo_set = cls()
        for txid, utxo_data in data.items():
            utxo = UTXO.from_dict(utxo_data)
            utxo_set.utxos[txid] = utxo
        return utxo_set
