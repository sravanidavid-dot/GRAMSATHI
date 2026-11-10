import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import time
import secrets
import uuid
from threading import Lock
from pathlib import Path
from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(Path(__file__).resolve().parent / ".env")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# MYSQL DATABASE
# =========================================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "4000")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca=os.getenv("DB_SSL_CA"),
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        use_pure=True
    )


def get_db():
    try:
        return get_db_connection()
    except mysql.connector.Error as e:
        print("MySQL connection error:", e)
        return None


def serialize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def serialize_row(row):
    if not row:
        return row

    return {
        key: serialize_value(value)
        for key, value in row.items()
    }


# =========================================================
# NOTIFICATION HELPERS
# =========================================================

def create_notification(cursor, user_id, message):
    """
    Create one notification for one user.
    """

    if not user_id:
        return

    cursor.execute(
        """
        INSERT INTO notifications
        (
            user_id,
            message
        )
        VALUES
        (
            %s,
            %s
        )
        """,
        (
            int(user_id),
            message
        )
    )


def notify_role(cursor, role, message):
    """
    Notify every user having the specified role.
    """

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE role = %s
        """,
        (role,)
    )

    users = cursor.fetchall()

    for user in users:
        create_notification(
            cursor,
            user["id"],
            message
        )


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "GramaSathi Backend is running",
        "database": "MySQL",
        "server": "http://127.0.0.1:5001"
    })


# =========================================================
# TEST DATABASE
# =========================================================

@app.route("/api/test-db", methods=["GET"])
def test_db():

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500

        cursor = conn.cursor()

        cursor.execute(
            "SELECT DATABASE()"
        )

        database_name = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "MySQL connection successful",
            "database": database_name
        })

    except Error as e:

        return jsonify({
            "success": False,
            "message": "Database test failed",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "success": False,
            "message": "JSON request body is required"
        }), 400

    name = str(
        data.get("name") or ""
    ).strip()

    mobile = str(
        data.get("mobile") or ""
    ).strip()

    email = str(
        data.get("email") or ""
    ).strip().lower()

    village = str(
        data.get("village") or ""
    ).strip()

    password = str(
        data.get("password") or ""
    )

    # Public registration is restricted to Citizen accounts.
    # Admin and Officer accounts must be created securely.
    role = "citizen"


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400

    if not mobile:

        return jsonify({
            "success": False,
            "message": "Mobile number is required"
        }), 400

    if not mobile.isdigit() or len(mobile) != 10:

        return jsonify({
            "success": False,
            "message": "Enter a valid 10-digit mobile number"
        }), 400

    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    if not village:

        return jsonify({
            "success": False,
            "message": "Village is required"
        }), 400

    if len(password) < 8:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 8 characters"
        }), 400


    # -----------------------------------------------------
    # PASSWORD HASH
    # -----------------------------------------------------

    password_hash = generate_password_hash(
        password
    )


    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # CHECK MOBILE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE mobile = %s
            LIMIT 1
            """,
            (mobile,)
        )

        existing_mobile = cursor.fetchone()

        if existing_mobile:

            return jsonify({
                "success": False,
                "message": "Mobile number already registered"
            }), 409


        # -------------------------------------------------
        # CHECK EMAIL
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            (email,)
        )

        existing_email = cursor.fetchone()

        if existing_email:

            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409


        # -------------------------------------------------
        # INSERT USER
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                mobile,
                email,
                password,
                role,
                village
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                mobile,
                email,
                password_hash,
                role,
                village
            )
        )

        user_id = cursor.lastrowid

        conn.commit()


        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "name": name,
                "mobile": mobile,
                "email": email,
                "role": role,
                "village": village
            }
        }), 201


    except IntegrityError:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Mobile number or email is already registered"
        }), 409


    except Error as e:

        if conn:
            conn.rollback()

        app.logger.exception(
            "Registration database error"
        )

        return jsonify({
            "success": False,
            "message": "Unable to register user",
            "error": str(e)
        }), 500


    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Registration failed",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    start_time = time.perf_counter()

    conn = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}

        login_id = str(
            data.get("mobile")
            or data.get("email")
            or data.get("loginId")
            or data.get("login_id")
            or ""
        ).strip().lower()

        password = str(data.get("password", ""))

        if not login_id or not password:
            return jsonify({
                "success": False,
                "message": "Mobile/email and password are required"
            }), 400

        # 1. Database connection timing
        db_start = time.perf_counter()

        conn = get_db()

        db_seconds = time.perf_counter() - db_start

        print(
            f"[LOGIN TIMING] Database connection: {db_seconds:.3f} seconds",
            flush=True
        )

        if conn is None:
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500

        cursor = conn.cursor(dictionary=True)

        # 2. User search timing
        query_start = time.perf_counter()

        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                password,
                role,
                village,
                profile_image
            FROM users
            WHERE mobile = %s
               OR LOWER(email) = %s
            LIMIT 1
            """,
            (login_id, login_id)
        )

        user = cursor.fetchone()

        query_seconds = time.perf_counter() - query_start

        print(
            f"[LOGIN TIMING] User search: {query_seconds:.3f} seconds",
            flush=True
        )

        if user is None:
            return jsonify({
                "success": False,
                "message": "Invalid mobile/email or password"
            }), 401

        # 3. Password verification timing
        password_start = time.perf_counter()

        password_valid = check_password_hash(
            user["password"],
            password
        )

        password_seconds = time.perf_counter() - password_start

        print(
            f"[LOGIN TIMING] Password verification: {password_seconds:.3f} seconds",
            flush=True
        )

        if not password_valid:
            return jsonify({
                "success": False,
                "message": "Invalid mobile/email or password"
            }), 401

        user.pop("password", None)

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        })

    except Error as e:
        app.logger.exception("Login database error")

        return jsonify({
            "success": False,
            "message": "Login failed",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

        total_seconds = time.perf_counter() - start_time

        print(
            f"[LOGIN TIMING] TOTAL: {total_seconds:.3f} seconds",
            flush=True
        )

# =========================================================
# GET USER PROFILE
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                role,
                village,
                profile_image,
                created_at
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )


        user = cursor.fetchone()


        if user is None:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        return jsonify({
            "success": True,
            "user": serialize_row(user)
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load user",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# UPDATE USER PROFILE
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["PUT"])
def update_user(user_id):

    data = request.get_json(
        silent=True
    ) or {}


    name = str(
        data.get("name", "")
    ).strip()

    mobile = str(
        data.get("mobile", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower() or None

    village = str(
        data.get("village", "")
    ).strip()


    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400


    if not mobile:

        return jsonify({
            "success": False,
            "message": "Mobile number is required"
        }), 400


    if not mobile.isdigit() or len(mobile) != 10:

        return jsonify({
            "success": False,
            "message": "Enter a valid 10-digit mobile number"
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # CHECK USER
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                role
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        existing_user = cursor.fetchone()


        if existing_user is None:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        # -------------------------------------------------
        # DUPLICATE MOBILE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE mobile = %s
              AND id != %s
            LIMIT 1
            """,
            (
                mobile,
                user_id
            )
        )

        duplicate_mobile = cursor.fetchone()


        if duplicate_mobile:

            return jsonify({
                "success": False,
                "message": "Mobile number already used by another account"
            }), 409


        # -------------------------------------------------
        # DUPLICATE EMAIL
        # -------------------------------------------------

        if email:

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = %s
                  AND id != %s
                LIMIT 1
                """,
                (
                    email,
                    user_id
                )
            )

            duplicate_email = cursor.fetchone()


            if duplicate_email:

                return jsonify({
                    "success": False,
                    "message": "Email already used by another account"
                }), 409


        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                mobile = %s,
                email = %s,
                village = %s
            WHERE id = %s
            """,
            (
                name,
                mobile,
                email,
                village,
                user_id
            )
        )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        })


    except IntegrityError as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Mobile or email already exists",
            "error": str(e)
        }), 409


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update profile",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREATE COMPLAINT
# =========================================================

