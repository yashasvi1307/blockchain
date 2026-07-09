import json
from datetime import datetime
from block import Block
from models import get_all_blocks, add_block_to_db

class Blockchain:
    def __init__(self):
        """Initializes the blockchain ledger. Loads existing history from the database."""
        self.chain = []
        self.load_from_db()

    def load_from_db(self):
        """Synchronizes the local chain representation with SQLite database records."""
        db_blocks = get_all_blocks()
        self.chain = [Block.from_dict(b) for b in db_blocks]
        # In case the table is empty (e.g. database not seeded), seed genesis block
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Creates and registers the block #0 (Genesis Block)."""
        genesis = Block(
            index=0,
            timestamp="2026-07-07 00:00:00",
            vote_data="Genesis Block - Blockchain Voting System Initialized",
            previous_hash="0"
        )
        add_block_to_db(
            block_index=genesis.index,
            timestamp=genesis.timestamp,
            vote_data=genesis.vote_data,
            previous_hash=genesis.previous_hash,
            block_hash=genesis.hash
        )
        self.chain.append(genesis)

    def get_last_block(self):
        """Returns the latest block in the chain."""
        if not self.chain:
            self.load_from_db()
        return self.chain[-1]

    def add_vote(self, voter_id, election_id, candidate_id):
        """Adds a new vote transaction to the ledger as a separate block.
        
        Args:
            voter_id (int): ID of the voter (anonymized in data).
            election_id (int): Election reference.
            candidate_id (int): Candidate reference.
            
        Returns:
            tuple: (inserted_row_id, new_block_object)
        """
        # Synchronize chain state with database first
        self.load_from_db()
        last_block = self.get_last_block()
        new_index = last_block.index + 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Structure the transaction data securely as a JSON string
        vote_data_dict = {
            "voter_id_hash": hashlib_sha256(str(voter_id)), # Hashing the voter ID to keep voter secret
            "election_id": election_id,
            "candidate_id": candidate_id
        }
        vote_data_str = json.dumps(vote_data_dict, sort_keys=True)
        
        new_block = Block(
            index=new_index,
            timestamp=timestamp,
            vote_data=vote_data_str,
            previous_hash=last_block.hash
        )
        
        # Persist block record in the database
        block_id = add_block_to_db(
            block_index=new_block.index,
            timestamp=new_block.timestamp,
            vote_data=new_block.vote_data,
            previous_hash=new_block.previous_hash,
            block_hash=new_block.hash
        )
        
        self.chain.append(new_block)
        return block_id, new_block

    def is_chain_valid(self):
        """Performs cryptographical integrity checking on the entire chain.
        Detects tampering, invalid parent references, or invalid SHA-256 signatures.
        
        Returns:
            dict: {
                "is_valid": bool,
                "errors": list,
                "report": list of dicts (individual block diagnostic)
            }
        """
        self.load_from_db()
        errors = []
        report = []
        is_valid = True
        
        if not self.chain:
            return {
                "is_valid": False,
                "errors": ["Chain empty."],
                "report": []
            }
            
        # Verify Genesis
        genesis = self.chain[0]
        genesis_ok = True
        if genesis.index != 0:
            genesis_ok = False
            errors.append("Genesis block index is not 0.")
        
        calc_gen_hash = genesis.calculate_hash()
        if genesis.hash != calc_gen_hash:
            genesis_ok = False
            errors.append(f"Genesis block hash altered. Stored: {genesis.hash[:10]}, Calculated: {calc_gen_hash[:10]}")
            
        report.append({
            "index": 0,
            "status": "VALID" if genesis_ok else "TAMPERED",
            "stored_hash": genesis.hash,
            "calculated_hash": calc_gen_hash,
            "previous_hash": genesis.previous_hash,
            "error_msg": None if genesis_ok else "Genesis integrity breached."
        })
        if not genesis_ok:
            is_valid = False
            
        # Verify remaining blocks
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]
            block_errors = []
            
            # Hash verification
            calc_hash = current.calculate_hash()
            if current.hash != calc_hash:
                block_errors.append(f"Calculated hash ({calc_hash[:10]}) does not match stored hash ({current.hash[:10]})")
                
            # Previous Hash linking verification
            if current.previous_hash != prev.hash:
                block_errors.append(f"Previous link broken. Expected: {prev.hash[:10]}, Got: {current.previous_hash[:10]}")
                
            block_ok = len(block_errors) == 0
            if not block_ok:
                is_valid = False
                errors.extend([f"Block #{current.index}: {err}" for err in block_errors])
                
            report.append({
                "index": current.index,
                "status": "VALID" if block_ok else "TAMPERED",
                "stored_hash": current.hash,
                "calculated_hash": calc_hash,
                "previous_hash": current.previous_hash,
                "error_msg": "; ".join(block_errors) if not block_ok else None
            })
            
        return {
            "is_valid": is_valid,
            "errors": errors,
            "report": report
        }

def hashlib_sha256(data_string):
    """Utility helper for quick string hashes."""
    import hashlib
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
