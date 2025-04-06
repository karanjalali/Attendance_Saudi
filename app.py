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

# Base64 encoded Google credentials
base64_string = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_BASE64')

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, resources={r"/*": {"origins": "*"}})

USERNAME = 'admin'
PASSWORD = 'password123'

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

if not base64_string:
    raise ValueError("The environment variable 'GOOGLE_APPLICATION_CREDENTIALS_BASE64' is not set")

creds_dict = json.loads(base64.b64decode(base64_string).decode('utf-8'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

google_sheet_url = "https://docs.google.com/spreadsheets/d/1PygGy0YAV7VczmRfDhaV10GYZWQmBMmoHg0XhKfHdAo"
spreadsheet = client.open_by_url(google_sheet_url)
sheet = spreadsheet.worksheet("AttendanceData")
response_sheet = spreadsheet.worksheet("FormResponses")
chapters_sheet = spreadsheet.worksheet("Chapters")

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
            return redirect(url_for('attendance_form'))
        else:
            error = 'Invalid credentials. Please try again.'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/attendance_form')
def attendance_form():
    if 'logged_in' in session and session['logged_in']:
        return render_template('index.html')
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
        teachers = sorted(list(set(sheet.col_values(9)[1:])))
        subjects = sorted(list(set(sheet.col_values(7)[1:])))
        grades = sorted(list(set(sheet.col_values(6)[1:])))
        class_types = sorted(list(set(sheet.col_values(3)[1:])))
        batches = sorted(list(set([rec['Batch'] for rec in sheet.get_all_records()])))

        student_records = sheet.get_all_records()
        students = [{'branchName': rec['Branch'], 'batchName': rec['Batch'], 'studentName': rec['Student']} for rec in student_records]

        chapter_names = [{'subjectName': rec['Subject'], 'chapterName': rec['Chapter Name']} for rec in student_records]
        assignment_grades = list(set([rec['Assignment Grade'] for rec in student_records]))

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
        all_data = chapters_sheet.get_all_records()
        chapters = [
            row['Chapter'] for row in all_data
            if str(row.get('Grade', '')).strip().lower() == str(grade).strip().lower() and
               str(row.get('Subject', '')).strip().lower() == str(subject).strip().lower()
        ]
        return jsonify({'chapters': chapters})
    except Exception as e:
        print(f'Error in get_chapters: {e}')
        return jsonify({'error': str(e)})

@app.route('/get_batches', methods=['GET'])
def get_batches():
    branch = request.args.get('branch')
    try:
        batches = sorted(list(set([rec['Batch'] for rec in sheet.get_all_records() if rec['Branch'] == branch])))
        return jsonify({'batches': batches})
    except Exception as e:
        print(f"Error in get_batches: {e}")
        return jsonify({'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime("%d-%b-%y"))
        time = data.get('time', datetime.now().strftime("%H:%M:%S"))

        branch_name = data['branchName']
        batch_name = data['batchName']
        grade = data['grade']
        teacher_name = data['teacherName']
        subject_name = data['subjectName']
        chapter_name = data['chapterName']
        subtopic_name = data['subtopicName']
        student_data = data['studentData']
        class_type = data['classType']

        print("Student Data:", student_data)

        rows_to_add = []
        for student in student_data:
            row = [
                student['studentName'],          # Column A: Student
                class_type,                      # Column B: Class Type
                student['present'],              # Column C: Present/Absent
                subject_name,                    # Column D: Subject
                chapter_name,                    # Column E: Chapter Name
                grade,                           # Column F: Grade
                teacher_name,                    # Column G: Teacher
                branch_name,                     # Column H: Branch
                batch_name,                      # Column I: Batch
                date,                            # Column J: Date
                time,                            # Column K: Time
                subtopic_name                    # Column L: Sub-Topic
            ]
            rows_to_add.append(row)

        print("Submitting rows:", rows_to_add)

        response_sheet.append_rows(rows_to_add)

        # Store recent submissions in session
        session['recent_submissions'] = rows_to_add

        return jsonify({'message': 'Form submitted successfully', 'redirect': url_for('view_submissions')})
    except Exception as e:
        print(f"Error in /submit: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/view_submissions')
def view_submissions():
    try:
        data = session.pop('recent_submissions', [])
        return render_template('submissions.html', submissions=data)
    except Exception as e:
        print(f"Error in /view_submissions: {e}")
        return "Error loading submissions."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)