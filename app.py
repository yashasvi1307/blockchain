from flask import Flask
from flask_cors import CORS
import os

def create_app():
    """Flask Application Factory."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Enable CORS for APIs
    CORS(app)
    
    # Configure session secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secure-blockchain-voting-secret-key-123987')
    
    # Register Authentication blueprint
    from auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Register Core views and REST APIs blueprint
    from routes import routes_bp
    app.register_blueprint(routes_bp)
    
    return app
