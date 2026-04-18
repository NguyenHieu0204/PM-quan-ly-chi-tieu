from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
import os
import pandas as pd
import shutil
from datetime import datetime
import io

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

@app.route('/delete/<int:id>', methods=['DELETE', 'POST'])
def delete_expense(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/list')
def get_expenses():
    start = request.args.get('start')
    end = request.args.get('end')
    
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM expenses'
    params = []
    if start and end:
        query += ' WHERE date BETWEEN ? AND ?'
        params = [start, end]
    query += ' ORDER BY date DESC, id DESC'
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/export')
def export_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    
    conn = get_db()
    query = 'SELECT * FROM expenses'
    params = []
    if start and end:
        query += ' WHERE date BETWEEN ? AND ?'
        params = [start, end]
    query += ' ORDER BY date DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        return "No data to export", 400
        
    df.columns = ["ID", "Số tiền (VNĐ)", "Phân loại", "Nội dung", "Ngày"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Chi tiết')
    output.seek(0)
    
    return send_file(output, 
                     as_attachment=True, 
                     download_name=f"Bao_cao_chi_tieu_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/backup')
def backup_db():
    return send_file(DB_PATH, as_attachment=True, download_name=f"Backup_TaiChinh_{datetime.now().strftime('%Y%m%d')}.db")

@app.route('/import', methods=['POST'])
def import_db():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.db'):
        shutil.copy2(DB_PATH, DB_PATH + '.bak')
        file.save(DB_PATH)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Invalid format'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)