from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "gramasathi.db")

# Frontend folder
FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "Frontend")
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # ---------------- USERS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            mobile TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT DEFAULT 'citizen',

            village TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- COMPLAINTS ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            complaint_id TEXT UNIQUE NOT NULL,

            user_id INTEGER NOT NULL,

            category TEXT NOT NULL,

            description TEXT,

            village TEXT,

            location TEXT,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "GramaSathi Backend is running",
        "server": "Flask",
        "database": "SQLite",
        "port": 5001
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name", "").strip()
    mobile = data.get("mobile", "").strip()
    password = data.get("password", "")
    village = data.get("village", "").strip()

    if not name or not mobile or not password:

        return jsonify({
            "success": False,
            "message": "Name, mobile and password are required"
        }), 400

    hashed_password = generate_password_hash(password)

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, mobile, password, role, village)

            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            mobile,
            hashed_password,
            "citizen",
            village
        ))

        conn.commit()

        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user_id": user_id
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Mobile number already registered"
        }), 409

    finally:

        conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    mobile = data.get("mobile", "").strip()
    password = data.get("password", "")

    if not mobile or not password:

        return jsonify({
            "success": False,
            "message": "Mobile and password are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE mobile = ?
    """, (mobile,))

    user = cursor.fetchone()

    conn.close()

    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid mobile number or password"
        }), 401

    if not check_password_hash(user["password"], password):

        return jsonify({
            "success": False,
            "message": "Invalid mobile number or password"
        }), 401

    return jsonify({

        "success": True,

        "message": "Login successful",

        "user": {

            "id": user["id"],
            "name": user["name"],
            "mobile": user["mobile"],
            "role": user["role"],
            "village": user["village"]

        }

    })


# =========================================================
# GET USER
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, mobile, role, village, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    if user is None:

        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    return jsonify({
        "success": True,
        "user": dict(user)
    })


# =========================================================
# CREATE COMPLAINT
# =========================================================

@app.route("/api/complaints", methods=["POST"])
def create_complaint():

    data = request.get_json()

    user_id = data.get("user_id")
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    village = data.get("village", "").strip()
    location = data.get("location", "").strip()

    if not user_id or not category:

        return jsonify({
            "success": False,
            "message": "User ID and complaint category are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    # Generate complaint ID
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM complaints
    """)

    total = cursor.fetchone()["total"]

    complaint_id = f"GC{total + 1:03d}"

    cursor.execute("""
        INSERT INTO complaints
        (
            complaint_id,
            user_id,
            category,
            description,
            village,
            location,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        user_id,
        category,
        description,
        village,
        location,
        "Pending"
    ))

    conn.commit()

    complaint_db_id = cursor.lastrowid

    conn.close()

    return jsonify({

        "success": True,

        "message": "Complaint submitted successfully",

        "complaint": {

            "id": complaint_db_id,
            "complaint_id": complaint_id,
            "status": "Pending"

        }

    }), 201


# =========================================================
# GET ALL USER COMPLAINTS
# =========================================================

@app.route("/api/complaints/user/<int:user_id>", methods=["GET"])
def get_user_complaints(user_id):

    status = request.args.get("status")

    conn = get_db()
    cursor = conn.cursor()

    if status:

        cursor.execute("""
            SELECT *
            FROM complaints
            WHERE user_id = ?
            AND status = ?
            ORDER BY id DESC
        """, (user_id, status))

    else:

        cursor.execute("""
            SELECT *
            FROM complaints
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

    complaints = cursor.fetchall()

    conn.close()

    return jsonify({

        "success": True,

        "count": len(complaints),

        "complaints": [
            dict(complaint)
            for complaint in complaints
        ]

    })


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):

    conn = get_db()
    cursor = conn.cursor()

    # Total
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE user_id = ?
    """, (user_id,))

    total = cursor.fetchone()["count"]

    # Pending
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE user_id = ?
        AND status = 'Pending'
    """, (user_id,))

    pending = cursor.fetchone()["count"]

    # In Progress
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE user_id = ?
        AND status = 'In Progress'
    """, (user_id,))

    in_progress = cursor.fetchone()["count"]

    # Resolved
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE user_id = ?
        AND status = 'Resolved'
    """, (user_id,))

    resolved = cursor.fetchone()["count"]

    # Recent complaints
    cursor.execute("""
        SELECT
            complaint_id,
            category,
            description,
            village,
            status,
            created_at,
            updated_at

        FROM complaints

        WHERE user_id = ?

        ORDER BY id DESC

        LIMIT 5
    """, (user_id,))

    recent = cursor.fetchall()

    conn.close()

    return jsonify({

        "success": True,

        "summary": {

            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved

        },

        "recent_complaints": [

            dict(item)
            for item in recent

        ]

    })


# =========================================================
# UPDATE COMPLAINT STATUS
# =========================================================

@app.route("/api/complaints/<complaint_id>/status", methods=["PUT"])
def update_complaint_status(complaint_id):

    data = request.get_json()

    status = data.get("status", "").strip()

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:

        return jsonify({

            "success": False,

            "message": "Invalid status"

        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints

        SET
            status = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE complaint_id = ?
    """, (
        status,
        complaint_id
    ))

    conn.commit()

    if cursor.rowcount == 0:

        conn.close()

        return jsonify({

            "success": False,

            "message": "Complaint not found"

        }), 404

    conn.close()

    return jsonify({

        "success": True,

        "message": "Complaint status updated"

    })


# =========================================================
# GET SINGLE COMPLAINT
# =========================================================

@app.route("/api/complaints/<complaint_id>", methods=["GET"])
def get_complaint(complaint_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,))

    complaint = cursor.fetchone()

    conn.close()

    if complaint is None:

        return jsonify({

            "success": False,

            "message": "Complaint not found"

        }), 404

    return jsonify({

        "success": True,

        "complaint": dict(complaint)

    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    init_db()

    print("---------------------------------------")
    print("      GRAMASATHI BACKEND SERVER")
    print("---------------------------------------")
    print("Database :", DATABASE)
    print("Server   : http://127.0.0.1:5001")
    print("---------------------------------------")

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )