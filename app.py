print("Starting Flask app...",
flush=True)

from flask import Flask, request, jsonify,redirect,render_template, session,url_for
import joblib
import pandas as pd
import mysql.connector
from datetime import datetime
from flask_cors import CORS
from config import get_db_connection
from werkzeug.security import generate_password_hash,check_password_hash
import traceback
import os


app = Flask(__name__)
CORS(app)
model = joblib.load('model.pkl')
app.secret_key = os.environ.get('SECRET_KEY','defaultset')

@app.route('/generate-schedule', methods=['POST'])
def generate_schedule():
    data = request.json['subjects']
    schedule = []

    for subject in data:
        days_left = (datetime.strptime(subject['deadline'], "%Y-%m-%d") - datetime.today()).days
        prediction = model.predict([[subject['priority'], days_left]])
        hours = round(prediction[0], 2)

        schedule.append({
            'subject': subject['name'],
            'hours': hours,
            'deadline': subject['deadline']
        })

    return jsonify({'schedule': schedule})

tasks = []


@app.route('/tasks', methods=['GET'])
def get_tasks():
    global tasks
    try:
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM tasks")
            raw_tasks = cursor.fetchall()
            print("Fetched tasks:",raw_tasks)
            tasks = []

            for row in raw_tasks:
                # Example priority formula
                row['priority'] = int(row['difficulty']) * int(row['hours'])
                tasks.append(row)

        return jsonify({'tasks': tasks}), 200
    except Exception as e:
        return jsonify({'error in /tasks:',str(e)}), 500
    finally:
        if conn:
            conn.close
            
@app.route("/test")
def test():
    return "CORS working!"


@app.route('/add_task', methods=['POST'])
def add_task():
    global model
    data = request.get_json()
    print("DEBUG: Recieved data:", data)
    title = data.get('title')
    hours = data.get('hours')
    difficulty = data.get('difficulty')
    user_id = data.get('user_id')
    deadline = data.get('deadline') or "2025-12-31"
    
    if not all([title, hours, difficulty, user_id, deadline]):
      return jsonify({'error': 'Missing form data'}), 400
    
    try:
        hours = int(hours)
        difficulty = int(difficulty)
        user_id = int(user_id)
    except ValueError:
      return jsonify({"error": "Invalid numeric input"}), 400
    
    input_df = pd.DataFrame([{
    'hours': hours,
    'difficulty': difficulty,
    }])
    priority =  int(model.predict(input_df)[0])
    
    
    try:
        
        
       conn = get_db_connection()
       with conn.cursor(dictionary=True) as cursor:
        sql = """
            INSERT INTO
            tasks( user_id, title , hours, difficulty, priority, deadline)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        print("Executing SQL with values:",(user_id , title, hours, difficulty, priority, deadline))
        cursor.execute(sql, 
    (user_id, title , hours, difficulty, priority, deadline))
        conn.commit()
        
        
        
        task_id = cursor.lastrowid
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
           conn.close()

    
    task = {
        'id': task_id,
        'user_id': user_id,
        'title': title,
        'hours': hours,
        'difficulty': difficulty,
        'priority' : priority,
        'deadline' : deadline
    }

    tasks.append(task)
    tasks.sort(key=lambda x: x['priority'], reverse=True)
    
    return jsonify({"message": "Task added", "task": task}), 200


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (name, email, hashed_password))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template('register.html')  # HTML form

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['username']
            return redirect('/dashboard')
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    print("session before clearing:",dict(session))
    session.clear()
    print("session after clearing:",dict(session))
    return redirect('/login')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/delete_task/<int:index>', methods=['DELETE'])
def delete_task(index):
    global tasks

    if 0 <= index < len(tasks):
        task_to_delete = tasks[index]
        task_id = task_to_delete.get('id')  # Ensure each task has an 'id' from the DB

        try:
            # Delete from database
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "DELETE FROM tasks WHERE id = %s"
                cursor.execute(sql, (task_id,))
                conn.commit()

            # Delete from in-memory list
            del tasks[index]

            return jsonify({'message': 'Task deleted'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

        finally:
            if conn:
                conn.close()
    else:
        return jsonify({'error': 'Invalid index'}), 400
    

@app.route('/reset_tasks', methods=['DELETE'])
def reset_tasks():
    global tasks
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "DELETE FROM schedules"
            cursor.execute(sql)
            conn.commit()

        # Clear the in-memory list
        tasks.clear()

        return jsonify({'message': 'All tasks cleared.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "_main_":
    print("Inside __main__ block",
flush=True)
    app.run(debug=True,
host="127.0.0.1", port=5000)
        

   
