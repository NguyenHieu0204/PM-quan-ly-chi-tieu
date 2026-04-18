from flask import Flask, request, jsonify, render_template, send_file
import os
import pandas as pd
from datetime import datetime
import io
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Supabase Setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_expense():
    data = request.json
    # Supabase expects float for amount
    res = supabase.table("expenses").insert({
        "amount": float(data['amount']),
        "type": data['type'],
        "description": data['description'],
        "date": data['date']
    }).execute()
    return jsonify({'status': 'ok'})

@app.route('/update', methods=['POST'])
def update_expense():
    data = request.json
    res = supabase.table("expenses").update({
        "amount": float(data['amount']),
        "type": data['type'],
        "description": data['description'],
        "date": data['date']
    }).eq("id", int(data['id'])).execute()
    return jsonify({'status': 'ok'})

@app.route('/delete/<int:id>', methods=['DELETE', 'POST'])
def delete_expense(id):
    supabase.table("expenses").delete().eq("id", id).execute()
    return jsonify({'status': 'ok'})

@app.route('/list')
def get_expenses():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = supabase.table("expenses").select("*")
    if start and end:
        query = query.gte("date", start).lte("date", end)
    
    res = query.order("date", desc=True).order("id", desc=True).execute()
    return jsonify(res.data)

@app.route('/export')
def export_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = supabase.table("expenses").select("*")
    if start and end:
        query = query.gte("date", start).lte("date", end)
    
    res = query.order("date", desc=True).execute()
    df = pd.DataFrame(res.data)
    
    if df.empty:
        return "No data to export", 400
        
    # Reorder/rename columns for export
    df_export = df[["id", "amount", "type", "description", "date"]]
    df_export.columns = ["ID", "Số tiền (VNĐ)", "Phân loại", "Nội dung", "Ngày"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Chi tiết')
    output.seek(0)
    
    return send_file(output, 
                     as_attachment=True, 
                     download_name=f"Bao_cao_chi_tieu_{datetime.now().strftime('%Y%m%d')}.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Backup/Import functionality can be adapted or removed for Supabase
# For now, I'll keep simple JSON backup
@app.route('/backup')
def backup_json():
    res = supabase.table("expenses").select("*").execute()
    output = io.BytesIO(str(res.data).encode())
    return send_file(output, as_attachment=True, download_name=f"Backup_TaiChinh_{datetime.now().strftime('%Y%m%d')}.json")

if __name__ == '__main__':
    app.run(debug=True, port=5001)