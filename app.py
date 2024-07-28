from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Configure Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/Users/karanjalali/Desktop/Visual_Code_Attendance/groomville-d7053-a34cbef576f9.json", scope)
client = gspread.authorize(creds)

# Open the spreadsheet by URL
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1-JBOTTfWizQnY4-JFXVPhCbFuWkcqutNMgd-L_NoFak/edit?gid=1886189268#gid=1886189268")
sheet = spreadsheet.worksheet("AttendanceData")
response_sheet = spreadsheet.worksheet("FormResponses")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    branches = list(set(sheet.col_values(10)[1:]))
    teachers = list(set(sheet.col_values(9)[1:]))
    subjects = list(set(sheet.col_values(6)[1:]))
    grades = list(set(sheet.col_values(8)[1:]))
    class_types = list(set(sheet.col_values(3)[1:]))

    # Fetching student data for populating dropdowns
    student_records = sheet.get_all_records()
    students = [{'branchName': rec['Branch'], 'batchName': rec['Batch'], 'studentName': rec['Student']} for rec in student_records]
    chapter_names = [{'subjectName': rec['Subject'], 'chapterName': rec['Chapter Name']} for rec in student_records]
    assignment_grades = list(set([rec['Assignment Grade'] for rec in student_records]))
    batches = list(set([rec['Batch'] for rec in student_records]))

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

    # Append data to the Google Sheet
    for student in student_data:
        response_sheet.append_row([
            student['studentName'], student['assignmentGrade'], class_type, student['present'],
            student['quizScore'], subject_name, chapter_name,
            grade, teacher_name, branch_name, batch_name, date, time, subtopic_name
        ])

    # Calculate the topper and present count
    quiz_scores = [int(student['quizScore']) for student in student_data if student['present'] == 'Present']
    topper = max(student_data, key=lambda x: int(x['quizScore']) if x['present'] == 'Present' else 0)
    present_count = sum(1 for student in student_data if student['present'] == 'Present')

    return jsonify({
        'topperName': topper['studentName'],
        'presentCount': present_count
    })

if __name__ == "__main__":
    app.run(debug=True)