from flask import Blueprint, request, jsonify, session
from models import (
    create_user, get_user_by_username, check_password_hash,
    get_admin_by_username, create_admin
)
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Simple email validator regex."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Voter registration endpoint."""
    data = request.get_json() or {}
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    
    # Input Validation
    if not username or not password or not full_name or not email:
        return jsonify({"success": False, "message": "All fields are required."}), 400
        
    if len(username) < 3 or len(username) > 30:
        return jsonify({"success": False, "message": "Username must be between 3 and 30 characters."}), 400
        
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400
        
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Please provide a valid email address."}), 400
        
    # Duplicate prevention checks
    try:
        existing_user = get_user_by_username(username)
        if existing_user:
            return jsonify({"success": False, "message": "Username is already taken."}), 409
            
        # Register user
        user_id = create_user(username, password, full_name, email)
        return jsonify({
            "success": True, 
            "message": "Registration successful! You can now login.",
            "user_id": user_id
        }), 201
    except Exception as e:
        # Check if the error is due to email unique constraint
        if "UNIQUE constraint failed: Users.email" in str(e):
            return jsonify({"success": False, "message": "Email is already registered."}), 409
        return jsonify({"success": False, "message": "Database error occurred during registration."}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Unified login endpoint for voter or admin roles."""
    data = request.get_json() or {}
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'voter').strip() # 'voter' or 'admin'
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
        
    try:
        if role == 'admin':
            admin = get_admin_by_username(username)
            if admin and check_password_hash(admin['password_hash'], password):
                session.clear()
                session['user_id'] = admin['id']
                session['username'] = admin['username']
                session['full_name'] = admin['full_name']
                session['role'] = 'admin'
                return jsonify({
                    "success": True,
                    "message": "Admin login successful.",
                    "user": {
                        "username": admin['username'],
                        "full_name": admin['full_name'],
                        "role": "admin"
                    }
                }), 200
            else:
                return jsonify({"success": False, "message": "Invalid admin credentials."}), 401
        
        else: # voter role
            user = get_user_by_username(username)
            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['role'] = 'voter'
                return jsonify({
                    "success": True,
                    "message": "Login successful.",
                    "user": {
                        "username": user['username'],
                        "full_name": user['full_name'],
                        "role": "voter"
                    }
                }), 200
            else:
                return jsonify({"success": False, "message": "Invalid voter credentials."}), 401
                
    except Exception as e:
        return jsonify({"success": False, "message": f"Server login error: {str(e)}"}), 500


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clears user session."""
    session.clear()
    return jsonify({"success": True, "message": "Logout successful."}), 200


@auth_bp.route('/api/auth/session', methods=['GET'])
def get_session():
    """Checks and returns current session details."""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "user_id": session['user_id'],
                "username": session['username'],
                "full_name": session['full_name'],
                "role": session['role']
            }
        }), 200
    return jsonify({"logged_in": False}), 200
