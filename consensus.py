import time
import json
import random
import hashlib
from blockchain import Block
from stake import StakeManager
from typing import Tuple

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
        self.MAX_BLOCK_SIZE = 1024 * 1024  # 1MB
        self.MAX_TIMESTAMP_DRIFT = 300  # 5 minutes

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

    def validate_proposal(self, blockchain, block: Block, proposer: str) -> Tuple[bool, str]:
        """
        Validates a block proposal before voting.
        Returns (is_valid, reason).
        """
        # 1. Check block structure
        if block.index != len(blockchain.chain):
            return False, "Invalid block index"
        
        if block.previous_hash != blockchain.get_last_block().hash:
            return False, "Invalid previous block hash"

        # Check timestamp (not in future, not too old)
        current_time = time.time()
        if block.timestamp > current_time + self.MAX_TIMESTAMP_DRIFT:
            return False, "Block timestamp too far in future"
        if block.timestamp < current_time - self.MAX_TIMESTAMP_DRIFT:
            return False, "Block timestamp too old"

        # 2. Check proposer validity
        expected_proposer = self.validators[self.round_robin_index]
        if proposer != expected_proposer:
            return False, f"Invalid proposer. Expected {expected_proposer}, got {proposer}"

        # 3. Check block size
        block_size = len(json.dumps(block.to_dict()).encode())
        if block_size > self.MAX_BLOCK_SIZE:
            return False, "Block size too large"

        # 4. Validate transactions
        seen_txs = set()  # For duplicate detection
        for tx in block.transactions:
            # Skip validation for reward transactions
            if tx.get('sender') == 'NETWORK':
                continue

            # Check for duplicate transactions
            tx_hash = hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            if tx_hash in seen_txs:
                return False, "Duplicate transaction detected"
            seen_txs.add(tx_hash)

            # In a real system, we would also:
            # - Verify transaction signatures
            # - Check sender balances
            # - Verify transaction format
            # - Check for double-spending against chain history

        # 5. Verify block hash
        if block.hash != block.compute_hash():
            return False, "Invalid block hash"

        return True, "Block is valid"

    def simulate_votes(self, blockchain):
        """
        Simulates validators voting on the current proposal.
        Now includes actual validation before voting.
        """
        if not self.current_proposal:
            return None  # No proposal to vote on

        votes = {}
        block = self.current_proposal['block']
        proposer = self.current_proposal['proposer']

        for val in self.validators:
            # Actually validate the block before voting
            is_valid, reason = self.validate_proposal(blockchain, block, proposer)
            
            if is_valid:
                votes[val] = 'yes'
            else:
                votes[val] = 'no'
                print(f"Validator {val} voted NO: {reason}")

        self.current_votes = votes
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

class ProofOfStake:
    """
    A simple Proof of Stake mechanism.
    Validators are selected based on their stake to create new blocks.
    """
    def __init__(self):
        self.stake_manager = StakeManager()
        # For demo, add some initial stakes
        self._add_initial_stakes()

    def _add_initial_stakes(self):
        """Add some demo stakes."""
        initial_stakes = {
            "alice": 100.0,
            "bob": 50.0,
            "charlie": 25.0
        }
        for validator, amount in initial_stakes.items():
            self.stake_manager.add_stake(validator, amount, time.time())

    def get_stakes(self):
        """Get current stakes for all validators."""
        return self.stake_manager.get_all_stakes()

    def add_stake(self, validator: str, amount: float):
        """Add stake for a validator."""
        return self.stake_manager.add_stake(validator, amount, time.time())

    def remove_stake(self, validator: str, amount: float):
        """Remove stake from a validator."""
        return self.stake_manager.remove_stake(validator, amount)

    def create_block(self, blockchain, validator_address: str = None):
        """
        Create a new block using PoS.
        If validator_address is provided, verify they're eligible.
        Otherwise, select a validator based on stake.
        """
        # Get last block hash as seed for deterministic selection
        last_block = blockchain.get_last_block()
        seed = last_block.hash.encode('utf-8')

        # Select validator if not provided
        if not validator_address:
            validator_address, stake = self.stake_manager.select_validator(seed)
            if not validator_address:
                return None, "No eligible validators"
        else:
            # Verify provided validator is eligible
            if not self.stake_manager.is_validator(validator_address):
                return None, f"Address {validator_address} is not an eligible validator"
            stake = self.stake_manager.get_stake(validator_address)

        # Create the new block
        index = len(blockchain.chain)
        transactions = blockchain.current_transactions.copy()

        # Add validator reward (proportional to stake)
        reward = min(1.0, stake / 100.0)  # Max 1.0 reward, scales with stake
        reward_tx = {
            "sender": "NETWORK",
            "recipient": validator_address,
            "amount": reward,
            "signature": None,
            "type": "pos_reward"
        }
        transactions.append(reward_tx)

        # Create and add the block
        new_block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.time(),
            previous_hash=last_block.hash,
            consensus_method="pos"  # Mark as PoS block
        )
        
        # Instead of PoW, we'll use a simple hash
        new_block.hash = new_block.compute_hash()
        
        # Try to add to chain
        added = blockchain.add_block(new_block)
        if added:
            blockchain.clear_transactions()
            return new_block, f"Block created by validator {validator_address} (stake: {stake})"
        
        return None, "Failed to add block to chain"

    def handle_malicious_attempt(self, validator: str) -> Tuple[bool, str]:
        """
        Simulates a validator being caught attempting malice and slashes them.
        Returns (success, message).
        """
        if not self.stake_manager.is_validator(validator):
            return False, f"Address {validator} is not an active validator."
        
        print(f"[PoS Simulation] Simulating malicious attempt by {validator}...")
        # In a real system, proof of malice would be required.
        # Here we just directly slash.
        success, slashed_amount = self.stake_manager.slash_stake(validator)
        
        if success:
            message = f"Malice detected! Slashed {slashed_amount:.2f} stake from {validator}."
            return True, message
        else:
            return False, f"Failed to slash {validator}."
