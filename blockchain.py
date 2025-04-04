import time
import json
import hashlib
import uuid
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import \
    decode_dss_signature, encode_dss_signature

class Transaction:
    """
    A simple transaction object storing the sender, recipient, amount,
    and a digital signature.
    """
    def __init__(self, sender, recipient, amount, signature=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature  # (r, s) in simplified form, or None initially

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'signature': self.signature
        }

    def sign_transaction(self, private_key):
        """
        Sign the transaction using ECDSA. The transaction's stringified version
        is signed to produce a signature (r, s) tuple.
        """
        tx_data = f"{self.sender}{self.recipient}{self.amount}"
        tx_data_bytes = tx_data.encode('utf-8')

        signature = private_key.sign(
            tx_data_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        (r, s) = decode_dss_signature(signature)
        self.signature = (r, s)

    def is_valid(self, public_key):
        """
        Check if the signature is valid given the provided public key.
        """
        if not self.signature:
            return False

        (r, s) = self.signature
        signature_asn1 = encode_dss_signature(r, s)

        tx_data = f"{self.sender}{self.recipient}{self.amount}"
        tx_data_bytes = tx_data.encode('utf-8')

        try:
            public_key.verify(signature_asn1, tx_data_bytes, ec.ECDSA(hashes.SHA256()))
            return True
        except:
            return False


class Block:
    """
    A basic Block structure with:
    - index
    - timestamp
    - transactions
    - previous_hash
    - nonce (used in PoW) or round info (used in BFT)
    - hash (once calculated)
    - signatures (for BFT, if used)
    """
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0, signatures=None):
        self.index = index
        self.transactions = transactions  # list of transaction dicts
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.signatures = signatures if signatures else []  # BFT: list of validator sigs
        self.hash = None

    def compute_hash(self):
        """
        Compute the SHA-256 hash of the block's contents (excluding 'hash').
        """
        block_string = json.dumps({
            'index': self.index,
            'transactions': [tx for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'signatures': self.signatures
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'signatures': self.signatures,
            'hash': self.hash
        }


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0",
            nonce=0,
            signatures=[]
        )
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction):
        """
        Add a transaction to the list of current transactions.
        (Here we assume transactions are validated externally.)
        """
        self.current_transactions.append(transaction.to_dict())

    def add_block(self, block: Block):
        """
        Add a block to the chain after verification.
        """
        # 1. Check that previous_hash matches
        last_block_hash = self.get_last_block().hash
        if block.previous_hash != last_block_hash:
            print("[Error] The block's previous_hash doesn't match the chain's last block.")
            return False

        # 2. Recompute hash to ensure correctness
        block.hash = block.compute_hash()
        if not self.is_valid_block(block):
            print("[Error] Block hash or structure is invalid.")
            return False

        self.chain.append(block)
        return True

    def is_valid_block(self, block: Block):
        """
        Very simplified check for block validity. 
        """
        # Recalculate hash
        recomputed_hash = block.compute_hash()
        return recomputed_hash == block.hash

    def is_valid_chain(self):
        """
        Check the entire chain's validity by verifying hashes and links.
        """
        for i in range(1, len(self.chain)):
            curr_block = self.chain[i]
            prev_block = self.chain[i - 1]

            if curr_block.previous_hash != prev_block.hash:
                return False

            if curr_block.compute_hash() != curr_block.hash:
                return False

        return True

    def clear_transactions(self):
        self.current_transactions = []
