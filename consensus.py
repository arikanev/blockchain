import time
import json
import random
from blockchain import Block

DIFFICULTY_PREFIX = "0000"  # Low difficulty for faster demonstration

class ProofOfWork:
    """
    A simple Proof-of-Work mechanism.
    """

    def mine_block(self, blockchain, miner_address):
        """
        Mines a new block by incrementing nonce until the block's hash
        meets the difficulty requirement.
        """
        last_block = blockchain.get_last_block()
        index = len(blockchain.chain)
        transactions = blockchain.current_transactions.copy()

        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash
        )

        # Very naive coin reward
        reward_transaction = {
            "sender": "NETWORK",
            "recipient": miner_address,
            "amount": 1,
            "signature": None
        }
        block.transactions.append(reward_transaction)

        nonce = 0
        while True:
            block.nonce = nonce
            block_hash = block.compute_hash()
            if block_hash.startswith(DIFFICULTY_PREFIX):
                block.hash = block_hash
                break
            nonce += 1

        # Add block to the chain
        added = blockchain.add_block(block)
        if added:
            # Clear out the transaction pool
            blockchain.clear_transactions()
            return block
        else:
            return None


class TendermintBFT:
    """
    A simplified Tendermint-inspired BFT mechanism.
    """

    def __init__(self, validators=None):
        # In a real system, validators would be public keys
        # For demonstration, let's just store some "validator" addresses
        self.validators = validators if validators else ["valA", "valB", "valC"]
        # A naive approach: each "round" has one proposer
        self.round_robin_index = 0

    def propose_block(self, blockchain):
        """
        The next validator in the round-robin proposes a block containing
        current transactions. We'll pretend there's immediate network communication.
        """
        proposer = self.validators[self.round_robin_index]
        last_block = blockchain.get_last_block()
        index = len(blockchain.chain)
        transactions = blockchain.current_transactions.copy()

        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash,
            nonce=0,  # not relevant for BFT
            signatures=[]
        )
        block.hash = block.compute_hash()
        return block, proposer

    def vote_and_commit_block(self, blockchain, block):
        """
        Each validator "votes" on the proposed block.
        If enough votes (2/3) are collected, we consider the block committed.
        """
        # Let's pretend each validator randomly decides to vote yes for simplicity
        approvals = []
        for val in self.validators:
            if random.random() > 0.1:  # 90% chance to vote yes
                approvals.append(val)

        # If we have 2/3 approvals, the block is committed
        threshold = (2 * len(self.validators)) // 3 + 1
        if len(approvals) >= threshold:
            block.signatures = approvals  # store approvals in block
            # Add block to the chain
            added = blockchain.add_block(block)
            if added:
                blockchain.clear_transactions()
                return block
        return None

    def next_round(self):
        self.round_robin_index = (self.round_robin_index + 1) % len(self.validators)
