from src.blockchain import Blockchain
from src.wallet import Wallet
from src.transaction import Transaction
import time

def main():
    # Initialize blockchain
    blockchain = Blockchain(difficulty=2)  # Lower difficulty for demo
    print("Initialized blockchain with genesis block")

    # Create wallets
    alice = Wallet.generate()
    bob = Wallet.generate()
    charlie = Wallet.generate()
    miner = Wallet.generate()

    # Register wallets with blockchain
    blockchain.register_wallet(alice)
    blockchain.register_wallet(bob)
    blockchain.register_wallet(charlie)
    blockchain.register_wallet(miner)
    print("\nCreated and registered wallets for Alice, Bob, Charlie, and Miner")

    # Mine first block to get initial coins
    print("\nMining first block to get initial coins...")
    blockchain.mine_pending_transactions(miner.address)
    miner_balance = blockchain.get_balance(miner.address)
    print(f"Miner balance: {miner_balance} coins")

    # Miner sends coins to Alice and Bob
    print("\nMiner distributing coins to Alice and Bob...")
    tx1 = Transaction.create_transaction(
        sender_address=miner.address,
        recipient_address=alice.address,
        amount=4.0,  # Reduced amount
        utxo_set=blockchain.utxo_set,
        private_key=miner.private_key,
        fee=0.001
    )
    if tx1:
        blockchain.add_transaction(tx1, miner)
        print("Transaction to Alice created successfully")

    tx2 = Transaction.create_transaction(
        sender_address=miner.address,
        recipient_address=bob.address,
        amount=3.0,  # Reduced amount
        utxo_set=blockchain.utxo_set,
        private_key=miner.private_key,
        fee=0.001
    )
    if tx2:
        blockchain.add_transaction(tx2, miner)
        print("Transaction to Bob created successfully")

    # Mine block with distribution transactions
    print("\nMining block with distribution transactions...")
    blockchain.mine_pending_transactions(miner.address)

    # Show balances after distribution
    print("\nBalances after initial distribution:")
    print(f"Miner: {blockchain.get_balance(miner.address)} coins")
    print(f"Alice: {blockchain.get_balance(alice.address)} coins")
    print(f"Bob: {blockchain.get_balance(bob.address)} coins")
    print(f"Charlie: {blockchain.get_balance(charlie.address)} coins")

    # Demonstrate transactions between users
    print("\nPerforming transactions between users...")
    
    # Alice sends coins to Charlie
    tx3 = Transaction.create_transaction(
        sender_address=alice.address,
        recipient_address=charlie.address,
        amount=1.5,  # Reduced amount
        utxo_set=blockchain.utxo_set,
        private_key=alice.private_key,
        fee=0.002  # Higher fee for faster processing
    )
    if tx3:
        blockchain.add_transaction(tx3, alice)
        print("Transaction from Alice to Charlie created successfully")

    # Bob sends coins to Charlie
    tx4 = Transaction.create_transaction(
        sender_address=bob.address,
        recipient_address=charlie.address,
        amount=1.0,  # Reduced amount
        utxo_set=blockchain.utxo_set,
        private_key=bob.private_key,
        fee=0.001
    )
    if tx4:
        blockchain.add_transaction(tx4, bob)
        print("Transaction from Bob to Charlie created successfully")

    # Mine block with user transactions
    print("\nMining block with user transactions...")
    blockchain.mine_pending_transactions(miner.address)

    # Show final balances
    print("\nFinal balances:")
    print(f"Miner: {blockchain.get_balance(miner.address)} coins")
    print(f"Alice: {blockchain.get_balance(alice.address)} coins")
    print(f"Bob: {blockchain.get_balance(bob.address)} coins")
    print(f"Charlie: {blockchain.get_balance(charlie.address)} coins")

    # Verify blockchain integrity
    print("\nVerifying blockchain integrity...")
    is_valid = blockchain.is_chain_valid()
    print(f"Blockchain is {'valid' if is_valid else 'invalid'}")

    # Try an invalid transaction (insufficient funds)
    print("\nTrying to send more coins than available...")
    invalid_tx = Transaction.create_transaction(
        sender_address=charlie.address,
        recipient_address=alice.address,
        amount=100.0,  # More than Charlie has
        utxo_set=blockchain.utxo_set,
        private_key=charlie.private_key,
        fee=0.001
    )
    if invalid_tx:
        result = blockchain.add_transaction(invalid_tx, charlie)
        print(f"Transaction {'accepted' if result else 'rejected'}")
    else:
        print("Transaction creation failed: Insufficient funds")

if __name__ == "__main__":
    main()
