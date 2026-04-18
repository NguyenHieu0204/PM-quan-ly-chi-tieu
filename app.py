from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_expense():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (amount, type, description, date)
        VALUES (?, ?, ?, ?)
    ''', (float(data['amount']), data['type'], data['description'], data['date']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/update', methods=['POST'])
def update_expense():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expenses 
        SET amount = ?, type = ?, description = ?, date = ?
        WHERE id = ?
    ''', (float(data['amount']), data['type'], data['description'], data['date'], int(data['id'])))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/list')
def get_expenses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(debug=True, port=5001)