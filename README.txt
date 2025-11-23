================================================================
SMART UNIVERSITY ROOM ALLOTMENT SYSTEM - FINAL YEAR PROJECT
================================================================

[1] PROJECT OVERVIEW
--------------------
This project is a full-stack automated room scheduling system designed for universities. 
It replaces manual booking processes with an intelligent, conflict-free allocation engine. 
The system integrates:
- A custom Python-based Data Structures & Algorithms (DSA) core for conflict resolution.
- A Generative AI (NLP) layer that allows users to book rooms using natural language commands.
- A secure Role-Based Access Control (RBAC) system for Admins, Faculty, and Students.

[2] TECHNOLOGY STACK
--------------------
- Backend: Python 3.x, Flask (REST API), Pandas (Data Processing)
- Frontend: HTML5, JavaScript (ES6+), W3.CSS Framework
- Data Storage: CSV Flat-file Database (rooms_master.csv, user_master.csv)
- AI Component: Natural Language Processing (NLP) Parser (Simulated/Ollama Integration Architecture)
- Version Control: GitHub

[3] FILE STRUCTURE
------------------
- api_server.py         : The main Python Flask server (Logic + API Routes).
- index.html            : The project Landing Page.
- login.html            : The central Role Selection Hub.
- admin-login.html      : Dedicated login page for Administrators.
- faculty-login.html    : Dedicated login page for Faculty/Staff.
- student-login.html    : Dedicated login page for Students.
- control-panel.html    : The main AI Command Center for Admin/Faculty booking.
- dashboard.html        : The read-only Schedule Viewer and Request Form for Students.
- adminrequests.html    : The Admin interface to review and approve student requests.
- manualhandle.html     : A manual form-based booking page (Override).
- style.css             : Global styling sheet.
- rooms_master.csv      : Dataset containing university room details.
- user_master.csv       : Dataset containing authorized users and roles.

[4] HOW TO RUN THE PROJECT
--------------------------
1. Prerequisites:
   Ensure Python is installed on your machine.
   Install required libraries by running:
   >> pip install flask flask-cors pandas

2. Start the Server:
   Open your terminal in the project folder and run:
   >> python api_server.py
   
   (Keep this terminal window open while using the app)

3. Launch the Application:
   Open 'index.html' in your web browser.

[5] DEMONSTRATION CREDENTIALS
-----------------------------
To log in, use the exact User IDs from 'user_master.csv'. The default demo password is '12345'.

- Administrator:
  User ID: Himanshu
  Password: 12345

- Faculty:
  User ID: Mr. Imran Siraj (or any other Faculty name from CSV)
  Password: 12345

- Student:
  User ID: (Any Name)
  Password: (Any) - Student login is open for demo purposes.

[6] KEY FEATURES TO TEST
------------------------
1. AI Command Booking: Log in as Admin/Faculty and type "Book Classroom R101 for 10:00 to 12:00".
2. Conflict Resolution: Try to book the same room at the same time again to see the AI suggestion.
3. Student Request: Log in as Student, submit a request, then log in as Admin to review it in the 'Review Requests' panel.