@app.route("/api/complaints", methods=["POST"])
def create_complaint():

    data = request.get_json(
        silent=True
    ) or {}


    user_id = data.get("user_id")

    title = str(
        data.get("title", "")
    ).strip()

    category = str(
        data.get("category", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    village = str(
        data.get("village", "")
    ).strip()

    location = str(
        data.get("location", "")
    ).strip()


    if not user_id:

        return jsonify({
            "success": False,
            "message": "User ID is required"
        }), 400


    try:
        user_id = int(user_id)
    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid user ID"
        }), 400


    if not title:

        return jsonify({
            "success": False,
            "message": "Complaint title is required"
        }), 400


    if not category:

        return jsonify({
            "success": False,
            "message": "Complaint category is required"
        }), 400


    if not description:

        return jsonify({
            "success": False,
            "message": "Complaint description is required"
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # GET CITIZEN
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                name,
                village,
                role
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if user is None:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        if user["role"] != "citizen":

            return jsonify({
                "success": False,
                "message": "Only citizens can submit complaints"
            }), 403


        if not village:

            village = user.get(
                "village"
            ) or ""


        # -------------------------------------------------
        # CREATE COMPLAINT ID
        # -------------------------------------------------

        complaint_id = (
            "GC"
            + uuid.uuid4().hex[:8].upper()
        )


        # -------------------------------------------------
        # INSERT COMPLAINT
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO complaints
            (
                complaint_id,
                user_id,
                title,
                category,
                description,
                village,
                location,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )
            """,
            (
                complaint_id,
                user_id,
                title,
                category,
                description,
                village,
                location
            )
        )


        database_complaint_id = cursor.lastrowid


        # -------------------------------------------------
        # CITIZEN NOTIFICATION
        # -------------------------------------------------

        create_notification(
            cursor,
            user_id,
            f"Complaint {complaint_id} submitted successfully."
        )


        # -------------------------------------------------
        # ADMIN NOTIFICATION
        # -------------------------------------------------

        notify_role(
            cursor,
            "admin",
            f"New complaint {complaint_id} has been submitted by a citizen."
        )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Complaint submitted successfully",
            "complaint": {
                "id": database_complaint_id,
                "complaint_id": complaint_id,
                "title": title,
                "category": category,
                "description": description,
                "village": village,
                "location": location,
                "status": "Pending"
            }
        }), 201


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to create complaint",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GET USER COMPLAINTS
# =========================================================

@app.route(
    "/api/complaints/user/<int:user_id>",
    methods=["GET"]
)
def get_user_complaints(user_id):

    status_filter = request.args.get(
        "status"
    )

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        query = """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                u.name AS officer_name
            FROM complaints c
            LEFT JOIN users u
                ON c.assigned_officer = u.id
            WHERE c.user_id = %s
        """

        params = [user_id]


        if status_filter:

            query += """
                AND c.status = %s
            """

            params.append(
                status_filter
            )


        query += """
            ORDER BY c.id DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        complaints = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(complaints),
            "complaints": [
                serialize_row(row)
                for row in complaints
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load complaints",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# USER DASHBOARD SUMMARY
# =========================================================

@app.route(
    "/api/dashboard/<int:user_id>",
    methods=["GET"]
)
def dashboard_summary(user_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_complaints,
                SUM(status = 'Pending') AS pending,
                SUM(status = 'In Progress') AS in_progress,
                SUM(status = 'Resolved') AS resolved
            FROM complaints
            WHERE user_id = %s
            """,
            (user_id,)
        )


        summary = cursor.fetchone()


        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                role,
                village,
                profile_image
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )


        user = cursor.fetchone()


        if user is None:

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404


        return jsonify({
            "success": True,
            "user": serialize_row(user),
            "summary": {
                "total_complaints": int(
                    summary["total_complaints"] or 0
                ),
                "pending": int(
                    summary["pending"] or 0
                ),
                "in_progress": int(
                    summary["in_progress"] or 0
                ),
                "resolved": int(
                    summary["resolved"] or 0
                )
            }
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load dashboard",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GET SINGLE COMPLAINT + HISTORY
# =========================================================

@app.route(
    "/api/complaints/<complaint_id>",
    methods=["GET"]
)
def get_complaint(complaint_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                citizen.name AS citizen_name,
                citizen.mobile AS citizen_mobile,
                officer.name AS officer_name
            FROM complaints c
            LEFT JOIN users citizen
                ON c.user_id = citizen.id
            LEFT JOIN users officer
                ON c.assigned_officer = officer.id
            WHERE c.complaint_id = %s
            LIMIT 1
            """,
            (complaint_id,)
        )


        complaint = cursor.fetchone()


        if complaint is None:

            return jsonify({
                "success": False,
                "message": "Complaint not found"
            }), 404


        cursor.execute(
            """
            SELECT
                h.id,
                h.status,
                h.note,
                h.updated_by,
                h.created_at
            FROM complaint_history h
            WHERE h.complaint_id = %s
            ORDER BY h.id ASC
            """,
            (complaint["id"],)
        )


        history = cursor.fetchall()


        complaint["history"] = [
            serialize_row(row)
            for row in history
        ]


        return jsonify({
            "success": True,
            "complaint": serialize_row(
                complaint
            )
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load complaint",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GENERIC COMPLAINT STATUS UPDATE
# =========================================================

@app.route(
    "/api/complaints/<complaint_id>/status",
    methods=["PUT"]
)
def update_complaint_status(complaint_id):

    data = request.get_json(
        silent=True
    ) or {}


    status = str(
        data.get("status", "")
    ).strip()

    note = str(
        data.get("note", "")
    ).strip()

    updated_by = data.get(
        "updated_by"
    )


    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]


    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid complaint status"
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                user_id,
                assigned_officer,
                status
            FROM complaints
            WHERE complaint_id = %s
            LIMIT 1
            """,
            (complaint_id,)
        )


        complaint = cursor.fetchone()


        if complaint is None:

            return jsonify({
                "success": False,
                "message": "Complaint not found"
            }), 404


        cursor.execute(
            """
            UPDATE complaints
            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (
                status,
                complaint_id
            )
        )


        history_note = (
            note
            or f"Complaint status changed to {status}"
        )


        cursor.execute(
            """
            INSERT INTO complaint_history
            (
                complaint_id,
                status,
                note,
                updated_by
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                complaint["id"],
                status,
                history_note,
                updated_by
            )
        )


        # Citizen notification
        create_notification(
            cursor,
            complaint["user_id"],
            f"Complaint {complaint_id} is now {status}."
        )


        # Admin notification
        notify_role(
            cursor,
            "admin",
            f"Complaint {complaint_id} is now {status}."
        )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Complaint status updated successfully",
            "complaint_id": complaint_id,
            "status": status
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update complaint status",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# GET NOTIFICATIONS
# =========================================================

@app.route(
    "/api/notifications/<int:user_id>",
    methods=["GET"]
)
def get_notifications(user_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                user_id,
                message,
                is_read,
                created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,)
        )


        notifications = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(notifications),
            "notifications": [
                serialize_row(row)
                for row in notifications
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load notifications",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# MARK NOTIFICATION AS READ
# =========================================================

@app.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["PUT"]
)
def mark_notification_read(notification_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s
            """,
            (notification_id,)
        )


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Notification not found"
            }), 404


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update notification",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - GET ALL COMPLAINTS
# =========================================================

@app.route(
    "/api/admin/complaints",
    methods=["GET"]
)
def admin_get_complaints():

    status_filter = request.args.get(
        "status"
    )

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        query = """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                citizen.name AS citizen_name,
                citizen.mobile AS citizen_mobile,
                officer.name AS officer_name
            FROM complaints c
            LEFT JOIN users citizen
                ON c.user_id = citizen.id
            LEFT JOIN users officer
                ON c.assigned_officer = officer.id
        """

        params = []


        if status_filter:

            query += """
                WHERE c.status = %s
            """

            params.append(
                status_filter
            )


        query += """
            ORDER BY c.id DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        complaints = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(complaints),
            "complaints": [
                serialize_row(row)
                for row in complaints
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load admin complaints",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - ASSIGN COMPLAINT TO OFFICER
# =========================================================

@app.route(
    "/api/admin/complaints/<complaint_id>/assign",
    methods=["PUT"]
)
def assign_complaint(complaint_id):

    data = request.get_json(
        silent=True
    ) or {}


    officer_id = data.get(
        "officer_id"
    )

    admin_id = data.get(
        "admin_id"
    )


    if not officer_id:

        return jsonify({
            "success": False,
            "message": "Officer ID is required"
        }), 400


    try:
        officer_id = int(
            officer_id
        )
    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid officer ID"
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # CHECK OFFICER
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                name,
                role
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (officer_id,)
        )


        officer = cursor.fetchone()


        if officer is None:

            return jsonify({
                "success": False,
                "message": "Officer not found"
            }), 404


        if officer["role"] != "officer":

            return jsonify({
                "success": False,
                "message": "Selected user is not an officer"
            }), 400


        # -------------------------------------------------
        # CHECK COMPLAINT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                assigned_officer,
                status
            FROM complaints
            WHERE complaint_id = %s
            LIMIT 1
            """,
            (complaint_id,)
        )


        complaint = cursor.fetchone()


        if complaint is None:

            return jsonify({
                "success": False,
                "message": "Complaint not found"
            }), 404


        # -------------------------------------------------
        # ASSIGN
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE complaints
            SET
                assigned_officer = %s,
                status = 'In Progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (
                officer_id,
                complaint_id
            )
        )


        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO complaint_history
            (
                complaint_id,
                status,
                note,
                updated_by
            )
            VALUES
            (
                %s,
                'In Progress',
                %s,
                %s
            )
            """,
            (
                complaint["id"],
                f"Complaint assigned to officer {officer['name']}",
                admin_id
            )
        )


        # -------------------------------------------------
        # CITIZEN NOTIFICATION
        # -------------------------------------------------

        create_notification(
            cursor,
            complaint["user_id"],
            f"Complaint {complaint_id} has been assigned to an officer."
        )


        # -------------------------------------------------
        # OFFICER NOTIFICATION
        # -------------------------------------------------

        create_notification(
            cursor,
            officer_id,
            f"Complaint {complaint_id} has been assigned to you."
        )


        # -------------------------------------------------
        # ADMIN NOTIFICATION
        # -------------------------------------------------

        if admin_id:

            create_notification(
                cursor,
                admin_id,
                f"Complaint {complaint_id} assigned to officer {officer['name']}."
            )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Complaint assigned successfully",
            "complaint_id": complaint_id,
            "officer_id": officer_id,
            "status": "In Progress"
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to assign complaint",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# OFFICER - GET ASSIGNED COMPLAINTS
# =========================================================

@app.route(
    "/api/officer/complaints/<int:officer_id>",
    methods=["GET"]
)
def officer_get_complaints(officer_id):

    status_filter = request.args.get(
        "status"
    )

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        query = """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                u.name AS citizen_name,
                u.mobile AS citizen_mobile
            FROM complaints c
            LEFT JOIN users u
                ON c.user_id = u.id
            WHERE c.assigned_officer = %s
        """

        params = [
            officer_id
        ]


        if status_filter:

            query += """
                AND c.status = %s
            """

            params.append(
                status_filter
            )


        query += """
            ORDER BY c.id DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        complaints = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(complaints),
            "complaints": [
                serialize_row(row)
                for row in complaints
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load officer complaints",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# OFFICER - UPDATE COMPLAINT STATUS
# =========================================================

@app.route(
    "/api/officer/complaints/<complaint_id>/status",
    methods=["PUT"]
)
def officer_update_status(complaint_id):

    data = request.get_json(
        silent=True
    ) or {}


    officer_id = data.get(
        "officer_id"
    )

    status = str(
        data.get("status", "")
    ).strip()

    resolution_note = str(
        data.get("resolution_note", "")
    ).strip()


    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]


    if not officer_id:

        return jsonify({
            "success": False,
            "message": "Officer ID is required"
        }), 400


    try:
        officer_id = int(
            officer_id
        )
    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid officer ID"
        }), 400


    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid status"
        }), 400


    if status == "Resolved" and not resolution_note:

        return jsonify({
            "success": False,
            "message": "Resolution note is required when resolving a complaint"
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # GET COMPLAINT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                assigned_officer,
                status
            FROM complaints
            WHERE complaint_id = %s
            LIMIT 1
            """,
            (complaint_id,)
        )


        complaint = cursor.fetchone()


        if complaint is None:

            return jsonify({
                "success": False,
                "message": "Complaint not found"
            }), 404


        # -------------------------------------------------
        # VERIFY OFFICER
        # -------------------------------------------------

        if complaint["assigned_officer"] != officer_id:

            return jsonify({
                "success": False,
                "message": "This complaint is not assigned to this officer"
            }), 403


        # -------------------------------------------------
        # UPDATE COMPLAINT
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE complaints
            SET
                status = %s,
                resolution_note = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
              AND assigned_officer = %s
            """,
            (
                status,
                resolution_note
                if status == "Resolved"
                else None,
                complaint_id,
                officer_id
            )
        )


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Complaint update failed"
            }), 400


        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        if status == "Resolved":

            history_note = (
                resolution_note
                or "Complaint resolved by officer"
            )

        else:

            history_note = (
                f"Officer updated status to {status}"
            )


        cursor.execute(
            """
            INSERT INTO complaint_history
            (
                complaint_id,
                status,
                note,
                updated_by
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                complaint["id"],
                status,
                history_note,
                officer_id
            )
        )


        # -------------------------------------------------
        # CITIZEN NOTIFICATION
        # -------------------------------------------------

        create_notification(
            cursor,
            complaint["user_id"],
            f"Complaint {complaint_id} is now {status}."
        )


        # -------------------------------------------------
        # ADMIN NOTIFICATION
        # -------------------------------------------------

        notify_role(
            cursor,
            "admin",
            f"Complaint {complaint_id} is now {status}."
        )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Complaint updated successfully",
            "complaint_id": complaint_id,
            "status": status,
            "resolution_note": resolution_note
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update complaint",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ANNOUNCEMENTS - GET ALL
# =========================================================

@app.route(
    "/api/announcements",
    methods=["GET"]
)
def get_announcements():

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                a.id,
                a.title,
                a.message,
                a.category,
                a.created_by,
                a.created_at,
                u.name AS creator_name
            FROM announcements a
            LEFT JOIN users u
                ON a.created_by = u.id
            ORDER BY a.id DESC
            """
        )


        announcements = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(announcements),
            "announcements": [
                serialize_row(row)
                for row in announcements
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load announcements",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - CREATE ANNOUNCEMENT
# =========================================================

@app.route(
    "/api/admin/announcements",
    methods=["POST"]
)
def create_announcement():

    data = request.get_json(
        silent=True
    ) or {}


    title = str(
        data.get("title", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    category = str(
        data.get(
            "category",
            "General"
        )
    ).strip()

    created_by = data.get(
        "created_by"
    )


    if not title:

        return jsonify({
            "success": False,
            "message": "Announcement title is required"
        }), 400


    if not message:

        return jsonify({
            "success": False,
            "message": "Announcement message is required"
        }), 400


    if not category:
        category = "General"


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # VERIFY ADMIN
        # -------------------------------------------------

        if created_by:

            try:
                created_by = int(
                    created_by
                )
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message": "Invalid admin ID"
                }), 400


            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    role
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (created_by,)
            )


            admin = cursor.fetchone()


            if admin is None:

                return jsonify({
                    "success": False,
                    "message": "Admin user not found"
                }), 404


            if admin["role"] != "admin":

                return jsonify({
                    "success": False,
                    "message": "Only admin can create announcements"
                }), 403


        # -------------------------------------------------
        # INSERT ANNOUNCEMENT
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO announcements
            (
                title,
                message,
                category,
                created_by
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                title,
                message,
                category,
                created_by
            )
        )


        announcement_id = cursor.lastrowid


        notification_message = (
            f"New announcement: {title}"
        )


        # -------------------------------------------------
        # CITIZENS
        # -------------------------------------------------

        notify_role(
            cursor,
            "citizen",
            notification_message
        )


        # -------------------------------------------------
        # OFFICERS
        # -------------------------------------------------

        notify_role(
            cursor,
            "officer",
            notification_message
        )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Announcement created successfully",
            "announcement": {
                "id": announcement_id,
                "title": title,
                "message": message,
                "category": category,
                "created_by": created_by
            }
        }), 201


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to create announcement",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - DELETE ANNOUNCEMENT
# =========================================================

