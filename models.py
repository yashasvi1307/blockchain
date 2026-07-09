from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query, execute_read_query, execute_read_one

# ==========================================
# USER MODELS (Voters)
# ==========================================

def create_user(username, password, full_name, email):
    """Creates a new voter in the Users table."""
    hashed_password = generate_password_hash(password)
    query = """
        INSERT INTO Users (username, password_hash, full_name, email)
        VALUES (?, ?, ?, ?)
    """
    return execute_query(query, (username, hashed_password, full_name, email))

def get_user_by_username(username):
    """Retrieves a voter by username."""
    query = "SELECT * FROM Users WHERE username = ?"
    return execute_read_one(query, (username,))

def get_user_by_id(user_id):
    """Retrieves a voter by ID."""
    query = "SELECT * FROM Users WHERE id = ?"
    return execute_read_one(query, (user_id,))

def get_all_voters():
    """Retrieves list of all voters."""
    query = "SELECT id, username, full_name, email, created_at FROM Users"
    return execute_read_query(query)


# ==========================================
# ADMIN MODELS
# ==========================================

def create_admin(username, password, full_name):
    """Creates a new admin user."""
    hashed_password = generate_password_hash(password)
    query = """
        INSERT INTO Admin (username, password_hash, full_name)
        VALUES (?, ?, ?)
    """
    return execute_query(query, (username, hashed_password, full_name))

def get_admin_by_username(username):
    """Retrieves an admin by username."""
    query = "SELECT * FROM Admin WHERE username = ?"
    return execute_read_one(query, (username,))


# ==========================================
# ELECTION MODELS
# ==========================================

def create_election(title, description):
    """Creates a new election. Active status by default is 'active'."""
    query = """
        INSERT INTO Election (title, description, status)
        VALUES (?, ?, 'active')
    """
    return execute_query(query, (title, description))

def get_all_elections():
    """Retrieves all elections."""
    query = "SELECT * FROM Election ORDER BY id DESC"
    return execute_read_query(query)

def get_active_elections():
    """Retrieves only active elections."""
    query = "SELECT * FROM Election WHERE status = 'active' ORDER BY id DESC"
    return execute_read_query(query)

def get_election_by_id(election_id):
    """Retrieves detailed election by ID."""
    query = "SELECT * FROM Election WHERE id = ?"
    return execute_read_one(query, (election_id,))

def close_election(election_id):
    """Closes an election by setting status to 'closed'."""
    query = "UPDATE Election SET status = 'closed' WHERE id = ?"
    return execute_query(query, (election_id,))


# ==========================================
# CANDIDATE MODELS
# ==========================================

def add_candidate(election_id, name, party, details=""):
    """Adds a candidate to an election."""
    query = """
        INSERT INTO Candidates (election_id, name, party, details)
        VALUES (?, ?, ?, ?)
    """
    return execute_query(query, (election_id, name, party, details))

def get_candidates_by_election(election_id):
    """Retrieves all candidates registered under a specific election."""
    query = "SELECT * FROM Candidates WHERE election_id = ?"
    return execute_read_query(query, (election_id,))

def get_candidate_by_id(candidate_id):
    """Retrieves candidate details by ID."""
    query = "SELECT * FROM Candidates WHERE id = ?"
    return execute_read_one(query, (candidate_id,))


# ==========================================
# VOTE & TAMPER MODELS
# ==========================================

def has_user_voted(user_id, election_id):
    """Checks if a user has already voted in an election."""
    query = "SELECT 1 FROM Votes WHERE user_id = ? AND election_id = ?"
    result = execute_read_one(query, (user_id, election_id))
    return result is not None

def record_vote(user_id, election_id, candidate_id, block_id=None):
    """Inserts a record indicating user voted. Points to blockchain block ID if mined."""
    query = """
        INSERT INTO Votes (user_id, election_id, candidate_id, block_id)
        VALUES (?, ?, ?, ?)
    """
    return execute_query(query, (user_id, election_id, candidate_id, block_id))

def get_vote_results(election_id):
    """Aggregates vote counts for candidates in an election."""
    query = """
        SELECT c.id as candidate_id, c.name, c.party, COUNT(v.id) as vote_count
        FROM Candidates c
        LEFT JOIN Votes v ON c.id = v.candidate_id
        WHERE c.election_id = ?
        GROUP BY c.id
        ORDER BY vote_count DESC
    """
    return execute_read_query(query, (election_id,))

def get_all_votes_with_details():
    """Gets all casted votes details (anonymous transaction tracking list)."""
    query = """
        SELECT v.id, e.title as election_title, c.name as candidate_name, v.timestamp, v.block_id
        FROM Votes v
        JOIN Election e ON v.election_id = e.id
        JOIN Candidates c ON v.candidate_id = c.id
        ORDER BY v.timestamp DESC
    """
    return execute_read_query(query)


# ==========================================
# BLOCKCHAIN STORAGE MODELS
# ==========================================

def add_block_to_db(block_index, timestamp, vote_data, previous_hash, block_hash):
    """Inserts a new block to the database chain."""
    query = """
        INSERT INTO Blockchain (block_index, timestamp, vote_data, previous_hash, hash)
        VALUES (?, ?, ?, ?, ?)
    """
    return execute_query(query, (block_index, timestamp, vote_data, previous_hash, block_hash))

def get_all_blocks():
    """Retrieves all blocks stored in the database."""
    query = "SELECT * FROM Blockchain ORDER BY block_index ASC"
    return execute_read_query(query)

def get_last_block_from_db():
    """Gets the block with the highest index from the database."""
    query = "SELECT * FROM Blockchain ORDER BY block_index DESC LIMIT 1"
    return execute_read_one(query)

def clear_blockchain_db():
    """Clears all blocks from the DB (for clean testing reinitializations)."""
    query = "DELETE FROM Blockchain"
    execute_query(query)
