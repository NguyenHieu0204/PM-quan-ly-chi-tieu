from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
import os
import pandas as pd
from datetime import datetime
import io
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default-secret-key")

# Supabase Setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path in ['/add', '/update', '/list'] or request.path.startswith('/delete'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session['user'])

@app.route('/auth')
def auth():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    invite_code = data.get('invite_code')
    expected_code = os.environ.get('APP_INVITE_CODE', 'xpense123')
    
    if invite_code != expected_code:
        return jsonify({'status': 'error', 'message': 'Mã đăng ký không hợp lệ!'}), 403

    try:
        res = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })
        if res.user:
            return jsonify({'status': 'ok', 'message': 'Đăng ký thành công! Hãy kiểm tra email để xác nhận (nếu có).'})
        else:
            return jsonify({'status': 'error', 'message': 'Đăng ký thất bại.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        res = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })
        if res.user:
            session['user'] = {
                'id': res.user.id,
                'email': res.user.email
            }
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error', 'message': 'Sai email hoặc mật khẩu.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/logout')
def logout():
    supabase.auth.sign_out()
    session.pop('user', None)
    return redirect(url_for('auth'))

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    # The default value for user_id in Supabase is auth.uid(), 
    # but since RLS is enabled, we should specify it if we use Service Role, 
    # or just let Supabase handle it if we use the user's session token.
    # However, supabase-py by default uses the key provided. 
    # To use the user's session, we'd need to set the session in the client.
    
    # Simple way: just pass the user_id from our session
    res = supabase.table("expenses").insert({
        "amount": float(data['amount']),
        "type": data['type'],
        "description": data['description'],
        "date": data['date'],
        "user_id": session['user']['id']
    }).execute()
    return jsonify({'status': 'ok'})

@app.route('/update', methods=['POST'])
@login_required
def update_expense():
    data = request.json
    res = supabase.table("expenses").update({
        "amount": float(data['amount']),
        "type": data['type'],
        "description": data['description'],
        "date": data['date']
    }).eq("id", int(data['id'])).eq("user_id", session['user']['id']).execute()
    return jsonify({'status': 'ok'})

@app.route('/delete/<int:id>', methods=['DELETE', 'POST'])
@login_required
def delete_expense(id):
    supabase.table("expenses").delete().eq("id", id).eq("user_id", session['user']['id']).execute()
    return jsonify({'status': 'ok'})

@app.route('/list')
@login_required
def get_expenses():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = supabase.table("expenses").select("*").eq("user_id", session['user']['id'])
    if start and end:
        query = query.gte("date", start).lte("date", end)
    
    res = query.order("date", desc=True).order("id", desc=True).execute()
    return jsonify(res.data)

@app.route('/export')
@login_required
def export_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = supabase.table("expenses").select("*").eq("user_id", session['user']['id'])
    if start and end:
        query = query.gte("date", start).lte("date", end)
    
    res = query.order("date", desc=True).execute()
    df = pd.DataFrame(res.data)
    
    if df.empty:
        return "No data to export", 400
        
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

@app.route('/backup')
@login_required
def backup_json():
    res = supabase.table("expenses").select("*").eq("user_id", session['user']['id']).execute()
    output = io.BytesIO(str(res.data).encode())
    return send_file(output, as_attachment=True, download_name=f"Backup_TaiChinh_{datetime.now().strftime('%Y%m%d')}.json")

if __name__ == '__main__':
    app.run(debug=True, port=5001)