@app.route(
    "/api/admin/announcements/<int:announcement_id>",
    methods=["DELETE"]
)
def delete_announcement(announcement_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor()


        cursor.execute(
            """
            DELETE FROM announcements
            WHERE id = %s
            """,
            (announcement_id,)
        )


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Announcement not found"
            }), 404


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Announcement deleted successfully"
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to delete announcement",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN DASHBOARD SUMMARY
# =========================================================

@app.route(
    "/api/admin/dashboard",
    methods=["GET"]
)
def admin_dashboard():

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM complaints
            """
        )

        total = cursor.fetchone()[
            "total"
        ]


        cursor.execute(
            """
            SELECT COUNT(*) AS pending
            FROM complaints
            WHERE status = 'Pending'
            """
        )

        pending = cursor.fetchone()[
            "pending"
        ]


        cursor.execute(
            """
            SELECT COUNT(*) AS in_progress
            FROM complaints
            WHERE status = 'In Progress'
            """
        )

        in_progress = cursor.fetchone()[
            "in_progress"
        ]


        cursor.execute(
            """
            SELECT COUNT(*) AS resolved
            FROM complaints
            WHERE status = 'Resolved'
            """
        )

        resolved = cursor.fetchone()[
            "resolved"
        ]


        cursor.execute(
            """
            SELECT COUNT(*) AS citizens
            FROM users
            WHERE role = 'citizen'
            """
        )

        citizens = cursor.fetchone()[
            "citizens"
        ]


        cursor.execute(
            """
            SELECT COUNT(*) AS officers
            FROM users
            WHERE role = 'officer'
            """
        )

        officers = cursor.fetchone()[
            "officers"
        ]


        return jsonify({
            "success": True,
            "summary": {
                "total_complaints": int(
                    total or 0
                ),
                "pending": int(
                    pending or 0
                ),
                "in_progress": int(
                    in_progress or 0
                ),
                "resolved": int(
                    resolved or 0
                ),
                "citizens": int(
                    citizens or 0
                ),
                "officers": int(
                    officers or 0
                )
            }
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load admin dashboard",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - GET OFFICERS
# =========================================================

@app.route(
    "/api/admin/officers",
    methods=["GET"]
)
def get_officers():

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                village,
                created_at
            FROM users
            WHERE role = 'officer'
            ORDER BY name ASC
            """
        )


        officers = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(officers),
            "officers": [
                serialize_row(row)
                for row in officers
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load officers",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN - GET CITIZENS
# =========================================================

@app.route(
    "/api/admin/citizens",
    methods=["GET"]
)
def get_citizens():

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                name,
                mobile,
                email,
                village,
                created_at
            FROM users
            WHERE role = 'citizen'
            ORDER BY id DESC
            """
        )


        citizens = cursor.fetchall()


        return jsonify({
            "success": True,
            "count": len(citizens),
            "citizens": [
                serialize_row(row)
                for row in citizens
            ]
        })


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load citizens",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# FORGOT PASSWORD / OTP
# =========================================================

otp_storage = {}
reset_tokens = {}

otp_lock = Lock()

OTP_EXPIRY = 300
RESET_TOKEN_EXPIRY = 300
MAX_OTP_ATTEMPTS = 5


def normalize_contact(contact):

    return str(
        contact or ""
    ).strip().lower()


def valid_contact(contact):

    email_valid = re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        contact
    )

    phone_valid = re.fullmatch(
        r"\+?\d{10,15}",
        contact
    )

    return bool(
        email_valid
        or phone_valid
    )


def valid_password(password):

    return (
        len(password) >= 8
        and re.search(
            r"[A-Z]",
            password
        )
        and re.search(
            r"[0-9]",
            password
        )
        and re.search(
            r"[^A-Za-z0-9]",
            password
        )
    )


# =========================================================
# SEND OTP
# =========================================================

@app.route(
    "/api/forgot-password/send-otp",
    methods=["POST"]
)
def send_forgot_password_otp():

    data = request.get_json(
        silent=True
    ) or {}


    contact = normalize_contact(
        data.get("contact")
    )


    if not valid_contact(contact):

        return jsonify({
            "success": False,
            "message": "Enter a valid mobile number or email."
        }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
               OR mobile = %s
            LIMIT 1
            """,
            (
                contact,
                contact
            )
        )


        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "No account found with this mobile number or email."
            }), 404


        otp = f"{secrets.randbelow(1000000):06d}"


        with otp_lock:

            otp_storage[contact] = {
                "otp": otp,
                "expires": time.time()
                + OTP_EXPIRY,
                "attempts": 0
            }


            for token, record in list(
                reset_tokens.items()
            ):

                if record["contact"] == contact:

                    reset_tokens.pop(
                        token,
                        None
                    )


        # Development OTP
        app.logger.warning(
            "Development OTP generated for %s: %s",
            contact,
            otp
        )


        return jsonify({
            "success": True,
            "message": "OTP generated. Check backend terminal for testing.",
            "expires_in": OTP_EXPIRY
        }), 200


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Database error while sending OTP.",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# VERIFY OTP
# =========================================================

