# QuantumChain

A quantum-resistant blockchain implementation featuring hybrid signatures (Ed25519 + SPHINCS+) for enhanced security and future-proofing against quantum computing threats.

## Features

- **Hybrid Signature System**
  - Ed25519 for current security and efficiency
  - SPHINCS+ for quantum resistance (shake256-128f)
  - Seamless signature verification
  - Support for legacy wallets

- **Transaction System**
  - UTXO-based transaction model
  - Change output calculation
  - Fee handling
  - Coinbase transaction support
  - JSON serialization

- **Merkle Tree Implementation**
  - Efficient proof generation
  - Transaction verification
  - Support for odd number of transactions
  - Duplicate leaf handling

## Project Structure

```
quantumchain/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── block.py           # Block implementation
│   ├── blockchain.py      # Blockchain core logic
│   ├── merkle.py         # Merkle tree implementation
│   ├── quantum_sig.py    # SPHINCS+ and hybrid signatures
│   ├── transaction.py    # Transaction implementation
│   ├── utxo.py          # UTXO set management
│   └── wallet.py        # Wallet implementation
├── tests/                 # Test suite
│   ├── merkle_test.py    # Merkle tree tests
│   ├── quantum_sig_test.py # Signature tests
│   ├── transaction_test.py # Transaction tests
│   ├── utxo_test.py      # UTXO tests
│   └── wallet_test.py    # Wallet tests
├── CONTRIBUTING.md       # Contribution guidelines
├── README.md            # This file
├── ROADMAP.md          # Development roadmap
├── requirements.txt    # Python dependencies
└── demo.py            # Demo application
```

## Dependencies

- Python 3.10+
- pyspx 0.5.0 (SPHINCS+ implementation)
- cryptography (Ed25519 implementation)
- pytest (testing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quantumchain.git
cd quantumchain
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Create a new wallet:
```python
from src.wallet import Wallet

# Generate new wallet with both Ed25519 and SPHINCS+ keys
wallet = Wallet.generate()

# Save wallet to file
wallet.save('my_wallet.json')
```

2. Create and sign a transaction:
```python
from src.transaction import Transaction
from decimal import Decimal

# Create transaction
tx = Transaction(
    sender=wallet.address,
    recipient="recipient_address",
    amount=Decimal('1.0'),
    fee=Decimal('0.001'),
    inputs=[utxo]
)

# Sign with both Ed25519 and SPHINCS+
tx.sign(wallet)
```

3. Verify transaction:
```python
# Verify transaction including signatures and UTXO validity
is_valid = tx.verify(utxo_set, wallet)
```

## Testing

Run the test suite:
```bash
python -m pytest -v
```

## Security

This implementation uses:
- Ed25519 for traditional digital signatures
- SPHINCS+ (shake256-128f) for post-quantum security
- SHA-256 for Merkle tree hashing
- JSON for data serialization

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- SPHINCS+ team for the pyspx implementation
- The quantum computing community for security insights
