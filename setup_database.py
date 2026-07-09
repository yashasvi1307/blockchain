import sqlite3
import os
import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash
from database import DATABASE_PATH

def create_tables():
    """Creates the database tables for the Blockchain Voting System."""
    print(f"Initializing database at: {DATABASE_PATH}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Admin Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL
    );
    """)
    
    # 3. Election Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Election (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT CHECK( status IN ('active', 'closed') ) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 4. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        election_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        party TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY (election_id) REFERENCES Election(id) ON DELETE CASCADE
    );
    """)
    
    # 5. Blockchain Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Blockchain (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_index INTEGER UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        vote_data TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        hash TEXT NOT NULL
    );
    """)
    
    # 6. Votes Table (with unique index on user_id + election_id to prevent double voting)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        election_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        block_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (election_id) REFERENCES Election(id),
        FOREIGN KEY (candidate_id) REFERENCES Candidates(id),
        FOREIGN KEY (block_id) REFERENCES Blockchain(id),
        UNIQUE(user_id, election_id)
    );
    """)
    
    # Seed default Admin
    cursor.execute("SELECT * FROM Admin WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_password = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO Admin (username, password_hash, full_name)
            VALUES ('admin', ?, 'System Administrator')
        """, (hashed_password,))
        print("Default admin created (username: 'admin', password: 'admin123')")
    
    # Seed Genesis Block
    cursor.execute("SELECT * FROM Blockchain WHERE block_index = 0")
    if not cursor.fetchone():
        genesis_index = 0
        genesis_timestamp = "2026-07-07 00:00:00"
        genesis_data = "Genesis Block - Blockchain Voting System Initialized"
        genesis_prev_hash = "0"
        
        # Calculate Hash
        block_contents = f"{genesis_index}{genesis_timestamp}{genesis_data}{genesis_prev_hash}".encode('utf-8')
        genesis_hash = hashlib.sha256(block_contents).hexdigest()
        
        cursor.execute("""
            INSERT INTO Blockchain (block_index, timestamp, vote_data, previous_hash, hash)
            VALUES (?, ?, ?, ?, ?)
        """, (genesis_index, genesis_timestamp, genesis_data, genesis_prev_hash, genesis_hash))
        print("Genesis Block created successfully!")
        
    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    create_tables()
