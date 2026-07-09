import os
from app import create_app
from setup_database import create_tables
from database import DATABASE_PATH

app = create_app()

if __name__ == "__main__":
    # Check if the SQLite database file exists. If not, initialize it automatically.
    if not os.path.exists(DATABASE_PATH):
        print("SQLite Database not found. Automatically setting up schemas...")
        try:
            create_tables()
        except Exception as e:
            print(f"Error during automatic database initialization: {e}")
            
    print("------------------------------------------------------------")
    print("Starting Blockchain Voting System Local Server...")
    print("Access the web UI at: http://127.0.0.1:5000")
    print("------------------------------------------------------------")
    
    # Run the Flask development server
    app.run(debug=True, host="127.0.0.1", port=5000)
