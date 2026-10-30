from flask import Flask, jsonify, request, render_template
import sqlite3, os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'gramasathi.db'
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def log_action(action, details=''):
    with db() as con:
        con.execute('INSERT INTO activity_log(action, details, created_at) VALUES(?,?,?)',
                    (action, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def init_db():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS complaints (
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, citizen TEXT NOT NULL,
          category TEXT NOT NULL, description TEXT NOT NULL, officer TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Pending', remarks TEXT DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, name TEXT NOT NULL,
          mobile TEXT NOT NULL, role TEXT NOT NULL, village TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Active', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS services (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
          description TEXT DEFAULT '', icon TEXT DEFAULT '🛠️', status TEXT NOT NULL DEFAULT 'Active');
        CREATE TABLE IF NOT EXISTS notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, message TEXT NOT NULL,
          kind TEXT DEFAULT 'info', is_read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS activity_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, details TEXT DEFAULT '', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS admin_profile (
          id INTEGER PRIMARY KEY CHECK(id=1), name TEXT, admin_code TEXT, department TEXT,
          mobile TEXT, email TEXT, address TEXT);
        ''')
        if con.execute('SELECT COUNT(*) FROM complaints').fetchone()[0] == 0:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            con.executemany('INSERT INTO complaints(code,citizen,category,description,officer,status,remarks,created_at) VALUES(?,?,?,?,?,?,?,?)', [
              ('GC101','Ravi Kumar','Electricity','Street light not working','Officer Suresh','Pending','',now),
              ('GC102','Priya','Water','Water supply problem','Officer Ramesh','In Progress','',now),
              ('GC107','Arjun','Road','Road damaged near entrance','Officer Kumar','Pending','',now),
              ('GC110','Ramesh','Water','Pipeline leakage','Officer Suresh','Resolved','Repaired',now)])
        if con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            con.executemany('INSERT INTO users(code,name,mobile,role,village,status,created_at) VALUES(?,?,?,?,?,?,?)', [
              ('USR001','Ravi Kumar','9876543210','Citizen','Village A','Active',now),
              ('USR002','Priya','9876501234','Citizen','Village B','Active',now),
              ('OFF001','Officer Suresh','9876512345','Officer','Village A','Active',now),
              ('OFF002','Officer Ramesh','9876523456','Officer','Village B','Active',now)])
        if con.execute('SELECT COUNT(*) FROM services').fetchone()[0] == 0:
            con.executemany('INSERT INTO services(name,description,icon,status) VALUES(?,?,?,?)', [
              ('Water Supply','Report water supply problems, pipeline issues and related complaints.','💧','Active'),
              ('Electricity','Report street light and electricity related problems.','💡','Active'),
              ('Roads','Report damaged roads and infrastructure issues.','🛣️','Active'),
              ('Sanitation','Report waste collection and sanitation issues.','🧹','Active')])
        if con.execute('SELECT COUNT(*) FROM notifications').fetchone()[0] == 0:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            con.executemany('INSERT INTO notifications(title,message,kind,is_read,created_at) VALUES(?,?,?,?,?)', [
              ('New complaint received','A new citizen complaint needs review.','warning',0,now),
              ('Complaint resolved','A complaint has been marked as resolved.','success',0,now),
              ('System update','GramaSathi admin dashboard is ready.','info',1,now)])
        if con.execute('SELECT COUNT(*) FROM admin_profile').fetchone()[0] == 0:
            con.execute('INSERT INTO admin_profile VALUES(1,?,?,?,?,?,?)', ('Admin','ADM-1001','GramaSathi Administration','9876543210','admin@gramasathi.com','GramaSathi Administration Office'))

@app.get('/')
def index():
    return render_template('admindashboard.html')

@app.get('/api/dashboard')
def dashboard():
    with db() as con:
        total = con.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
        pending = con.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0]
        progress = con.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'").fetchone()[0]
        resolved = con.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0]
        users = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        services = con.execute('SELECT COUNT(*) FROM services').fetchone()[0]
        recent = [dict(r) for r in con.execute('SELECT * FROM complaints ORDER BY id DESC LIMIT 5')]
    return jsonify(total=total, pending=pending, progress=progress, resolved=resolved, users=users, services=services, recent=recent)

@app.route('/api/complaints', methods=['GET','POST'])
def complaints():
    if request.method == 'GET':
        with db() as con: rows = [dict(r) for r in con.execute('SELECT * FROM complaints ORDER BY id DESC')]
        return jsonify(rows)
    data = request.get_json(silent=True) or {}
    required = ['citizen','category','description']
    if any(not str(data.get(k,'')).strip() for k in required): return jsonify(error='Citizen, category and description are required.'), 400
    with db() as con:
        nextid = con.execute('SELECT COALESCE(MAX(id),100)+1 FROM complaints').fetchone()[0]
        code = 'GC' + str(nextid)
        con.execute('INSERT INTO complaints(code,citizen,category,description,officer,status,remarks,created_at) VALUES(?,?,?,?,?,?,?,?)',
          (code, data['citizen'].strip(), data['category'].strip(), data['description'].strip(), data.get('officer','').strip(), 'Pending','',datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    log_action('Complaint created', f'{code}: {data["category"]}')
    return jsonify(ok=True, code=code), 201

@app.patch('/api/complaints/<int:row_id>')
def update_complaint(row_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ['Pending','In Progress','Resolved']: return jsonify(error='Invalid complaint status.'), 400
    with db() as con:
        cur = con.execute('UPDATE complaints SET status=?, remarks=?, officer=? WHERE id=?', (status, data.get('remarks',''), data.get('officer',''), row_id))
        if not cur.rowcount: return jsonify(error='Complaint not found.'), 404
        row = dict(con.execute('SELECT * FROM complaints WHERE id=?',(row_id,)).fetchone())
    log_action('Complaint updated', f'{row["code"]} status: {status}')
    return jsonify(row)

@app.route('/api/users', methods=['GET','POST'])
def users():
    if request.method == 'GET':
        with db() as con: return jsonify([dict(r) for r in con.execute('SELECT * FROM users ORDER BY id DESC')])
    d = request.get_json(silent=True) or {}
    if any(not str(d.get(k,'')).strip() for k in ['name','mobile','role','village']): return jsonify(error='Please fill all user details.'), 400
    if d['role'] not in ['Citizen','Officer']: return jsonify(error='Invalid role.'), 400
    with db() as con:
        code = ('OFF' if d['role']=='Officer' else 'USR') + datetime.now().strftime('%H%M%S%f')[-8:]
        cur = con.execute('INSERT INTO users(code,name,mobile,role,village,status,created_at) VALUES(?,?,?,?,?,?,?)', (code,d['name'].strip(),d['mobile'].strip(),d['role'],d['village'].strip(),'Active',datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        row = dict(con.execute('SELECT * FROM users WHERE id=?',(cur.lastrowid,)).fetchone())
    log_action('User created', f'{row["name"]} ({row["role"]})')
    return jsonify(row), 201

@app.patch('/api/users/<int:row_id>')
def update_user(row_id):
    d = request.get_json(silent=True) or {}
    status = d.get('status')
    if status not in ['Active','Blocked']: return jsonify(error='Invalid user status.'), 400
    with db() as con:
        cur = con.execute('UPDATE users SET status=? WHERE id=?',(status,row_id))
        if not cur.rowcount: return jsonify(error='User not found.'),404
        row = dict(con.execute('SELECT * FROM users WHERE id=?',(row_id,)).fetchone())
    log_action('User status changed', f'{row["name"]}: {status}')
    return jsonify(row)

@app.route('/api/services', methods=['GET','POST'])
def services():
    if request.method == 'GET':
        with db() as con: return jsonify([dict(r) for r in con.execute('SELECT * FROM services ORDER BY id')])
    d = request.get_json(silent=True) or {}
    name = str(d.get('name','')).strip()
    if not name: return jsonify(error='Service name is required.'),400
    try:
        with db() as con:
            cur = con.execute('INSERT INTO services(name,description,icon,status) VALUES(?,?,?,?)',(name,str(d.get('description','')).strip(),d.get('icon','🛠️'),'Active'))
            row = dict(con.execute('SELECT * FROM services WHERE id=?',(cur.lastrowid,)).fetchone())
    except sqlite3.IntegrityError: return jsonify(error='A service with this name already exists.'),409
    log_action('Service created',name)
    return jsonify(row),201

@app.patch('/api/services/<int:row_id>')
def update_service(row_id):
    d = request.get_json(silent=True) or {}
    name = str(d.get('name','')).strip()
    if not name: return jsonify(error='Service name is required.'),400
    status = d.get('status','Active')
    if status not in ['Active','Inactive']: return jsonify(error='Invalid status.'),400
    try:
        with db() as con:
            cur = con.execute('UPDATE services SET name=?, description=?, status=? WHERE id=?',(name,str(d.get('description','')).strip(),status,row_id))
            if not cur.rowcount: return jsonify(error='Service not found.'),404
            row = dict(con.execute('SELECT * FROM services WHERE id=?',(row_id,)).fetchone())
    except sqlite3.IntegrityError: return jsonify(error='A service with this name already exists.'),409
    log_action('Service updated',name)
    return jsonify(row)

@app.route('/api/notifications', methods=['GET'])
def notifications():
    with db() as con: return jsonify([dict(r) for r in con.execute('SELECT * FROM notifications ORDER BY id DESC')])

@app.patch('/api/notifications/<int:row_id>')
def update_notification(row_id):
    d = request.get_json(silent=True) or {}
    with db() as con:
        if d.get('action') == 'delete':
            cur = con.execute('DELETE FROM notifications WHERE id=?',(row_id,))
            if not cur.rowcount: return jsonify(error='Notification not found.'),404
            log_action('Notification deleted',str(row_id)); return jsonify(ok=True)
        cur = con.execute('UPDATE notifications SET is_read=1 WHERE id=?',(row_id,))
        if not cur.rowcount: return jsonify(error='Notification not found.'),404
        row = dict(con.execute('SELECT * FROM notifications WHERE id=?',(row_id,)).fetchone())
    log_action('Notification read',row['title'])
    return jsonify(row)

@app.post('/api/notifications/read-all')
def read_all_notifications():
    with db() as con: con.execute('UPDATE notifications SET is_read=1')
    log_action('Notifications marked read','All notifications')
    return jsonify(ok=True)

@app.route('/api/profile', methods=['GET','PUT'])
def profile():
    if request.method == 'GET':
        with db() as con: return jsonify(dict(con.execute('SELECT name, admin_code AS id, department, mobile, email, address FROM admin_profile WHERE id=1').fetchone()))
    d = request.get_json(silent=True) or {}
    with db() as con:
        con.execute('UPDATE admin_profile SET name=?, admin_code=?, department=?, mobile=?, email=?, address=? WHERE id=1', (d.get('name',''),d.get('id',''),d.get('department',''),d.get('mobile',''),d.get('email',''),d.get('address','')))
    log_action('Admin profile updated','Profile details saved')
    return jsonify(ok=True)

@app.get('/api/activity')
def activity():
    with db() as con: return jsonify([dict(r) for r in con.execute('SELECT * FROM activity_log ORDER BY id DESC LIMIT 100')])

@app.get('/health')
def health(): return jsonify(status='ok')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
else:
    init_db()
