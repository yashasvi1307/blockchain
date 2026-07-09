import hashlib
import json

class Block:
    def __init__(self, index, timestamp, vote_data, previous_hash, block_hash=None):
        """Initializes a Block instance.
        
        Args:
            index (int): Position of the block in the chain.
            timestamp (str): ISO formatted time string.
            vote_data (str/dict): Information of the vote cast.
            previous_hash (str): The hash of the block preceding this one.
            block_hash (str, optional): The block's pre-computed hash. Computed if None.
        """
        self.index = index
        self.timestamp = timestamp
        self.vote_data = vote_data
        self.previous_hash = previous_hash
        self.hash = block_hash or self.calculate_hash()

    def calculate_hash(self):
        """Computes the SHA-256 cryptographic hash of the block."""
        data_str = self.vote_data if isinstance(self.vote_data, str) else json.dumps(self.vote_data, sort_keys=True)
        block_string = f"{self.index}{self.timestamp}{data_str}{self.previous_hash}".encode('utf-8')
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        """Converts the block instance into a dictionary format."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'vote_data': self.vote_data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, data):
        """Constructs a Block instance from a dictionary representation."""
        # Support both sqlite column naming ('block_index') and standard ('index')
        idx = data.get('block_index') if data.get('block_index') is not None else data.get('index')
        return cls(
            index=int(idx),
            timestamp=str(data['timestamp']),
            vote_data=data['vote_data'],
            previous_hash=str(data['previous_hash']),
            block_hash=str(data['hash'])
        )

    def __repr__(self):
        return f"<Block #{self.index} - Hash: {self.hash[:8]}...>"
