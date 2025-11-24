import sqlite3
import docker
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB_NAME = 'auth_users.db'

def init_db():
    """Створює базу даних SQLite та таблицю користувачів, якщо вони не існують."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# init db on start
init_db()

@app.route('/register', methods=['POST'])
def register_user():
    """Створює нового користувача з хешованим паролем."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # hash pass
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        
        return jsonify({'message': f'User {username} created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    except Exception as e:
        return jsonify({'message': f'An error occurred: {e}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    """Перевіряє облікові дані користувача."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # get hash pass from db
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    user_record = cursor.fetchone()
    conn.close()

    if user_record and check_password_hash(user_record[0], password):
        # todo: add generating token (now just mock)
        return jsonify({
            'message': 'Login successful', 
            'token': 'mock-auth-token-12345' 
        }), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/status', methods=['GET'])
def status():
    """Перевірка статусу сервера."""
    return jsonify({'status': 'Auth Server is running'}), 200

def is_authorized(auth_header):
    """Імітація перевірки токена авторизації."""
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # should be generated, now just mock
        return token == 'mock-auth-token-12345'
    return False

@app.route('/generator/<action>', methods=['POST'])
def control_generator(action):
    # check authorisation
    auth_header = request.headers.get('Authorization')
    if not is_authorized(auth_header):
        return jsonify({'message': 'Authorization required or invalid token'}), 401

    # 2. execute docker command
    if action not in ['start', 'stop']:
        return jsonify({'message': 'Invalid action. Use start or stop.'}), 400

    try:
        client = docker.from_env()
        container = client.containers.get('data_generator')

        if action == 'stop':
            container.stop()
            message = "Data Generator stopped successfully."
        elif action == 'start':
            container.start()
            message = "Data Generator started successfully."

        return jsonify({'message': message, 'status': container.status}), 200

    except docker.errors.NotFound:
        return jsonify({'message': 'Container data_generator not found.'}), 500
    except Exception as e:
        return jsonify({'message': f'Docker command failed: {e}'}), 500
    
if __name__ == '__main__':
    # server is launched on port 5000
    app.run(host='0.0.0.0', port=5000)