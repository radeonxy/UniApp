from flask import Flask, request, render_template_string, redirect, url_for, session, render_template
import hashlib
import datetime
import fct_module as fct
import mysql.connector

app = Flask(__name__)
app.secret_key = 'AUL-3020220003'

# Store user data in a text file
USER_DATA_FILE = 'user_data.txt'
USER_MESSAGES_FILE = 'user_messages.txt'
INSTRUCTOR_DATA_FILE = 'instructor_data.txt'

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'university',
}

# Establish a connection to the database
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()






# Function to fetch student data from the database
def get_student_data(username):
    query = (
        "SELECT c.course_name, c.credits, c.fees, c.total "
        "FROM students s "
        "JOIN student_courses sc ON s.student_id = sc.student_id "
        "JOIN courses c ON sc.course_id = c.course_id "
        f"WHERE s.username = '{username}';"
    )
    cursor.execute(query)
    data = cursor.fetchall()
    return data


@app.route('/student_data')
def student_data():
    if 'username' in session:
        username = session['username']
        courses_data = get_student_data(username)
        return render_template('student_data.html', student_data=courses_data)
    else:
        return redirect(url_for('login'))


##############adding courses here#################


@app.route('/register_course', methods=['GET', 'POST'])
def register_course():
    if 'instructor_id' in session:
        if request.method == 'POST':
            course_name = request.form['course_name']
            student_id = request.form['student_id']

            # Get the course_id based on the selected course_name
            course_id = get_course_id(course_name)

            # Check if the student exists
            if student_exists(student_id):
                # Check if the student is already registered for the selected course
                if not is_student_registered(student_id, course_id):
                    # Insert the data into the registered_courses table
                    query = "INSERT INTO student_courses (student_id, course_id) VALUES (%s, %s)"
                    values = (student_id, course_id)
                    cursor.execute(query, values)
                    connection.commit()

                    return render_template_string('''
                    <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                    <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                    <h2>Student registered for the course successfully.</h2>
                    <a href="/inst_dashboard">Go back to Dashboard</a>
                    ''')
                else:
                    return render_template_string('''
                    <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                    <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                    <h2>Student is already registered for the selected course.</h2>
                    <a href="/register_course">Go back</a>
                    ''')

            return render_template_string('''
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                <h2>Invalid student ID</h2>
                <a href="/register_course">Go back</a>
                ''')

        # Get the list of courses for the dropdown
        courses = get_course_list()
        return render_template('register_courses.html', courses=courses)

    return redirect(url_for('inst_login'))


# Helper function to get the list of course names
def get_course_list():
    query = "SELECT course_name FROM courses"
    cursor.execute(query)
    return [course[0] for course in cursor.fetchall()]


# Helper function to get the course_id based on course_name
def get_course_id(course_name):
    query = "SELECT course_id FROM courses WHERE course_name = %s"
    values = (course_name,)
    cursor.execute(query, values)
    result = cursor.fetchone()
    return result[0] if result else None


# Helper function to check if a student is already registered for a course
def is_student_registered(student_id, course_id):
    query = "SELECT COUNT(*) FROM student_courses WHERE student_id = %s AND course_id = %s"
    values = (student_id, course_id)
    cursor.execute(query, values)
    return cursor.fetchone()[0] > 0


# Helper function to check if a student exists
def student_exists(student_id):
    query = "SELECT COUNT(*) FROM students WHERE student_id = %s"
    values = (student_id,)
    cursor.execute(query, values)
    return cursor.fetchone()[0] > 0


###################################################
def load_user_messages():
    try:
        with open(USER_MESSAGES_FILE, 'r') as file:
            data = file.readlines()
        user_messages = {}
        for line in data:
            parts = line.split()
            username = parts[0]
            timestamp = parts[1]
            sender = parts[2]
            message = ' '.join(parts[3:])
            if username not in user_messages:
                user_messages[username] = []
            user_messages[username].append((timestamp, sender, message))
        return user_messages
    except FileNotFoundError:
        return {}


def save_user_messages(user_messages):
    with open(USER_MESSAGES_FILE, 'w') as file:
        for username, messages in user_messages.items():
            for timestamp, sender, message in messages:
                file.write(f'{username} {timestamp} {sender}: {message}\n')


