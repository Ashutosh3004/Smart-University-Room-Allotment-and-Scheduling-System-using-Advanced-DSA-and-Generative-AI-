# api_server.py (Consolidated Logic and API)

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import random
import string

app = Flask(__name__)
CORS(app) # Enable CORS
# allotment_engine.py

from datetime import datetime, timedelta

# --- UTILITIES ---

def parse_time(date_str, hhmm):
    """Converts YYYY-MM-DD HH:MM to epoch milliseconds."""
    try:
        dt_obj = datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")
        return dt_obj.timestamp() * 1000 
    except ValueError:
        return 0

def times_overlap(a_start, a_end, b_start, b_end):
    """Checks for simple time conflict (gap is not a factor since resources are removed)."""
    if a_end <= b_start or b_end <= a_start:
        return False
    return True

# --- DATASETS (Pre-provided Simulation) ---

# This simulates data read from the database/pre-provided dataset.
# The `rooms` list will be simplified as resources are removed.
ROOMS_DATASET = [
    {"id": "B101", "name": "Classroom B101"},
    {"id": "B102", "name": "Classroom B102"},
    {"id": "B111", "name": "Lab 201"},
    {"id": "A315", "name": "Seminar Hall"}
]

# Schedule list will hold the actual bookings. Start empty for fresh run.
SCHEDULE_DATASET = []

# --- SCHEDULING LOGIC ---

def check_conflict(room_id, start_ts, end_ts):
    """Checks if a room is already booked during the requested time slot."""
    for booking in SCHEDULE_DATASET:
        if booking['room_id'] == room_id:
            if times_overlap(booking['start_ts'], booking['end_ts'], start_ts, end_ts):
                return booking # Conflict found, return the conflicting booking
    return None # No conflict found

def book_new_slot(room_id, user_role, user_name, date, start_time, end_time):
    """
    Attempts to book a new slot.
    Permissions check: Only Admin/Faculty can book directly.
    """
    if user_role not in ['admin', 'faculty']:
        return {"status": "error", "message": "Permission Denied: Only Admin or Faculty can book directly."}

    start_ts = parse_time(date, start_time)
    end_ts = parse_time(date, end_time)

    if start_ts >= end_ts:
        return {"status": "error", "message": "Time Error: Start time must be before end time."}
    
    # Check for conflict
    conflicting_booking = check_conflict(room_id, start_ts, end_ts)
    if conflicting_booking:
        return {
            "status": "conflict", 
            "message": f"Conflict: Room {room_id} is already booked by {conflicting_booking['user_name']} during this time.",
            "conflicting_booking": conflicting_booking
        }
    
    # If no conflict, perform the booking
    new_slot = {
        "id": id_generator('B'),
        "room_id": room_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "user_role": user_role,
        "user_name": user_name
    }
    SCHEDULE_DATASET.append(new_slot)
    return {"status": "success", "message": f"Room {room_id} successfully booked by {user_name}."}

def cancel_slot(booking_id, user_role):
    """
    Cancels a booking.
    Permissions check: Only Admin/Faculty can cancel.
    """
    if user_role not in ['admin', 'faculty']:
        return {"status": "error", "message": "Permission Denied: Only Admin or Faculty can cancel bookings."}
    
    global SCHEDULE_DATASET
    initial_length = len(SCHEDULE_DATASET)
    
    # Remove the booking
    SCHEDULE_DATASET = [b for b in SCHEDULE_DATASET if b['id'] != booking_id]
    
    if len(SCHEDULE_DATASET) < initial_length:
        return {"status": "success", "message": f"Booking {booking_id} cancelled successfully."}
    else:
        return {"status": "error", "message": f"Booking ID {booking_id} not found."}

def submit_request(room_id, user_name, date, start_time, end_time):
    """
    Submits a booking request (read-only action).
    This function primarily serves the Student role.
    """
    # Note: In a full system, this would go into a separate 'Requests' queue,
    # but for simplicity, we just check the conflict and provide a suggestion.
    
    start_ts = parse_time(date, start_time)
    end_ts = parse_time(date, end_time)
    
    if start_ts >= end_ts:
        return {"status": "error", "message": "Time Error: Start time must be before end time."}
    
    conflicting_booking = check_conflict(room_id, start_ts, end_ts)
    
    if conflicting_booking:
        # Conflict found: provide suggestion of vacant rooms
        vacant_rooms = find_vacant_rooms(start_ts, end_ts)
        return {
            "status": "conflict_request", 
            "message": f"Request for {room_id} denied: Conflict with {conflicting_booking['user_name']}.",
            "vacant_suggestions": vacant_rooms,
            "conflicting_booking": conflicting_booking
        }
    else:
        # No conflict: request is successful (but still needs Admin/Faculty approval in a real system)
        return {"status": "success", "message": f"Request for {room_id} submitted successfully. No conflict found."}

def find_vacant_rooms(start_ts, end_ts):
    """Finds all rooms that are vacant during a specific time period."""
    vacant_rooms = []
    for room in ROOMS_DATASET:
        # Check if this room has any conflicts in the schedule
        conflict = check_conflict(room['id'], start_ts, end_ts)
        if conflict is None:
            vacant_rooms.append(room)
    return vacant_rooms


def get_view_schedule(room_id=None):
    """Returns the full schedule, filtered by room_id if provided."""
    schedule = []
    for booking in SCHEDULE_DATASET:
        if room_id is None or booking['room_id'] == room_id:
            schedule.append(booking)
    
    return {"status": "success", "schedule": schedule, "rooms": ROOMS_DATASET}

# Utility for generating simple IDs (must be defined locally or imported)
def id_generator(prefix):
    import random
    import string
    return prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=5))

