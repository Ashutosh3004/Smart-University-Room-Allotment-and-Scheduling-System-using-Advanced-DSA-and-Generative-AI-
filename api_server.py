# api_server.py (FINAL VERSION WITH RECURRING CLASSES)

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta # ADDED timedelta
import random
import string
import pandas as pd 
import os
import re

# --- GLOBAL DATASETS ---
ROOMS_DATASET = [] 
USER_MASTER_DATA = []
SCHEDULE_DATASET = [] 
REQUESTS_QUEUE = [] 

# --- FLASK SETUP ---
app = Flask(__name__)
CORS(app) 

# --- UTILITIES ---
def id_generator(prefix):
    return prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def parse_time(date_str, hhmm):
    try:
        dt_obj = datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")
        return dt_obj.timestamp() * 1000 
    except ValueError:
        return 0

def times_overlap(a_start, a_end, b_start, b_end):
    if a_end <= b_start or b_end <= a_start:
        return False
    return True

def check_conflict(room_id, start_ts, end_ts):
    for booking in SCHEDULE_DATASET:
        if booking['room_id'] == room_id:
            if times_overlap(booking['start_ts'], booking['end_ts'], start_ts, end_ts):
                return booking
    return None

def find_vacant_rooms(start_ts, end_ts):
    vacant_rooms = []
    for room in ROOMS_DATASET:
        conflict = check_conflict(room['id'], start_ts, end_ts)
        if conflict is None:
            vacant_rooms.append(room)
    return vacant_rooms

def generate_ai_suggestion(failed_room_id, vacant_rooms):
    if vacant_rooms:
        best_alt_room = vacant_rooms[0]
        suggestion_text = f"Suggestion: Move to **{best_alt_room['name']}** ({best_alt_room['id']})."
    else:
        suggestion_text = "No immediate vacant alternative rooms found."
    return suggestion_text

def load_csv_data(filename):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, filename)
        try: df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError: df = pd.read_csv(file_path, encoding='latin-1')
        
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('room_id', 'id')
        if 'name' in df.columns: df = df.rename(columns={'name': 'name'})
        else: df['name'] = df['id'] 
        if 'faculty_name' in df.columns: df = df.rename(columns={'faculty_name': 'user_name'})

        return df.to_dict('records')
    except Exception as e:
        print(f"CSV Error: {e}")
        return [{"id": "B101", "name": "Classroom B101"}]

# --- NEW FUNCTION: GENERATE RECURRING CLASS SCHEDULE ---
def generate_semester_schedule():
    """Pre-fills the schedule with recurring classes for the next 30 days."""
    print("Generating Semester Schedule...")
    
    # Define your Master Timetable here
    # Rooms must match IDs in your CSV
    timetable = [
        {"room": "B101", "start": "09:00", "end": "10:00", "faculty": "Dr. Pankaj ", "role": "faculty"},
        {"room": "B101", "start": "11:00", "end": "13:00", "faculty": "Dr. Kriti ", "role": "faculty"},
        {"room": "B111", "start": "14:00", "end": "16:00", "faculty": "Dr. Megha ", "role": "faculty"},
    ]
    
    start_date = datetime.now()
    # Generate for next 14 days (2 weeks)
    for i in range(10): 
        current_day = start_date + timedelta(days=i)
        
        # 0=Mon, 1=Tue ... 4=Fri. Skip Sat(5)/Sun(6)
        if current_day.weekday() > 4: 
            continue 
            
        date_str = current_day.strftime("%Y-%m-%d")
        
        for class_info in timetable:
            # Create booking object directly
            SCHEDULE_DATASET.append({
                "id": id_generator('CLS'),
                "room_id": class_info["room"],
                "date": date_str,
                "start_time": class_info["start"],
                "end_time": class_info["end"],
                "start_ts": parse_time(date_str, class_info["start"]),
                "end_ts": parse_time(date_str, class_info["end"]),
                "user_role": class_info["role"],
                "user_name": class_info["faculty"]
            })

# --- LOGIC FUNCTIONS ---

def book_new_slot(room_id, user_role, user_name, date, start_time, end_time):
    if user_role not in ['admin', 'faculty']:
        return {"status": "error", "message": "Permission Denied."}
    
    start_ts = parse_time(date, start_time)
    end_ts = parse_time(date, end_time)
    if start_ts >= end_ts: return {"status": "error", "message": "Invalid time range."}
    
    # --- REAL TIME CHECK ---
    current_ts = datetime.now().timestamp() * 1000
    if start_ts < current_ts:
         return {"status": "error", "message": "Invalid Time: Cannot book a past slot."}
    
    if check_conflict(room_id, start_ts, end_ts):
        vacant = find_vacant_rooms(start_ts, end_ts)
        return {"status": "conflict", "message": f"Room {room_id} is busy.", "suggestions": vacant}
    
    SCHEDULE_DATASET.append({
        "id": id_generator('B'), "room_id": room_id, "date": date, 
        "start_time": start_time, "end_time": end_time, "start_ts": start_ts, "end_ts": end_ts,
        "user_role": user_role, "user_name": user_name
    })
    return {"status": "success", "message": f"Booked {room_id}."}