@app.route(
    "/api/forgot-password/verify-otp",
    methods=["POST"]
)
def verify_forgot_password_otp():

    data = request.get_json(
        silent=True
    ) or {}


    contact = normalize_contact(
        data.get("contact")
    )

    entered_otp = str(
        data.get("otp", "")
    ).strip()


    if not contact or not re.fullmatch(
        r"\d{6}",
        entered_otp
    ):

        return jsonify({
            "success": False,
            "message": "Enter a valid 6-digit OTP."
        }), 400


    with otp_lock:

        record = otp_storage.get(
            contact
        )


        if not record:

            return jsonify({
                "success": False,
                "message": "Request an OTP first."
            }), 400


        if time.time() > record["expires"]:

            otp_storage.pop(
                contact,
                None
            )

            return jsonify({
                "success": False,
                "message": "OTP expired. Request a new one."
            }), 400


        if record["attempts"] >= MAX_OTP_ATTEMPTS:

            otp_storage.pop(
                contact,
                None
            )

            return jsonify({
                "success": False,
                "message": "Too many attempts. Request a new OTP."
            }), 429


        record["attempts"] += 1


        if not secrets.compare_digest(
            entered_otp,
            record["otp"]
        ):

            return jsonify({
                "success": False,
                "message": "Incorrect OTP."
            }), 400


        otp_storage.pop(
            contact,
            None
        )


        reset_token = secrets.token_urlsafe(
            32
        )


        reset_tokens[reset_token] = {
            "contact": contact,
            "expires": time.time()
            + RESET_TOKEN_EXPIRY
        }


    return jsonify({
        "success": True,
        "message": "OTP verified successfully.",
        "reset_token": reset_token,
        "expires_in": RESET_TOKEN_EXPIRY
    }), 200


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/api/forgot-password/reset-password",
    methods=["POST"]
)
def reset_forgotten_password():

    data = request.get_json(
        silent=True
    ) or {}


    reset_token = str(
        data.get("reset_token", "")
    ).strip()

    new_password = str(
        data.get("new_password", "")
    )

    confirm_password = str(
        data.get("confirm_password", "")
    )


    if not reset_token:

        return jsonify({
            "success": False,
            "message": "Reset token is missing. Please verify OTP again."
        }), 400


    if not valid_password(
        new_password
    ):

        return jsonify({
            "success": False,
            "message": (
                "Password must contain at least 8 characters, "
                "one uppercase letter, one number, "
                "and one special character."
            )
        }), 400


    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400


    with otp_lock:

        token_record = reset_tokens.get(
            reset_token
        )


        if not token_record:

            return jsonify({
                "success": False,
                "message": "Invalid or expired reset token. Please verify OTP again."
            }), 400


        if time.time() > token_record["expires"]:

            reset_tokens.pop(
                reset_token,
                None
            )

            return jsonify({
                "success": False,
                "message": "Reset token has expired. Please verify OTP again."
            }), 400


        contact = token_record[
            "contact"
        ]


    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id,
                role
            FROM users
            WHERE LOWER(email) = %s
               OR mobile = %s
            LIMIT 1
            """,
            (
                contact,
                contact
            )
        )


        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "message": "No account found with this mobile number or email."
            }), 404


        password_hash = generate_password_hash(
            new_password
        )


        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (
                password_hash,
                user["id"]
            )
        )


        if cursor.rowcount != 1:

            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Password could not be updated."
            }), 500


        conn.commit()


        with otp_lock:

            reset_tokens.pop(
                reset_token,
                None
            )


        return jsonify({
            "success": True,
            "message": "Password reset successfully.",
            "user_id": user["id"],
            "role": user["role"]
        }), 200


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Database error while resetting password.",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - GET ALL COMPLAINTS
# =========================================================

@app.route(
    "/api/complaints",
    methods=["GET"]
)
def get_all_complaints_compat():

    status_filter = request.args.get(
        "status"
    )

    conn = None
    cursor = None

    try:

        conn = get_db()

        if conn is None:

            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500


        cursor = conn.cursor(
            dictionary=True
        )


        query = """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                u.name AS citizen_name,
                u.mobile AS citizen_mobile,
                o.name AS officer_name
            FROM complaints c
            LEFT JOIN users u
                ON c.user_id = u.id
            LEFT JOIN users o
                ON c.assigned_officer = o.id
        """


        params = []


        if status_filter:

            query += """
                WHERE c.status = %s
            """

            params.append(
                status_filter
            )


        query += """
            ORDER BY c.id DESC
        """


        cursor.execute(
            query,
            tuple(params)
        )


        rows = cursor.fetchall()


        return jsonify([
            serialize_row(row)
            for row in rows
        ])


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load complaints",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - RESOLVED COMPLAINTS
# =========================================================

@app.route(
    "/api/complaints/resolved",
    methods=["GET"]
)
def get_resolved_complaints_compat():

    conn = None
    cursor = None

    try:

        conn = get_db()

        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                c.id,
                c.complaint_id,
                c.user_id,
                c.title,
                c.category,
                c.description,
                c.village,
                c.location,
                c.status,
                c.assigned_officer,
                c.resolution_note,
                c.created_at,
                c.updated_at,
                u.name AS citizen_name,
                o.name AS officer_name
            FROM complaints c
            LEFT JOIN users u
                ON c.user_id = u.id
            LEFT JOIN users o
                ON c.assigned_officer = o.id
            WHERE c.status = 'Resolved'
            ORDER BY c.updated_at DESC, c.id DESC
            """
        )


        rows = cursor.fetchall()


        return jsonify([
            serialize_row(row)
            for row in rows
        ])


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load resolved complaints",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - GET OFFICERS
# =========================================================