# main page
@app.route('/')
def home():
    return render_template('index.html')




@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    success_message = None
    error_message = None

    if request.method == 'POST':
        # Extracting data from the form
        username = request.form['username']
        major = request.form['major']
        phone_nb = request.form['phone_nb']
        registration_date = request.form['registration_date']

        try:
            # SQL query to insert data into the database
            insert_query = "INSERT INTO students (username, major, phone_nb, registration_date) VALUES (%s, %s, %s, %s)"

            # Data to be inserted
            student_data = (username, major, phone_nb, registration_date)

            # Executing the query
            cursor.execute(insert_query, student_data)

            # Committing the transaction
            connection.commit()

            # Get the auto-generated student ID
            student_id = cursor.lastrowid

            # Display success message with student ID
            success_message = f"Student registered successfully and his ID is: {student_id}"
        except Exception as e:
            # Display error message
            error_message = "An error occurred while registering the student. Please try again."
            print("Error:", e)

    return render_template('add_student.html', success_message=success_message, error_message=error_message)


@app.route('/view_std_data', methods=['GET', 'POST'])
def display_students():
    search_result = None

    if request.method == 'POST':
        search_query = request.form['search_query']

        # SQL query to search for students
        search_sql = "SELECT * FROM students WHERE username LIKE %s OR major LIKE %s OR phone_nb LIKE %s"

        # Data for executing the search query
        search_data = ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%')

        # Executing the search query
        cursor.execute(search_sql, search_data)

        # Fetching search results
        search_result = cursor.fetchall()

    # SQL query to fetch all students
    all_students_sql = "SELECT * FROM students"

    # Executing the query
    cursor.execute(all_students_sql)

    # Fetching all students data
    all_students = cursor.fetchall()

    return render_template('display_students.html', all_students=all_students, search_result=search_result)


# instructor page
@app.route('/instructor_section')
# register page
def register_section_home():
    return render_template('instructor_section.html')


