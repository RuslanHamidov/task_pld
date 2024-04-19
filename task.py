from flask import Flask, request, jsonify
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
app = Flask(__name__)

# Database initialization
def initialize_database():
    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, user_id INTEGER,
                 name TEXT, description TEXT, category_id INTEGER, due_date TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 FOREIGN KEY(category_id) REFERENCES categories(id))''')

    conn.commit()
    conn.close()

initialize_database()

# Add User Endpoint
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({'error': 'Username, password, and email are required.'}), 400

    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User added successfully.'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists.'}), 400

# Add Category Endpoint
@app.route('/add_category', methods=['POST'])
def add_category():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Category name is required.'}), 400

    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Category added successfully.'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Category already exists.'}), 400

# Add Task Endpoint
@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')
    due_date = data.get('due_date')

    if not user_id or not name or not category_id or not due_date:
        return jsonify({'error': 'User ID, name, category ID, and due date are required.'}), 400

    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, name, description, category_id, due_date) VALUES (?, ?, ?, ?, ?)",
              (user_id, name, description, category_id, due_date))
    conn.commit()
    conn.close()

    # Send email reminder
    send_email_reminder(user_id, name, description, due_date)

    return jsonify({'message': 'Task added successfully.'}), 201

# View Tasks Endpoint
@app.route('/view_tasks/<int:user_id>', methods=['GET'])
def view_tasks(user_id):
    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    c.execute("SELECT t.id, t.name, t.description, c.name AS category, t.due_date \
               FROM tasks t \
               INNER JOIN categories c ON t.category_id = c.id \
               WHERE t.user_id=?", (user_id,))
    tasks = [{'id': row[0], 'name': row[1], 'description': row[2], 'category': row[3], 'due_date': row[4]} for row in c.fetchall()]
    conn.close()

    return jsonify({'tasks': tasks})

# Function to send email reminder
def send_email_reminder(user_id, task_name, task_description, due_date):
    conn = sqlite3.connect('tasks1.db')
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE id=?", (user_id,))
    user_email = c.fetchone()[0]
    conn.close()

    sender_email = 'urfanmusayev2003@gmail.com'
    sender_password = 'tlss uhns chvf yllb'
    receiver_email = user_email
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Task Reminder: ' + task_name
    body = f"Dear User,\n\nThis is a reminder for the task:\n\nName: {task_name}\nDescription: {task_description}\nDue Date: {due_date}\n\nBest regards,\nYour Task Management App"
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    app.run(debug=True)
