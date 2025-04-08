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
            previous_hash=last_block.hash,
            consensus_method="pow"
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
    Simulates proposal, voting, and commit phases.
    """

    def __init__(self, validators=None):
        # In a real system, validators would be public keys
        # For demonstration, let's just store some "validator" addresses
        self.validators = validators if validators else ["valA", "valB", "valC"]
        # A naive approach: each "round" has one proposer
        self.round_robin_index = 0
        # Temporary storage for demo purposes (Not suitable for real apps)
        self.current_proposal = None
        self.current_votes = None

    def propose_block(self, blockchain):
        """
        Proposes a block but does not commit it yet.
        Stores the proposal internally for the voting step.
        """
        proposer = self.validators[self.round_robin_index]
        last_block = blockchain.get_last_block()
        index = len(blockchain.chain)
        transactions = blockchain.current_transactions.copy()

        proposed_block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash,
            nonce=0,
            signatures=[],
            consensus_method="bft"
        )
        # Calculate hash now, it's needed for voting reference
        proposed_block.hash = proposed_block.compute_hash()

        # Store proposal for subsequent steps (demo only)
        self.current_proposal = {
            'block': proposed_block,
            'proposer': proposer
        }
        self.current_votes = None # Clear previous votes

        return self.current_proposal # Return the proposal details

    def simulate_votes(self):
        """
        Simulates validators voting on the current proposal.
        Requires propose_block to have been called first.
        Returns a dictionary of votes: {validator: 'yes'/'no'}.
        """
        if not self.current_proposal:
            return None # No proposal to vote on

        votes = {}
        for val in self.validators:
            # Simulate voting logic (e.g., random chance)
            # Could be modified later to simulate faults
            if random.random() > 0.1: # 90% chance to vote yes
                votes[val] = 'yes'
            else:
                votes[val] = 'no'

        self.current_votes = votes # Store votes (demo only)
        return self.current_votes

    def commit_block(self, blockchain):
        """
        Checks the votes for the current proposal and commits the block
        to the blockchain if the threshold is met.
        Requires propose_block and simulate_votes to have been called.
        """
        if not self.current_proposal or not self.current_votes:
            print("[Error] Cannot commit: Proposal or votes missing.")
            return None, "Commit failed: Missing proposal or votes."

        approvals = [val for val, vote in self.current_votes.items() if vote == 'yes']
        threshold = (2 * len(self.validators)) // 3 + 1

        if len(approvals) >= threshold:
            block_to_commit = self.current_proposal['block']
            block_to_commit.signatures = approvals # Store who approved

            # Add block to the actual chain
            added = blockchain.add_block(block_to_commit)
            if added:
                blockchain.clear_transactions()
                proposer = self.current_proposal['proposer']
                message = f"Consensus reached! Block {block_to_commit.index} committed by {proposer}."
                result_block = block_to_commit
            else:
                # This case shouldn't ideally happen if propose was based on latest chain state
                message = "Commit failed: Blockchain rejected the block."
                result_block = None
        else:
            message = f"Consensus failed: Only {len(approvals)}/{len(self.validators)} votes received (threshold {threshold})."
            result_block = None

        # Clear state for next round and advance proposer
        self.current_proposal = None
        self.current_votes = None
        self.next_round()

        return result_block, message

    def get_validators(self):
        """ Simple helper to get validator list """
        return self.validators

    def next_round(self):
        self.round_robin_index = (self.round_robin_index + 1) % len(self.validators)