@app.route(
    "/api/officers",
    methods=["GET"]
)
def get_officers_compat():

    conn = None
    cursor = None

    try:

        conn = get_db()

        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id AS officer_id,
                id,
                name,
                email,
                mobile AS phone,
                village,
                created_at
            FROM users
            WHERE role = 'officer'
            ORDER BY name ASC
            """
        )


        return jsonify([
            serialize_row(row)
            for row in cursor.fetchall()
        ])


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load officers",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - OFFICER PROFILE GET
# =========================================================

@app.route(
    "/api/officers/<int:officer_id>/profile",
    methods=["GET"]
)
def get_officer_profile_compat(officer_id):

    conn = None
    cursor = None

    try:

        conn = get_db()

        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                id AS officer_id,
                id,
                name,
                email,
                mobile AS phone,
                village,
                profile_image,
                created_at
            FROM users
            WHERE id = %s
              AND role = 'officer'
            LIMIT 1
            """,
            (officer_id,)
        )


        officer = cursor.fetchone()


        if not officer:

            return jsonify({
                "success": False,
                "message": "Officer not found"
            }), 404


        return jsonify(
            serialize_row(officer)
        )


    except Error as e:

        return jsonify({
            "success": False,
            "message": "Failed to load officer profile",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - OFFICER PROFILE UPDATE
# =========================================================

@app.route(
    "/api/officers/<int:officer_id>/profile",
    methods=["PUT"]
)
def update_officer_profile_compat(
    officer_id
):

    data = request.get_json(
        silent=True
    ) or {}


    allowed = [
        "name",
        "email",
        "mobile",
        "village"
    ]


    updates = {
        key: data[key]
        for key in allowed
        if key in data
    }


    if not updates:

        return jsonify({
            "success": False,
            "message": "No profile fields supplied"
        }), 400


    if "name" in updates:

        if not str(
            updates["name"]
        ).strip():

            return jsonify({
                "success": False,
                "message": "name cannot be empty"
            }), 400


    if "mobile" in updates:

        mobile = str(
            updates["mobile"]
        ).strip()


        if (
            not mobile.isdigit()
            or len(mobile) != 10
        ):

            return jsonify({
                "success": False,
                "message": "Enter a valid 10-digit mobile number"
            }), 400


        updates["mobile"] = mobile


    if "email" in updates:

        updates["email"] = str(
            updates["email"]
        ).strip().lower()


    conn = None
    cursor = None

    try:

        conn = get_db()

        cursor = conn.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
              AND role = 'officer'
            """,
            (officer_id,)
        )


        if not cursor.fetchone():

            return jsonify({
                "success": False,
                "message": "Officer not found"
            }), 404


        # -------------------------------------------------
        # MOBILE DUPLICATE
        # -------------------------------------------------

        if "mobile" in updates:

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE mobile = %s
                  AND id != %s
                LIMIT 1
                """,
                (
                    updates["mobile"],
                    officer_id
                )
            )


            if cursor.fetchone():

                return jsonify({
                    "success": False,
                    "message": "Mobile number already used"
                }), 409


        # -------------------------------------------------
        # EMAIL DUPLICATE
        # -------------------------------------------------

        if "email" in updates:

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                  AND id != %s
                LIMIT 1
                """,
                (
                    updates["email"],
                    officer_id
                )
            )


            if cursor.fetchone():

                return jsonify({
                    "success": False,
                    "message": "Email already used"
                }), 409


        fields = []
        values = []


        for key, value in updates.items():

            fields.append(
                f"`{key}` = %s"
            )

            values.append(
                str(value).strip()
                if value is not None
                else None
            )


        cursor.execute(
            f"""
            UPDATE users
            SET {', '.join(fields)}
            WHERE id = %s
            """,
            tuple(values)
            + (officer_id,)
        )


        conn.commit()


        cursor.execute(
            """
            SELECT
                id AS officer_id,
                id,
                name,
                email,
                mobile AS phone,
                village,
                profile_image,
                created_at
            FROM users
            WHERE id = %s
            """,
            (officer_id,)
        )


        profile = cursor.fetchone()


        return jsonify({
            "success": True,
            "message": "Officer profile saved successfully",
            "profile": serialize_row(
                profile
            )
        })


    except IntegrityError:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Mobile or email already exists"
        }), 409


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to save officer profile",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPATIBILITY - ASSIGN COMPLAINT
# =========================================================

@app.route(
    "/api/complaints/<complaint_id>/assign",
    methods=["PUT"]
)
def assign_complaint_compat(
    complaint_id
):

    data = request.get_json(
        silent=True
    ) or {}


    officer_id = data.get(
        "officer_id"
    )

    admin_id = data.get(
        "admin_id"
    )


    if officer_id in (
        None,
        ""
    ):

        officer_id = None

    else:

        try:

            officer_id = int(
                officer_id
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "success": False,
                "message": "Invalid officer_id"
            }), 400


    conn = None
    cursor = None

    try:

        conn = get_db()

        cursor = conn.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # GET COMPLAINT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                assigned_officer,
                status
            FROM complaints
            WHERE complaint_id = %s
            LIMIT 1
            """,
            (complaint_id,)
        )


        complaint = cursor.fetchone()


        if not complaint:

            return jsonify({
                "success": False,
                "message": "Complaint not found"
            }), 404


        officer = None


        # -------------------------------------------------
        # CHECK OFFICER
        # -------------------------------------------------

        if officer_id is not None:

            cursor.execute(
                """
                SELECT
                    id,
                    name
                FROM users
                WHERE id = %s
                  AND role = 'officer'
                LIMIT 1
                """,
                (officer_id,)
            )


            officer = cursor.fetchone()


            if not officer:

                return jsonify({
                    "success": False,
                    "message": "Officer not found"
                }), 404


        # -------------------------------------------------
        # UPDATE ASSIGNMENT
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE complaints
            SET
                assigned_officer = %s,
                status = CASE
                    WHEN %s IS NULL THEN status
                    WHEN status = 'Pending'
                        THEN 'In Progress'
                    ELSE status
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (
                officer_id,
                officer_id,
                complaint_id
            )
        )


        # -------------------------------------------------
        # NOTIFICATIONS
        # -------------------------------------------------

        if officer_id is not None:

            create_notification(
                cursor,
                complaint["user_id"],
                f"Complaint {complaint_id} has been assigned to an officer."
            )


            create_notification(
                cursor,
                officer_id,
                f"Complaint {complaint_id} has been assigned to you."
            )


            if admin_id:

                create_notification(
                    cursor,
                    admin_id,
                    f"Complaint {complaint_id} assigned to officer {officer['name']}."
                )


        conn.commit()


        return jsonify({
            "success": True,
            "message": "Complaint assignment updated successfully",
            "complaint_id": complaint_id,
            "assigned_officer_id": officer_id
        })


    except Error as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to assign complaint",
            "error": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# SERVER START
# =========================================================

if __name__ == "__main__":

    connection = get_db()


    if connection:

        connection.close()

        print("---------------------------------------")
        print("      GRAMASATHI UNIFIED BACKEND")
        print("---------------------------------------")
        print("Database : MySQL / gramasathi")
        print("Server   : http://127.0.0.1:5001")
        print("Features :")
        print("           Login")
        print("           Register")
        print("           Profile")
        print("           Complaints")
        print("           Complaint History")
        print("           Admin Assignment")
        print("           Officer Status Update")
        print("           Notifications")
        print("           Announcements")
        print("           OTP / Password Reset")
        print("           Citizen / Admin / Officer")
        print("---------------------------------------")


        app.run(
            host="127.0.0.1",
            port=5001,
            debug=True
        )


    else:

        print("---------------------------------------")
        print("      GRAMASATHI BACKEND ERROR")
        print("---------------------------------------")
        print("MySQL connection failed.")
        print("Check MySQL server and .env settings.")
        print("---------------------------------------")
