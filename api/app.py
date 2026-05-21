from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import time

app = Flask(__name__)
CORS(app)

# Database connection with retry logic
def get_db_connection():
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'tododb'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                port=os.getenv('DB_PORT', '5432')
            )
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise e

# Initialize database table
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# GET all todos
@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, title, completed, created_at FROM todos ORDER BY id DESC')
        todos = []
        for row in cur.fetchall():
            todos.append({
                'id': row[0],
                'title': row[1],
                'completed': row[2],
                'created_at': row[3].isoformat() if row[3] else None
            })
        cur.close()
        conn.close()
        return jsonify(todos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST create new todo
@app.route('/api/todos', methods=['POST'])
def create_todo():
    try:
        data = request.json
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO todos (title, completed) VALUES (%s, %s) RETURNING id, title, completed, created_at',
            (data['title'], data.get('completed', False))
        )
        row = cur.fetchone()
        todo = {
            'id': row[0],
            'title': row[1],
            'completed': row[2],
            'created_at': row[3].isoformat() if row[3] else None
        }
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(todo), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUT update todo
@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if todo exists
        cur.execute('SELECT id FROM todos WHERE id = %s', (todo_id,))
        if cur.fetchone() is None:
            cur.close()
            conn.close()
            return jsonify({'error': 'Todo not found'}), 404
        
        # Update todo
        cur.execute(
            'UPDATE todos SET title = %s, completed = %s WHERE id = %s RETURNING id, title, completed, created_at',
            (data.get('title'), data.get('completed'), todo_id)
        )
        row = cur.fetchone()
        todo = {
            'id': row[0],
            'title': row[1],
            'completed': row[2],
            'created_at': row[3].isoformat() if row[3] else None
        }
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(todo), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE todo
@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM todos WHERE id = %s RETURNING id', (todo_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted is None:
            return jsonify({'error': 'Todo not found'}), 404
        
        return jsonify({'message': 'Todo deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)