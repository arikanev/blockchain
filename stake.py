import random
from typing import Dict, List, Tuple, Optional

class StakeManager:
    """
    Manages validator stakes and selection for Proof of Stake.
    """
    def __init__(self):
        # Dictionary of validator_address -> stake amount
        self.stakes: Dict[str, float] = {}
        # Minimum stake required to be a validator
        self.MIN_STAKE = 10.0
        # Track when stakes were locked (for minimum lock period)
        self.stake_timestamps: Dict[str, float] = {}

    def add_stake(self, validator: str, amount: float, timestamp: float) -> bool:
        """Add or increase a validator's stake."""
        if amount <= 0:
            return False
        
        if validator in self.stakes:
            self.stakes[validator] += amount
        else:
            self.stakes[validator] = amount
        
        self.stake_timestamps[validator] = timestamp
        return True

    def remove_stake(self, validator: str, amount: float) -> bool:
        """Remove some or all of a validator's stake."""
        if validator not in self.stakes or amount <= 0:
            return False
        
        if amount > self.stakes[validator]:
            return False  # Can't remove more than staked
        
        self.stakes[validator] -= amount
        if self.stakes[validator] < self.MIN_STAKE:
            # If stake falls below minimum, remove validator completely
            del self.stakes[validator]
            del self.stake_timestamps[validator]
        return True

    def get_stake(self, validator: str) -> float:
        """Get a validator's current stake."""
        return self.stakes.get(validator, 0.0)

    def get_all_stakes(self) -> Dict[str, float]:
        """Get all current stakes."""
        return self.stakes.copy()

    def select_validator(self, seed: Optional[bytes] = None) -> Tuple[str, float]:
        """
        Select a validator weighted by stake.
        Returns (validator_address, stake_amount).
        Uses an optional seed for deterministic selection.
        """
        if not self.stakes:
            return None, 0.0

        # Filter for validators meeting minimum stake
        eligible = {v: s for v, s in self.stakes.items() if s >= self.MIN_STAKE}
        if not eligible:
            return None, 0.0

        # Calculate total stake
        total_stake = sum(eligible.values())

        # Use provided seed or generate random
        if seed:
            random.seed(int.from_bytes(seed, 'big'))
        
        # Select random point in total stake range
        point = random.uniform(0, total_stake)
        
        # Find which validator owns this point
        current = 0
        for validator, stake in eligible.items():
            current += stake
            if point <= current:
                return validator, stake

        # Should never reach here if math is correct
        return None, 0.0

    def get_validators(self) -> List[str]:
        """Get list of current validators (with sufficient stake)."""
        return [v for v, s in self.stakes.items() if s >= self.MIN_STAKE]

    def is_validator(self, address: str) -> bool:
        """Check if an address is a current validator."""
        return address in self.stakes and self.stakes[address] >= self.MIN_STAKE

    def slash_stake(self, validator: str, percentage: float = 0.1) -> Tuple[bool, float]:
        """
        Reduce a validator's stake by a percentage for misbehavior.
        Returns (success, slashed_amount).
        """
        if validator not in self.stakes:
            return False, 0.0
        
        current_stake = self.stakes[validator]
        slashed_amount = current_stake * percentage
        
        self.stakes[validator] -= slashed_amount
        print(f"[PoS Slashing] Slashed {slashed_amount:.2f} from {validator}. New stake: {self.stakes[validator]:.2f}")
        
        # Check if stake falls below minimum after slashing
        if self.stakes[validator] < self.MIN_STAKE:
            print(f"[PoS Slashing] Validator {validator} stake fell below minimum after slashing. Removing validator.")
            del self.stakes[validator]
            del self.stake_timestamps[validator]
            
        return True, slashed_amount 