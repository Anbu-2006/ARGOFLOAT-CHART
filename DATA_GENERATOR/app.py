"""
FloatChart - Data Generator Web App
Web-based interface for managing ARGO oceanographic data.
Run this separately from the chat app when you need to download or manage data.

Usage:
    cd DATA_GENERATOR
    python app.py

Opens at: http://localhost:5001
"""

import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_manager import data_manager_bp
from database_utils import load_environment

# Load environment
load_environment()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')
CORS(app)

# Register data manager blueprint
app.register_blueprint(data_manager_bp)


@app.route('/')
def index():
    """Serve the data manager interface."""
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/api/status')
def status():
    """Health check endpoint."""
    from database_utils import get_database_stats
    
    stats = get_database_stats()
    
    return jsonify({
        "status": "running",
        "app": "FloatChart Data Generator",
        "database_connected": stats is not None,
        "total_records": stats["total_records"] if stats else 0
    })


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  FloatChart - Data Generator")
    print("  Web interface for managing ARGO data")
    print("="*50)
    print(f"\n🌐 Opening at: http://localhost:5001")
    print("\n📋 Endpoints:")
    print("   GET  /                     - Data Manager UI")
    print("   GET  /api/status           - App status")
    print("   GET  /api/data-manager/stats    - Database stats")
    print("   GET  /api/data-manager/regions  - Available regions")
    print("   POST /api/data-manager/fetch    - Start data fetch")
    print("   POST /api/data-manager/init-db  - Initialize database")
    print("   POST /api/data-manager/clear    - Clear all data")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
