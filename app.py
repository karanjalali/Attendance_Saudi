from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
import gspread
import os
import json
import base64
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import csv  # Import CSV module to read local CSV file (added from Oman)

# Base64 encoded Google credentials
base64_string = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_BASE64')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Hardcoded credentials for simplicity
USERNAME = 'admin'
PASSWORD = 'password123'

# Configure Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load and decode the base64 encoded credentials
credentials_json = base64_string

if not credentials_json:
    raise ValueError("The environment variable 'GOOGLE_APPLICATION_CREDENTIALS_BASE64' is not set")

creds_dict = json.loads(base64.b64decode(credentials_json).decode('utf-8'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the spreadsheet by URL
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak")
sheet = spreadsheet.worksheet("AttendanceData")
response_sheet = spreadsheet.worksheet("FormResponses")

# Chapter data CSV file path (same as in Oman app)
CHAPTER_DATA_FILE = 'Chapter Data - Sheet1.csv'

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            print("Login successful")
            return redirect(url_for('attendance_form'))
        else:
            error = 'Invalid credentials. Please try again.'
            print("Login failed")
            return render_template('login.html', error=error)
    print("Displaying login page")
    return render_template('login.html')

@app.route('/attendance_form')
def attendance_form():
    if 'logged_in' in session and session['logged_in']:
        return render_template('index.html')  # Assuming this is your attendance form
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/get_data')
def get_data():
    try:
        branches = sorted(list(set(sheet.col_values(10)[1:])))
        print("Branches:", branches)  # Log branches
        teachers = sorted(list(set(sheet.col_values(9)[1:])))
        print("Teachers:", teachers)  # Log teachers
        subjects = sorted(list(set(sheet.col_values(7)[1:])))
        print("Subjects:", subjects)  # Log subjects
        grades = sorted(list(set(sheet.col_values(6)[1:])))
        print("Grades:", grades)  # Log grades
        class_types = sorted(list(set(sheet.col_values(3)[1:])))
        print("Class Types:", class_types)  # Log class types
        batches = sorted(list(set([rec['Batch'] for rec in sheet.get_all_records()])))
        print("Batches:", batches)  # Log batches

        student_records = sheet.get_all_records()
        students = [{'branchName': rec['Branch'], 'batchName': rec['Batch'], 'studentName': rec['Student']} for rec in student_records]
        print("Students:", students)  # Log students
        chapter_names = [{'subjectName': rec['Subject'], 'chapterName': rec['Chapter Name']} for rec in student_records]
        print("Chapter Names:", chapter_names)  # Log chapter names
        assignment_grades = list(set([rec['Assignment Grade'] for rec in student_records]))
        print("Assignment Grades:", assignment_grades)  # Log assignment grades

        return jsonify({
            'branches': branches,
            'teachers': teachers,
            'subjects': subjects,
            'grades': grades,
            'classTypes': class_types,
            'students': students,
            'chapterNames': chapter_names,
            'assignmentGrades': assignment_grades,
            'batches': batches
        })
    except Exception as e:
        print("Error in /get_data:", str(e))
        return jsonify({'error': 'An error occurred while fetching data'}), 500

@app.route('/get_chapters', methods=['GET'])
def get_chapters():
    grade = request.args.get('grade')
    subject = request.args.get('subject')

    try:
        chapters = []

        # Read the CSV file
        with open(CHAPTER_DATA_FILE, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                row_grade = row[0].strip().lower()
                row_subject = row[1].strip().lower()

                if row_grade == grade.strip().lower() and row_subject == subject.strip().lower():
                    chapters.append(row[2])

        # Debugging: Print the filtered chapters
        print(f"Filtered Chapters: {chapters}")

        return jsonify({'chapters': chapters})
    except Exception as e:
        print(f'Error in get_chapters: {e}')
        return jsonify({'error': str(e)})

@app.route('/get_batches', methods=['GET'])
def get_batches():
    branch = request.args.get('branch')
    try:
        batches = sorted(list(set([rec['Batch'] for rec in sheet.get_all_records() if rec['Branch'] == branch])))
        print(f"Batches for branch {branch}: {batches}")
        return jsonify({'batches': batches})
    except Exception as e:
        print(f"Error in get_batches: {e}")
        return jsonify({'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        # Get the date and time from the form submission
        date = data.get('date', datetime.now().strftime("%d-%b-%y"))  # Format date as DD-MMM-YY
        time = data.get('time', datetime.now().strftime("%H:%M:%S"))  # Ensure time is also retrieved from the form

        branch_name = data['branchName']
        batch_name = data['batchName']
        grade = data['grade']
        teacher_name = data['teacherName']
        subject_name = data['subjectName']
        chapter_name = data['chapterName']
        subtopic_name = data['subtopicName']
        student_data = data['studentData']
        class_type = data['classType']

        rows_to_add = []
        for student in student_data:
            rows_to_add.append([
                student['studentName'], student['assignmentGrade'], class_type, student['present'],
                student['quizScore'], subject_name, chapter_name,
                grade, teacher_name, branch_name, batch_name, date, time, subtopic_name
            ])

        response_sheet.append_rows(rows_to_add)

        quiz_scores = [int(student['quizScore']) for student in student_data if student['present'] == 'Present']
        topper = max(student_data, key=lambda x: int(x['quizScore']) if x['present'] == 'Present' else 0)
        present_count = sum(1 for student in student_data if student['present'] == 'Present')

        return jsonify({
            'topperName': topper['studentName'],
            'presentCount': present_count
        })
    except Exception as e:
        print(f"Error in /submit: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)