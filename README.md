# Blockchain Voting System

A secure, tamper-evident, internship-level Blockchain Voting System built from scratch using a custom Python blockchain, SQLite, Flask, and a premium HTML/CSS/JS frontend dashboard.

## Features

- **Admin Dashboard**: Create elections, add candidates, view candidates/voters, toggle election status (active/closed), view election results, visualize the blockchain, check chain integrity, export results as PDF, and export blockchain data as JSON.
- **Voter Dashboard**: Self-registration, secure login, vote casting (strictly one vote per person per election), and vote verification.
- **Custom Blockchain Core**: Each vote is recorded as a transaction, packed into blocks, cryptographically linked by hashes (SHA-256), and validated in real time to prevent and detect any tampering.
- **Security Features**: Password hashing (using Werkzeug security), parameterized SQL queries to prevent SQL injection, double-voting prevention, and duplicate registration protection.

## Technology Stack

- **Backend**: Python 3.12, Flask, Flask-CORS
- **Database**: SQLite3
- **Blockchain**: Python implementation using SHA-256 hashing
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+)

---

## Project Structure

```text
blockchain_voting_system/
│
├── app.py                  # Flask Application Factory
├── auth.py                 # Blueprint for Authentication (Register/Login)
├── block.py                # Block Data Class
├── blockchain.py           # Blockchain Ledger Manager
├── database.py             # SQLite Database Connections
├── models.py               # Data Models and Operations
├── routes.py               # Core Web & API Routes
├── setup_database.py       # DB Initialization & Admin Setup Script
├── run.py                  # Local Development Startup Script
├── requirements.txt        # Project Dependencies
│
├── static/
│   ├── css/
│   │   └── style.css       # Unified Modern stylesheet
│   └── js/
│       └── app.js          # Main Frontend interactive scripting
│
└── templates/
    ├── base.html           # Base layout template
    ├── login.html          # Authentication entry page
    ├── register.html       # Voter sign up page
    ├── voter_dashboard.html# Voter cast vote UI
    └── admin_dashboard.html# Admin control panel
```

---

## Installation & Setup

Follow these steps to run the application locally on your machine.

### Prerequisites
- Python 3.12 installed on your system.
- VS Code (or your preferred IDE).

### Steps

1. **Extract/Copy Files**
   Ensure all files are placed in a folder (e.g. `blockchain_voting_system`).

2. **Open Terminal**
   Open your terminal/command prompt and navigate to the project directory:
   ```bash
   cd C:\Users\ys246\.gemini\antigravity\scratch\blockchain_voting_system
   ```

3. **Install Dependencies**
   Run the following command to install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database**
   Run the database setup script. This creates the SQLite tables, inserts the Genesis block, and provisions the default Administrator user:
   ```bash
   python setup_database.py
   ```
   *Note: This creates the SQLite database file `voting_system.db`.*

5. **Start the Application**
   Launch the Flask server using:
   ```bash
   python run.py
   ```

6. **Access the Web Interface**
   Open your web browser and go to:
   ```text
   http://127.0.0.1:5000
   ```

---

## Default Accounts

For manual testing, the following accounts are initialized by default:

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

---

## Screenshots Placeholder
*(Add your system screenshots here when the application is running)*
- **Landing Page**: Dashboard login and registrations.
- **Admin Panel**: Manage candidates, check blockchain state, verify chain integrity.
- **Voter Area**: Transparent, clean election voting page.
