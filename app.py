"""
Todo App - Phase 1: Basic Flask App with SQLite
A simple daily todo list application with notifications
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
from datetime import datetime, date
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this to something secure

# Database file
DATABASE = 'todo.db'

def get_db():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def init_db():
    """Initialize the database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tasks table (simplified for daily use)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            task_time TEXT NOT NULL,  -- Format: HH:MM
            completed INTEGER DEFAULT 0,  -- 0 = not done, 1 = done
            notified INTEGER DEFAULT 0,   -- 0 = not notified, 1 = notified
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def hash_password(password):
    """Simple password hashing (use better methods in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

# Home page - shows today's tasks
@app.route('/')
def index():
    """Main page - shows today's tasks if user is logged in"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get today's tasks for the logged-in user
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? 
        ORDER BY task_time ASC
    ''', (session['user_id'],))
    
    tasks = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', tasks=tasks, username=session.get('username'))

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                      (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        email = request.form.get('email', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email) 
                VALUES (?, ?, ?)
            ''', (username, password, email))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Username already exists")
    
    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    """Log out the user"""
    session.clear()
    return redirect(url_for('login'))

# Add task
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    """Add a new task"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        task_time = request.form['task_time']  # Format: HH:MM
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, task_time) 
            VALUES (?, ?, ?)
        ''', (session['user_id'], title, task_time))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('add_task.html')

# Delete task
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    """Delete a task"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', 
                  (task_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Mark task as completed
@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    """Mark a task as completed"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?', 
                  (task_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# API endpoint for checking notifications (will be used in Phase 4)
@app.route('/api/check-notifications')
def check_notifications():
    """Check for tasks that need notifications"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    current_time = datetime.now().strftime('%H:%M')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Find tasks that are within 5 minutes of current time and not notified
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? 
        AND completed = 0 
        AND notified = 0
        AND task_time <= ?
        AND task_time > ?
    ''', (session['user_id'], 
          add_minutes_to_time(current_time, 5),  # Tasks in next 5 minutes
          current_time))  # Not past tasks
    
    tasks = cursor.fetchall()
    conn.close()
    
    # Convert to list of dicts for JSON response
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task['id'],
            'title': task['title'],
            'task_time': task['task_time']
        })
    
    return jsonify({'tasks': tasks_list})

def add_minutes_to_time(time_str, minutes):
    """Helper function to add minutes to a time string (HH:MM)"""
    t = datetime.strptime(time_str, '%H:%M')
    t = t.replace(year=1900, month=1, day=1)  # Add dummy date
    from datetime import timedelta
    t = t + timedelta(minutes=minutes)
    return t.strftime('%H:%M')


# Add these new functions after add_minutes_to_time()

@app.route('/api/task-response/<int:task_id>', methods=['POST'])
def task_response(task_id):
    """Handle user's response to task completion question"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    response = data.get('response')  # 'yes' or 'no'
    
    conn = get_db()
    cursor = conn.cursor()
    
    if response == 'yes':
        # Mark task as completed
        cursor.execute('UPDATE tasks SET completed = 1, notified = 1 WHERE id = ? AND user_id = ?', 
                      (task_id, session['user_id']))
    else:
        # Just mark as notified so we don't ask again
        cursor.execute('UPDATE tasks SET notified = 1 WHERE id = ? AND user_id = ?', 
                      (task_id, session['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/mark-notified/<int:task_id>', methods=['POST'])
def mark_notified(task_id):
    """Mark a task as notified (when we send a notification)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET notified = 1 WHERE id = ? AND user_id = ?', 
                  (task_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/get-previous-tasks')
def get_previous_tasks():
    """Get tasks that were in the past and need completion check"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    current_time = datetime.now().strftime('%H:%M')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Find tasks that are in the past (up to 2 hours ago) and not completed
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? 
        AND completed = 0 
        AND notified = 0
        AND task_time < ?
        AND task_time >= ?
    ''', (session['user_id'], 
          current_time,
          subtract_minutes_from_time(current_time, 120)))  # Last 2 hours
    
    tasks = cursor.fetchall()
    conn.close()
    
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task['id'],
            'title': task['title'],
            'task_time': task['task_time']
        })
    
    return jsonify({'tasks': tasks_list})

def subtract_minutes_from_time(time_str, minutes):
    """Helper function to subtract minutes from a time string"""
    t = datetime.strptime(time_str, '%H:%M')
    from datetime import timedelta
    t = t - timedelta(minutes=minutes)
    return t.strftime('%H:%M')
if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("🚀 Starting Todo App...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
