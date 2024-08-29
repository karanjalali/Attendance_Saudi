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
base64_string = 'ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiZ3Jvb212aWxsZS1kNzA1MyIsCiAgInByaXZhdGVfa2V5X2lkIjogIjM1NjZlMTcyZWViODU4NzMyZmJiZGE4MTQzNDRjZjMyZDZjZjE3NDYiLAogICJwcml2YXRlX2tleSI6ICItLS0tLUJFR0lOIFBSSVZBVEUgS0VZLS0tLS1cbk1JSUV2UUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktjd2dnU2pBZ0VBQW9JQkFRQzRnb0c4MzhtZVlsbnFcbjI5eGg5cUYzT1JraEE2SWdBWmhSR3BRdit1STRJaXQvTUhLd3ZwaWI0dWhpZWtRaldIaXlJSGM2TjFmeGFJN0lcbnl5VmFScmhkY2tBKzQrcnVXSDArdHBZOVc0MXZwc0Zuc056VUw4VVcydGtibGNicnVSeEROd0dyZWNtVElhdDJcbnF0NHlCVWVqWjdXalNwNzVOOTFzSzVUTnFlQ1AySFhBVjFaZnFKZFR0aTYrbFZvSkFqcEpjZzNrYzVLMUN0QzZcbllpcWI1WHpyNmhXRlNoUWprMFhTS0tXWm55MXJTUHRYOE0zY3VNdE9iVnlTajlxWGxvNEhiMnFhTzZvOVJYTzhcbnVKcm5LUVJhbnJyQ0JHdFZRbURDZndUYmxydjBkQzF0ZG5xM3VNNmhXMGNRM3JidkdHMDMyQXNrSVAwc2VodS9cbkphWVNxbmhKQWdNQkFBRUNnZ0VBRUNuN3ZtMlBBdEY4TGQxdXdrVEtXckRkZlJWTnh0Ykk3cU1BMUM2N0VuNllcbjE2ckpnMmNoSkxmMVVvcENUYVBtcC9rODVMUmNQNVdBdThIRFB4Ukd1c1lEYjVjRk9mWDEyL0NBT3pZWjd3djVcbmNkRnVXU2Jwc2VIQWh5Q0JGWjNKQm5EclZDZkdVMTNONFFhaFVsbkF6OFdLUmJqSDhrNlU5dkRlOTRFQVA2Mm9cbis1RDlSTTBpYmZEOXhhYUxxZHpRTkRTWStqT29wZU1la1g3VFBPREl5OVIydGFydGpBUkJQdS9uVFIyMDF0REFcbmd6NUhMQmRjSXZUaTNCT2dkMXRndTVoeHd2YWM5U1h1T2VhY0hmY2NFNlk2ODNheWErOW5LQk5pT2thZzZ0ZWpcblZYVFl4VUFHV1hWWnFrVjdLZjlGRE9mdXd4c21OMEhLbUJQQjJkcTJvUUtCZ1FEKzVvTitjZkdrMVNUQ09hY1FcbkFIY0ZSSzJtWVdScGlWbkJ0Vzh0YXp6Z3ZBMHVUNm5aN0VqeW5nMnpDZnJkOXZhcHhyRjVNQWZhZ2hrMEpYd2pcblRGa09NM0duRFV0NS8rbENQV3lxSENadFJNc0Z2Q2d4SVp5Z21qZHllK0lyUExxRHhvQkUyZFFmYkZrSVFyTkdcbkREN3BrZWgvSU5HZzY3WGN0UXdqTGlUSDZRS0JnUUM1VGtMRDJGeHFua3ZnNE1xZ1o5ZURFZmFRWUE2QkY0RGNcblFBUmlpVm1ZekhnR2RHVWNLOW5keXdyUUFRa3pIM2NnN1UzcVBlWHQrd1NBd2Y4a1dsTGV1QzFCMHZXSURRZnlcbjRVc0R1L2ZUWXFscWVTU2ppVmFBVzRoTG5ET29FKzB0VUFjM2FBVnhBeU45NWYxK3lhQnBLK0xqTFNlZzhpbC9cbk5zTUVwV3BSWVFLQmdRQzJaZHpTTGxicnpGbHhZaS9aazN1WG1YMXBBV2dJM1BBTlhQY2hXUXRIQlVtcFNmZ1FcbnFMUEthSzhFM3E5VkJkT2J5VUpWcGJqNDh2OTJBUnpEWlc2VWF0dDQzbHFVQWp1MzJweFhYYTFobzBoajRqQWdcbmVCek1ENDU5cllnNXlFcnU0S3dJbUpiaHBYWlFJdXFGeFYxL1paa28zeU1pTTRqL1ZjNUpua3RUZ1FLQmdHYzdcbllCcDJ5RlZsUm1STEZ0Ynh3cS8wSytZV2ZUNFJkK283aDdYVlNxTERGZ0tTaVZsK1hHc2hHQzcweE1sRU9EdVJcbnVCeE15M0VlckUyR3hicmN6dG5neE9Xc3ZyaENlakVtcllHeEQ4a2xaN2czTU9BaVBKeFpZYjZ0a0dHTWFFOGNcbkRFa2puQlJ2YVRCVUZqcXgzTGw2aDNXRHpGWHZVb3JhV1I2WGdIbEJBb0dBVEhUeUlhY3dDZFBuaUwzUjd5ZVJcblYyaUNOcmRpb1FvdW0wM0I3RXAzTjVGTmw2UHRORW5xYmFxYTh4OFA4ZFBycVhmenpOZ2Zwa01LbzFyWGRaR01cbktFV3lZdkhPa0h2N204b3NQUXpaWHJRWXZZU1YyeFlKeldjNThHQVl0Q1ZQZE9xQjNrbkgydHNHb1NpRUpOK0xcbjFpUnViajBLbUV2Q2ljU3FzemEzRVhVPVxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwKICAiY2xpZW50X2VtYWlsIjogImthcmFuamFsYWxpQGdyb29tdmlsbGUtZDcwNTMuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJjbGllbnRfaWQiOiAiMTA4MDI2NzEwMjA4OTY4OTE5MjcwIiwKICAiYXV0aF91cmkiOiAiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL2F1dGgiLAogICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLAogICJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3YxL2NlcnRzIiwKICAiY2xpZW50X3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vcm9ib3QvdjEvbWV0YWRhdGEveDUwOS9rYXJhbmphbGFsaSU0MGdyb29tdmlsbGUtZDcwNTMuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20iCn0K'

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Hardcoded credentials for simplicity
USERNAME = 'admin'
PASSWORD = 'password123'

# Configure Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load and decode the base64 encoded credentials
credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_BASE64')

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