# instructor registration
@app.route('/instructor_register', methods=['GET', 'POST'])
def inst_register():
    if request.method == 'POST':
        instructor_id = request.form['instructor_id']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        instructor_data = fct.load_instructor_data()
        if instructor_id not in instructor_data:
            instructor_data[instructor_id] = hashed_password
            fct.save_instructor_data(instructor_data)
            return redirect(url_for('instructor_login'))
        else:
            return "This instructor ID is already used, please check your entry or contact the university."
    # REGISTER CODE
    return render_template('inst_register.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Query to check if the student ID exists in the database
        query = "SELECT username FROM students WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        result = cursor.fetchone()

        if result:
            existing_username = result[0]
            if existing_username != username:
                return render_template_string('''
                    <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                    <link rel="stylesheet" href="{{ url_for('static', filename='/styles_user.css') }}">
                    <div class="content-container">
                        <h2>Invalid Username</h2>
                        <p>The provided username does not match the username associated with the student ID. Please try again.</p>
                        <a href="/register" class="button">Try Again</a>
                    </div>
                ''')
        else:
            # If the student ID is not found in the database, display an error message
            return render_template_string('''
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                <link rel="stylesheet" href="{{ url_for('static', filename='/styles_user.css') }}">
                <div class="content-container">
                    <h2>Invalid Student ID</h2>
                    <p>The provided student ID does not exist. Please try again.</p>
                    <a href="/register" class="button">Try Again</a>
                </div>
            ''')

        user_data = fct.load_user_data()
        if username not in user_data:
            user_data[username] = hashed_password
            fct.save_user_data(user_data)
            return redirect(url_for('login'))
        else:
            return render_template_string('''
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                <link rel="stylesheet" href="{{ url_for('static', filename='/styles_user.css') }}">
                <div class="content-container">
                    <h2>Username Already Exists</h2>
                    <p>The username you provided is already in use. Please choose another username.</p>
                    <a href="/register" class="button">Try Again</a>
                </div>
            ''')

    # Render the registration form HTML template for GET requests
    return render_template('student_register.html')

# user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user_data = fct.load_user_data()
        if username in user_data and user_data[username] == hashed_password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template_string('''
                <body>
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                 <link rel="stylesheet" href="{{ url_for('static', filename='/styles_user.css') }}">
                <h1>Wrong username or password</h1>
                <a href="/login" class="button">Try again</a>
                </body>
            ''')
    return render_template('student_login.html')


# inst login
@app.route('/instructor_login', methods=['GET', 'POST'])
def inst_login():
    if request.method == 'POST':
        instructor_id = request.form['instructor_id']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        instructor_data = fct.load_instructor_data()
        if instructor_id in instructor_data and instructor_data[instructor_id] == hashed_password:
            session['instructor_id'] = instructor_id
            return redirect(url_for('inst_dashboard'))
        else:
            return "Invalid instructor ID or password. Please try again."

    return render_template_string('''
        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
        <link rel="stylesheet" href="{{ url_for('static', filename='/styles_inst.css') }}">
        <h1>Login</h1>
        <h2>Please enter your credentials below to proceed
        <br>If you are a new user, please go back and register</h2>
        <form method="POST" action="{{ url_for('inst_login') }}">
            <label for="instructor_id">Instructor ID:</label>
            <input type="text" id="instructor_id" name="instructor_id" required><br>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
        <a href="/instructor_section" class="button">Go back</a>
    ''')


# instructor reset password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'instructor_id' in session:
        if request.method == 'POST':
            student_username = request.form['student_username']
            new_password = request.form['new_password']
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()

            user_data = fct.load_user_data()
            if student_username in user_data:
                user_data[student_username] = hashed_new_password
                fct.save_user_data(user_data)
                return render_template_string('''
                                        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                                         <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                                        <h2>Password reset successful</h2>
                                        <form method="POST">
                                        </form>
                                        <a href="/inst_dashboard">Done</a>
                                    ''')

            return render_template_string('''
                        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                         <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                        <h2>Student's username not found!</h2>
                        <form method="POST">
                        </form>
                        <a href="/reset_password">Try again</a>
                    ''')

        return render_template_string('''
            <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
             <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
            <h2>Reset Student's Password</h2>
            <form method="POST">
                <label for="student_username">Student Username:</label>
                <input type="text" id="student_username" name="student_username" required><br>
                <label for="new_password">New Password:</label>
                <input type="password" id="new_password" name="new_password" required><br>
                <input type="submit" value="Reset Password">
            </form>
            <a href="/inst_dashboard">Go back to Dashboard</a>
        ''')
    else:
        return redirect(url_for('inst_login'))


#################### user change password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' in session:
        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()

            user_data = fct.load_user_data()

            if session['username'] in user_data:
                if user_data[session['username']] == hashlib.sha256(old_password.encode()).hexdigest():
                    user_data[session['username']] = hashed_new_password
                    fct.save_user_data(user_data)
                    return render_template_string('''
                        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                        <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                        <h2>Password change successful</h2>
                        <form method="POST">
                        </form>
                        <a href="/dashboard">Done</a>
                    ''')

            return render_template_string('''
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                <h2>Incorrect old password!</h2>
                <form method="POST">
                </form>
                <a href="/change_password">Try again</a>
            ''')

        return render_template_string('''
            <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
            <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
            <h2>Change Password</h2>
            <form method="POST">
                <label for="old_password">Old Password:</label>
                <input type="password" id="old_password" name="old_password" required><br>
                <label for="new_password">New Password:</label>
                <input type="password" id="new_password" name="new_password" required><br>
                <input type="submit" value="Change Password">
            </form>
            <a href="/dashboard">Go back to Dashboard</a>
        ''')
    else:
        return redirect(url_for('/login'))


#####################
# inside the user's app
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('student_dashboard.html')

    else:
        return redirect(url_for('login'))


# inst_dashboard
@app.route('/inst_dashboard', methods=['GET', 'POST'])
def inst_dashboard():
    if 'instructor_id' in session:
        if request.method == 'POST' and request.form.get('logout_button'):
            session.pop('instructor_id', None)
            return redirect(url_for('home'))

        return render_template('instructor_dashboard.html')

    else:
        return redirect(url_for('inst_login'))


# gpa calculator

def calculate_letter_grade(grade):
    if 90 <= grade <= 100:
        return 'A'
    elif 80 <= grade < 90:
        return 'B'
    elif 70 <= grade < 80:
        return 'C'
    elif 50 <= grade < 70:
        return 'Pass'
    elif 0 <= grade < 50:
        return 'Fail'
    else:
        return 'Invalid Grade'


def calculate_gpa(grades):
    if not grades:
        return None
    return (sum(grades) / (100 * len(grades))) * 4


@app.route('/gpa_calculator', methods=['GET', 'POST'])
def gpa_calculator():
    if request.method == 'POST':
        num_grades = int(request.form.get('num_grades', 0))  # Get the number of grades
        grades = []

        for i in range(num_grades):
            grade = float(request.form.get(f'grade{i}', 0))
            grades.append(grade)

        overall_gpa = calculate_gpa(grades)

        grade_letter_list = [(grade, calculate_letter_grade(grade)) for grade in grades]

        return render_template('gpa_result.html', grade_letter_list=grade_letter_list, overall_gpa=overall_gpa)

    return render_template('gpa_calculator.html')


# messaging
@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if 'username' in session:
        if request.method == 'POST':
            receiver = request.form['receiver']
            message = request.form['message']
            timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

            user_messages = load_user_messages()
            if receiver in user_messages:
                user_messages[receiver].append((timestamp, session['username'], message))
            else:
                user_messages[receiver] = [(timestamp, session['username'], message)]
            save_user_messages(user_messages)
            return render_template_string('''
        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
         <link rel="stylesheet" href="{{ url_for('static', filename='/styles_msg.css') }}">
         <div class="content-container">
        <h2>Message sent successfully</h2>
            <a href="/send_message">Go back</a> </div>
        ''')

        return render_template_string('''
        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
         <link rel="stylesheet" href="{{ url_for('static', filename='/styles_msg.css') }}">
         <div class="content-container">
        <h2>Send a Message</h2>
            <form method="POST">
                <label for="receiver">Recipient's Username:</label>
                <input type="text" id="receiver" name="receiver" required><br>
                <label for="message">Message:</label>
                <textarea id="message" name="message" required></textarea><br>
                <input type="submit" value="Send">
            </form>
            <a href="/dashboard">Go back</a> </div>
        ''')
    else:
        return redirect(url_for('login'))


@app.route('/received_messages')
def received_messages():
    if 'username' in session:
        user_messages = load_user_messages()
        if session['username'] in user_messages:
            messages = user_messages[session['username']]
            if not messages:
                return "You have no messages."
            else:
                message_list = []
                for i, (timestamp, sender, message) in enumerate(messages, start=1):
                    message_link = f"<a href='/message/{i}'>[{i}] {sender} - {timestamp}</a><br>"
                    message_list.append(f"{message_link} ")
                messages_v = "<br>".join(message_list)

                return render_template_string('''
                        <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                        <link rel="stylesheet" href="{{ url_for('static', filename='/styles_msg.css') }}">
                        <head >
                            <title>Messages</title>
                        </head>
                        <body>''' f'''{messages_v}
                        </body>
                        <a href="/dashboard">Go back</a>

                     ''')
        else:
            return render_template_string('''
                    <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                    <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">
                    <h1>No messages</h1>
                    <a href="/dashboard">Go back</a>
                    ''')
    else:
        return redirect(url_for('login'))


@app.route('/carousel')
def carousel():
    return render_template('about_us.html')


@app.route('/message/<int:message_id>')
def view_message(message_id):
    if 'username' in session:
        user_messages = load_user_messages()
        if session['username'] in user_messages:
            messages = user_messages[session['username']]
            if 1 <= message_id <= len(messages):
                timestamp, sender, message = messages[message_id - 1]
                return render_template_string('''
                <div class="ribbon">FALL23 CCE Senior Project Faculty of Engineering - AUL</div>
                    <link rel="stylesheet" href="{{ url_for('static', filename='/styles.css') }}">'''
                                              f'''
                <h1>New message</h1>
                <h2><br><b>From</b> {message} <br></h2>
                <h2><b>Received on:</b> {timestamp}</br></h2>
                <a href='/received_messages'>Go back</a> ''')
            else:
                return "Invalid message ID."
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/inst_logout')
def inst_logout():
    session.pop('instructor_id', None)
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

