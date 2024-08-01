from flask import Flask, request, jsonify, render_template, send_from_directory
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
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Configure Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Decode the base64 credentials
credentials_json = base64.b64decode(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_BASE64')).decode('utf-8')
creds_dict = json.loads(credentials_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])

# Authorize the client with the credentials
client = gspread.authorize(creds)

# Open the spreadsheet by URL
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak")
sheet = spreadsheet.worksheet("AttendanceData")
response_sheet = spreadsheet.worksheet("FormResponses")

@app.route('/')
def index():
    return render_template('index.html')

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
        # Open the Google Sheet by ID and select the 'Chapters' sheet
        sheet = client.open_by_key('1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak').worksheet('Chapters')
        
        # Get all data from the sheet
        data = sheet.get_all_values()
        
        # Log all data for debugging
        print(f"All data from 'Chapters' sheet: {data}")
        
        # Filter data based on the grade and subject, then map to get the chapters
        chapters = [row[2] for row in data if row[0] == grade and row[1] == subject]
        
        # Log the filtered chapters for debugging
        print(f"Filtered chapters for Grade: {grade}, Subject: {subject}: {chapters}")
        
        return jsonify({'chapters': chapters})
    except Exception as e:
        print(f'Error in get_chapters: {e}')
        raise Exception('Failed to retrieve chapters')

def get_chapters(subject, grade):
    try:
        # Open the Google Sheet by ID and select the 'Chapters' sheet
        sheet = client.open_by_key('1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak').worksheet('AttendanceData')
        
        # Get all data from the sheet
        data = sheet.get_all_values()
        
        # Filter data based on the grade and subject, then map to get the chapters
        chapters = [row[7] for row in data if row[6] == grade and row[7] == subject]
        
        return chapters
    except Exception as e:
        print(f'Error in get_chapters: {e}')
        raise Exception('Failed to retrieve chapters')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    branch_name = data['branchName']
    batch_name = data['batchName']
    grade = data['grade']
    teacher_name = data['teacherName']
    subject_name = data['subjectName']
    chapter_name = data['chapterName']
    subtopic_name = data['subtopicName']
    student_data = data['studentData']
    class_type = data['classType']

    # Collect all rows of data
    rows_to_add = []
    for student in student_data:
        rows_to_add.append([
            student['studentName'], student['assignmentGrade'], class_type, student['present'],
            student['quizScore'], subject_name, chapter_name,
            grade, teacher_name, branch_name, batch_name, date, time, subtopic_name
        ])

    # Append all rows at once
    response_sheet.append_rows(rows_to_add)

    # Calculate the topper and present count
    quiz_scores = [int(student['quizScore']) for student in student_data if student['present'] == 'Present']
    topper = max(student_data, key=lambda x: int(x['quizScore']) if x['present'] == 'Present' else 0)
    present_count = sum(1 for student in student_data if student['present'] == 'Present')

    return jsonify({
        'topperName': topper['studentName'],
        'presentCount': present_count
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Ensure it's accessible