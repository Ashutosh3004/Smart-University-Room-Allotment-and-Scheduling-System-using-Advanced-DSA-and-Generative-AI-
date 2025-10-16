# api_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
# Import the core logic function
from allotment_engine import run_smart_allotment 

# Note: Your seating logic is now in allotment_engine.py as well
# from allotment_engine import SmartUniversitySystem 

app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# system = SmartUniversitySystem() # Only needed if you use the seating logic routes

@app.route("/api/run-allotment", methods=["POST"])
def run_allotment_route():
    """Route to handle the main Smart Room Allotment Algorithm."""
    try:
        data = request.get_json()
        
        if not data or 'rooms' not in data or 'requests' not in data:
            return jsonify({"status": "error", "message": "Invalid payload format. Missing rooms or requests."}), 400
        
        # Run the core logic using the data from the JavaScript frontend
        results = run_smart_allotment(data)
        
        return jsonify({
            "status": "success",
            "assignments": results.get('assignments', []),
            "unassigned": results.get('unassigned', [])
        })

    except Exception as e:
        print(f"Error during smart allotment: {e}")
        return jsonify({"status": "error", "message": f"Server processing error: {str(e)}"}), 500

# --- Routes for your original seat-booking logic (if needed in your final app) ---
# NOTE: These routes would need the SmartUniversitySystem instance setup.
# @app.route("/book_room", methods=["POST"])
# def book_room_route():
#    # ... implementation for book_room ...
#    pass 

if __name__ == "__main__":
    app.run(debug=True, port=5000) # Run on port 5000