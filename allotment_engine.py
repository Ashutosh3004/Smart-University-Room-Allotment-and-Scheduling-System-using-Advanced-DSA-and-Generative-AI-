# allotment_engine.py

from datetime import datetime, timedelta

# Utility: parse time for comparison (converts HH:MM to minutes since midnight)
def parse_time(date_str, hhmm):
    try:
        dt_obj = datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")
        return dt_obj.timestamp() * 1000 # Return milliseconds since epoch
    except ValueError:
        return 0 # Handle bad date/time input

# Utility: check time overlap
def times_overlap(a_start, a_end, b_start, b_end, min_gap_minutes=0):
    gap_ms = min_gap_minutes * 60 * 1000
    # If A ends before B starts OR B ends before A starts (with gap), no overlap.
    if a_end + gap_ms <= b_start:
        return False
    if b_end + gap_ms <= a_start:
        return False
    return True

# --- CORE SMART ALLOTMENT ALGORITHM (Ported from JavaScript) ---
def run_smart_allotment(payload):
    rooms = payload.get('rooms', [])
    requests = payload.get('requests', [])
    constraints = payload.get('constraints', {})
    
    min_gap = constraints.get('minGap', 0)
    allow_over = constraints.get('allowOver', 'false') == 'true'
    weights = constraints.get('weights', {})

    assignments = []
    unassigned = []
    schedule_by_room = {r['id']: [] for r in rooms}

    # 1. Score and sort requests (Priority > Duration > Attendees)
    reqs_scored = []
    for r in requests:
        start_ts = parse_time(r['date'], r['start'])
        end_ts = parse_time(r['date'], r['end'])
        
        # Calculate duration in minutes
        duration = (end_ts - start_ts) / 60000 if end_ts > start_ts else 0
        
        r['duration'] = duration
        r['score'] = weights.get(r['userType'], 50)
        r['start_ts'] = start_ts
        r['end_ts'] = end_ts
        reqs_scored.append(r)
        
    reqs_scored.sort(key=lambda r: (-r['score'], r['duration'], -r['attendees']))

    # 2. Process requests in prioritized order
    for req in reqs_scored:
        allocation_reason = ''
        
        # Candidate rooms filter (match constraints)
        candidates = []
        for r in rooms:
            # Type match
            if req.get('prefType') and r['type'] != req['prefType']:
                allocation_reason = 'Type mismatch'
                continue
            
            # Gender constraints (for hostel rooms)
            if r['type'] == 'hostel' and req['gender'] != 'any' and r['gender'] != 'any' and r['gender'] != req['gender']:
                allocation_reason = 'Gender mismatch (Hostel)'
                continue
                
            # Resource tags
            need_tags = [s.strip().lower() for s in req.get('need', '').split(',') if s.strip()]
            room_tags_lower = [x.lower() for x in r.get('tags', [])]
            if need_tags and not all(nt in room_tags_lower for nt in need_tags):
                allocation_reason = 'Missing required resource tags'
                continue
                
            # Capacity rule
            if not allow_over and r['capacity'] < req['attendees']:
                allocation_reason = 'Capacity too small (Strict)'
                continue
                
            candidates.append(r)

        # Sort candidates by capacity ascending (Smallest fitting room first)
        candidates.sort(key=lambda r: r['capacity'])

        # Find room that is free (no overlap)
        allocated_room = None
        time_conflict_found = False
        
        for cand in candidates:
            sch = schedule_by_room.get(cand['id'], [])
            
            # Check for conflict with existing bookings
            conflict = any(times_overlap(s['start_ts'], s['end_ts'], req['start_ts'], req['end_ts'], min_gap) for s in sch)
            
            if not conflict:
                allocated_room = cand
                # Reserve room
                schedule_by_room[cand['id']].append({
                    'start_ts': req['start_ts'], 
                    'end_ts': req['end_ts'], 
                    'reqId': req['id']
                })
                break
            else:
                time_conflict_found = True

        # Final Assignment or Failure Handling
        if allocated_room:
            assignments.append({'reqId': req['id'], 'roomId': allocated_room['id']})
        else:
            final_reason = allocation_reason
            if time_conflict_found and not final_reason:
                final_reason = 'Time conflict or minimum gap violation.'
            elif not candidates:
                final_reason = 'No rooms defined or no room matched all resource/type/capacity criteria.'
            
            unassigned.append({'reqId': req['id'], 'reason': final_reason or 'Failed to match any room.'})

    return {
        'assignments': assignments,
        'unassigned': unassigned
    }

# This is the logic from your app.py file, which is separate from the Smart Allotment:
class Room:
    # ... (Your existing Room class content) ...
    def __init__(self, room_number, host, start_time, end_time, from_date, to_date):
        self.room_number = room_number
        self.host = host
        self.start_time = start_time
        self.end_time = end_time
        self.from_date = from_date
        self.to_date = to_date
        self.capacity = 40
        self.seats = [["Empty" for _ in range(4)] for _ in range(10)]

    def display_seats(self):
        serial = 1
        empty_count = 0
        seat_data = []
        for i in range(10):
            row_data = []
            for j in range(4):
                seat_status = f"{serial}. {self.seats[i][j]}"
                row_data.append(seat_status)
                if self.seats[i][j] == "Empty":
                    empty_count += 1
                serial += 1
            seat_data.append(row_data)
        return {"seats": row_data, "empty_count": empty_count}


class SmartUniversitySystem:
    # ... (Your existing SmartUniversitySystem class content) ...
    def __init__(self):
        self.rooms = []

    def book_room(self, room_number, host, start_time, end_time, from_date, to_date):
        for r in self.rooms:
            if r.room_number == room_number:
                return {"status": "error", "message": f"Room {room_number} already exists!"}
        new_room = Room(room_number, host, start_time, end_time, from_date, to_date)
        self.rooms.append(new_room)
        return {"status": "success", "message": f"Room {room_number} booked successfully!"}
        
    # (Other methods like allocate_seat, show_room, show_all_rooms omitted for brevity)