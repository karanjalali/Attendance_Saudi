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

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Hardcoded credentials for simplicity
USERNAME = 'admin'
PASSWORD = 'password123'

# Configure Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Decode the base64 credentials
credentials_json = base64.b64decode(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_BASE64')).decode('utf-8')
creds_dict = json.loads(credentials_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the spreadsheet by URL
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak")
sheet = spreadsheet.worksheet("AttendanceData")
response_sheet = spreadsheet.worksheet("FormResponses")

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

@app.route('/get_chapters', methods=['GET'])
def get_chapters():
    grade = request.args.get('grade')
    subject = request.args.get('subject')
    
    try:
        sheet = client.open_by_key('1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak').worksheet('Chapters')
        data = sheet.get_all_values()
        chapters = [row[2] for row in data if row[0] == grade and row[1] == subject]
        return jsonify({'chapters': chapters})
    except Exception as e:
        print(f'Error in get_chapters: {e}')
        raise Exception('Failed to retrieve chapters')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    # Use the manually entered date and time if provided, otherwise use current date and time
    date = data.get('date') or datetime.now().strftime("%Y-%m-%d")
    time = data.get('time') or datetime.now().strftime("%H:%M:%S")
    branch_name = data['branchName']
    batch_name = data['batchName']
    grade = data['grade']
    teacher_name = data['teacherName']
    subject_name = data['subjectName']
    chapter_name = data['chapterName']
    subtopic_name = data['subtopicName']
    class_type = data['classType']
    assignment_quiz_topic = data['assignmentQuizTopic']
    speed_quiz_topic = data['speedQuizTopic']
    comments = data['comments']
    student_data = data['studentData']

    rows_to_add = []
    for student in student_data:
        rows_to_add.append([
            student['studentName'], student['assignmentGrade'], class_type, student['present'],
            student['quizScore'], subject_name, chapter_name,
            grade, teacher_name, branch_name, batch_name, date, time, subtopic_name,
            assignment_quiz_topic, speed_quiz_topic, comments  # New fields added here
        ])

    response_sheet.append_rows(rows_to_add)

    quiz_scores = [int(student['quizScore']) for student in student_data if student['present'] == 'Present']
    topper = max(student_data, key=lambda x: int(x['quizScore']) if x['present'] == 'Present' else 0)
    present_count = sum(1 for student in student_data if student['present'] == 'Present')

    return jsonify({
        'topperName': topper['studentName'],
        'presentCount': present_count
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)