def submit_request(room_id, user_name, date, start_time, end_time, user_role=None):
    start_ts = parse_time(date, start_time)
    end_ts = parse_time(date, end_time)
    if start_ts >= end_ts: return {"status": "error", "message": "Invalid time range."}

    REQUESTS_QUEUE.append({
        "id": id_generator('RQ'), "room_id": room_id, "user_name": user_name, 
        "date": date, "start_time": start_time, "end_time": end_time, "status": "Pending"
    }) 
    
    if check_conflict(room_id, start_ts, end_ts):
        vacant = find_vacant_rooms(start_ts, end_ts)
        return {"status": "conflict_request", "message": f"Request submitted (Room {room_id} busy).", "suggestions": vacant}
    else:
        return {"status": "success", "message": f"Request for {room_id} submitted."}

# --- AI PARSER ---
def parse_ai_prompt(prompt, user_role, user_name):
    action = 'BOOK' if user_role in ['admin', 'faculty'] else 'REQUEST'
    room_id = None
    
    recognized_ids = [r.get('id', '').lower() for r in ROOMS_DATASET if r.get('id')]
    
    prompt_lower = prompt.lower()
    for valid_id in recognized_ids:
        if valid_id in prompt_lower:
            room_id = valid_id.upper()
            break

    if not room_id: return {"status": "error", "message": "AI Error: No Valid Room ID found in prompt."}

    time_matches = re.findall(r'\b(\d{1,2}:\d{2})\b', prompt)
    start_time = time_matches[0] if len(time_matches) >= 1 else '13:00'
    end_time = time_matches[1] if len(time_matches) >= 2 else '14:00'
    date = datetime.now().strftime("%Y-%m-%d") 

    return {"status": "parsed_success", "action": action, "payload": {"room_id": room_id, "user_role": user_role, "user_name": user_name, "date": date, "start_time": start_time, "end_time": end_time}}

# --- ROUTES ---

@app.route("/api/schedule/ai-workflow", methods=["POST"])
def ai_workflow_route():
    data = request.json
    res = parse_ai_prompt(data.get("prompt"), data.get("user_role"), data.get("user_name"))
    if res['status'] != 'parsed_success': return jsonify(res), 400
    
    if res['action'] == 'BOOK': final_res = book_new_slot(**res['payload'])
    else: final_res = submit_request(**res['payload'])
        
    if final_res['status'] in ['conflict', 'conflict_request']:
        final_res['suggestion_text'] = generate_ai_suggestion(res['payload']['room_id'], final_res.get('suggestions', []))
        
    return jsonify(final_res)

@app.route("/api/schedule/view", methods=["GET"])
def view_schedule_route():
    return jsonify({
        "status": "success", 
        "schedule": SCHEDULE_DATASET,
        "rooms": ROOMS_DATASET, 
        "requests": REQUESTS_QUEUE,
        "requests_queue_length": len(REQUESTS_QUEUE)
    })

@app.route("/api/schedule/request/delete", methods=["POST"])
def delete_request_route():
    data = request.json
    req_id = data.get("request_id")
    global REQUESTS_QUEUE
    initial = len(REQUESTS_QUEUE)
    REQUESTS_QUEUE = [r for r in REQUESTS_QUEUE if r['id'] != req_id]
    if len(REQUESTS_QUEUE) < initial: return jsonify({"status": "success", "message": "Deleted."})
    else: return jsonify({"status": "error", "message": "Not found."}), 404

@app.route("/api/schedule/clear", methods=["POST"])
def clear_route():
    global SCHEDULE_DATASET, REQUESTS_QUEUE
    SCHEDULE_DATASET = []
    REQUESTS_QUEUE = []
    # RE-GENERATE SCHEDULE AFTER CLEARING? 
    # Uncomment the next line if you want 'Clear' to reset to the Semester Plan instead of Empty
    # generate_semester_schedule() 
    return jsonify({"status": "success"})

# --- NEW ROUTE: USER AUTHENTICATION ---
@app.route("/api/login", methods=["POST"])
def login_route():
    data = request.json
    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()
    role_request = data.get("role", "").lower()

    user_found = None
    for user in USER_MASTER_DATA:
        if user.get('user_name', '').lower() == user_id.lower():
            user_found = user
            break
    
    if not user_found:
        if role_request == 'student': return jsonify({"status": "success", "message": "Student Login Verified."})
        return jsonify({"status": "error", "message": "User ID not found."}), 401

    csv_role = user_found.get('role', '').lower()
    if role_request == 'admin' and csv_role != 'admin': return jsonify({"status": "error", "message": "Access Denied: Not an Admin."}), 403
    
    if password != "12345": return jsonify({"status": "error", "message": "Invalid Password."}), 401

    return jsonify({"status": "success", "message": f"Welcome, {user_found.get('user_name')}!"})

# --- STARTUP ---
# --- STARTUP ---
if __name__ == "__main__":
    # 1. Load datasets FIRST
    ROOMS_DATASET = load_csv_data('rooms_master.csv')
    USER_MASTER_DATA = load_csv_data('user_master.csv')
    
    print(f"Loaded {len(ROOMS_DATASET)} rooms and {len(USER_MASTER_DATA)} users.")
    
    # 2. Generate the schedule ONLY if data loaded successfully
    if ROOMS_DATASET and USER_MASTER_DATA:
        generate_semester_schedule()
        print(f"Pre-filled schedule with {len(SCHEDULE_DATASET)} classes.")
    else:
        print("WARNING: Could not generate schedule. Check CSV files.")

    # 3. Run the app
    app.run(debug=False, port=5000)
