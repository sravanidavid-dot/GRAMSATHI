from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os
import re
import time
import secrets
from threading import Lock
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")
app = Flask(__name__)
CORS(app)


# ==================== DATABASE ====================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "gramsathi_user"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "gramsathi_db")
    )


def get_columns(cursor, table):
    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
    return {row["Field"] for row in cursor.fetchall()}


def serialize(row):
    if not row:
        return row

    for key, value in row.items():
        if hasattr(value, "isoformat"):
            row[key] = value.isoformat()

    return row


def close_db(conn=None, cursor=None):
    if cursor:
        cursor.close()

    if conn and conn.is_connected():
        conn.close()


def error(message, code=400):
    return jsonify({"error": message}), code


# ==================== HOME ====================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "GramSathi Backend is running!"
    })


# ==================== DASHBOARD COUNTS ====================

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT status, COUNT(*) AS total
            FROM complaints
            GROUP BY status
        """)

        rows = cursor.fetchall()

        counts = {
            "Pending": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Rejected": 0
        }

        for row in rows:
            if row["status"] in counts:
                counts[row["status"]] = row["total"]

        counts["total"] = sum(counts.values())

        return jsonify(counts)

    except mysql.connector.Error:
        app.logger.exception("Dashboard API failed")
        return error("Unable to fetch dashboard data", 500)

    finally:
        close_db(conn, cursor)


# ==================== GET ALL COMPLAINTS ====================

@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        columns = get_columns(cursor, "complaints")

        preferred_columns = [
            "complaint_id",
            "title",
            "description",
            "category",
            "location",
            "citizen_name",
            "citizen_phone",
            "status",
            "assigned_officer_id",
            "created_at",
            "updated_at"
        ]

        selected = [
            col for col in preferred_columns
            if col in columns
        ]

        if not selected:
            return error("No supported complaint columns found", 500)

        query = "SELECT " + ", ".join(
            f"`{col}`" for col in selected
        ) + " FROM complaints"

        params = []
        officer_id = request.args.get("officer_id")

        if officer_id is not None:
            try:
                officer_id = int(officer_id)

                if officer_id <= 0:
                    raise ValueError

            except ValueError:
                return error(
                    "officer_id must be a positive integer",
                    400
                )

            if "assigned_officer_id" not in columns:
                return error(
                    "Officer assignment column is unavailable",
                    400
                )

            query += " WHERE assigned_officer_id = %s"
            params.append(officer_id)

        if "created_at" in columns:
            query += " ORDER BY created_at DESC"
        else:
            query += " ORDER BY complaint_id DESC"

        cursor.execute(query, tuple(params))
        complaints = cursor.fetchall()

        return jsonify([
            serialize(row) for row in complaints
        ])

    except mysql.connector.Error:
        app.logger.exception("Get complaints failed")
        return error("Unable to fetch complaints", 500)

    finally:
        close_db(conn, cursor)


# ==================== GET SINGLE COMPLAINT ====================

@app.route("/api/complaints/<int:complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM complaints
            WHERE complaint_id = %s
        """, (complaint_id,))

        complaint = cursor.fetchone()

        if not complaint:
            return error("Complaint not found", 404)

        return jsonify(serialize(complaint))

    except mysql.connector.Error:
        app.logger.exception("Get complaint failed")
        return error("Unable to fetch complaint", 500)

    finally:
        close_db(conn, cursor)


# ==================== CREATE COMPLAINT ====================

@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error("JSON request body is required", 400)

    required_fields = [
        "title",
        "description",
        "category",
        "location",
        "citizen_name"
    ]

    missing = [
        field for field in required_fields
        if not str(data.get(field) or "").strip()
    ]

    if missing:
        return jsonify({
            "error": "Required fields are missing",
            "missing_fields": missing
        }), 400

    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        columns = get_columns(cursor, "complaints")

        values = {
            "title": str(data["title"]).strip(),
            "description": str(data["description"]).strip(),
            "category": str(data["category"]).strip(),
            "location": str(data["location"]).strip(),
            "citizen_name": str(data["citizen_name"]).strip(),
            "status": "Pending"
        }

        if "citizen_phone" in columns and data.get("citizen_phone"):
            values["citizen_phone"] = str(
                data["citizen_phone"]
            ).strip()

        # Optional officer assignment
        if data.get("assigned_officer_id") not in (None, ""):
            if "assigned_officer_id" not in columns:
                return error(
                    "Officer assignment column is unavailable",
                    400
                )

            try:
                officer_id = int(data["assigned_officer_id"])
            except (TypeError, ValueError):
                return error("Invalid officer_id", 400)

            cursor.execute("""
                SELECT officer_id
                FROM officers
                WHERE officer_id = %s
            """, (officer_id,))

            if not cursor.fetchone():
                return error("Officer not found", 404)

            values["assigned_officer_id"] = officer_id

        values = {
            key: value
            for key, value in values.items()
            if key in columns
        }

        names = ", ".join(
            f"`{key}`" for key in values
        )

        placeholders = ", ".join(
            ["%s"] * len(values)
        )

        cursor.execute(
            f"INSERT INTO complaints ({names}) VALUES ({placeholders})",
            tuple(values.values())
        )

        complaint_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "message": "Complaint submitted successfully",
            "complaint_id": complaint_id,
            "status": "Pending"
        }), 201

    except mysql.connector.Error:
        if conn:
            conn.rollback()

        app.logger.exception("Create complaint failed")
        return error("Unable to create complaint", 500)

    finally:
        close_db(conn, cursor)


# ==================== UPDATE COMPLAINT STATUS ====================

@app.route(
    "/api/complaints/<int:complaint_id>/status",
    methods=["PUT"]
)
def update_complaint_status(complaint_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved",
        "Rejected"
    ]

    if status not in allowed_statuses:
        return jsonify({
            "error": "Invalid status",
            "allowed_statuses": allowed_statuses
        }), 400

    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT complaint_id
            FROM complaints
            WHERE complaint_id = %s
        """, (complaint_id,))

        if not cursor.fetchone():
            return error("Complaint not found", 404)

        cursor.execute("""
            UPDATE complaints
            SET status = %s
            WHERE complaint_id = %s
        """, (status, complaint_id))

        conn.commit()

        return jsonify({
            "message": "Complaint status updated successfully",
            "complaint_id": complaint_id,
            "status": status
        })

    except mysql.connector.Error:
        if conn:
            conn.rollback()

        app.logger.exception("Status update failed")
        return error("Unable to update complaint status", 500)

    finally:
        close_db(conn, cursor)


# ==================== RESOLVED COMPLAINTS ====================

@app.route("/api/complaints/resolved", methods=["GET"])
def get_resolved_complaints():
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM complaints
            WHERE status = 'Resolved'
            ORDER BY updated_at DESC, complaint_id DESC
        """)

        return jsonify([
            serialize(row) for row in cursor.fetchall()
        ])

    except mysql.connector.Error:
        app.logger.exception("Resolved complaints failed")
        return error("Unable to fetch resolved complaints", 500)

    finally:
        close_db(conn, cursor)


# ==================== GET OFFICERS ====================

@app.route("/api/officers", methods=["GET"])
def get_officers():
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                officer_id,
                name,
                email,
                phone,
                department,
                created_at
            FROM officers
            ORDER BY officer_id
        """)

        return jsonify([
            serialize(row) for row in cursor.fetchall()
        ])

    except mysql.connector.Error:
        app.logger.exception("Get officers failed")
        return error("Unable to fetch officers", 500)

    finally:
        close_db(conn, cursor)


# ==================== GET OFFICER PROFILE ====================

@app.route(
    "/api/officers/<int:officer_id>/profile",
    methods=["GET"]
)
def get_officer_profile(officer_id):
    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                officer_id,
                name,
                email,
                phone,
                department,
                created_at
            FROM officers
            WHERE officer_id = %s
        """, (officer_id,))

        officer = cursor.fetchone()

        if not officer:
            return error("Officer not found", 404)

        return jsonify(serialize(officer))

    except mysql.connector.Error:
        app.logger.exception("Get officer profile failed")
        return error("Unable to fetch officer profile", 500)

    finally:
        close_db(conn, cursor)


# ==================== UPDATE OFFICER PROFILE ====================

@app.route(
    "/api/officers/<int:officer_id>/profile",
    methods=["PUT"]
)
def update_officer_profile(officer_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error("JSON request body is required", 400)

    allowed_fields = [
        "name",
        "email",
        "phone",
        "department"
    ]

    updates = {}

    for field in allowed_fields:
        if field in data:
            value = data[field]

            if field in ["name", "email"]:
                if not str(value or "").strip():
                    return error(
                        f"{field} cannot be empty",
                        400
                    )

            updates[field] = (
                str(value).strip()
                if value is not None
                else None
            )

    if not updates:
        return error("No profile fields supplied", 400)

    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT officer_id
            FROM officers
            WHERE officer_id = %s
        """, (officer_id,))

        if not cursor.fetchone():
            return error("Officer not found", 404)

        set_clause = ", ".join(
            f"`{field}` = %s"
            for field in updates
        )

        cursor.execute(
            f"UPDATE officers SET {set_clause} WHERE officer_id = %s",
            tuple(updates.values()) + (officer_id,)
        )

        conn.commit()

        cursor.execute("""
            SELECT
                officer_id,
                name,
                email,
                phone,
                department,
                created_at
            FROM officers
            WHERE officer_id = %s
        """, (officer_id,))

        return jsonify({
            "message": "Officer profile saved successfully",
            "profile": serialize(cursor.fetchone())
        })

    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()

        return error(
            "That email address is already used by another officer",
            409
        )

    except mysql.connector.Error:
        if conn:
            conn.rollback()

        app.logger.exception("Update officer profile failed")
        return error("Unable to save officer profile", 500)

    finally:
        close_db(conn, cursor)


# ==================== ASSIGN COMPLAINT TO OFFICER ====================

@app.route(
    "/api/complaints/<int:complaint_id>/assign",
    methods=["PUT"]
)
def assign_complaint_to_officer(complaint_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or "officer_id" not in data:
        return error(
            "Provide officer_id in JSON; use null to unassign",
            400
        )

    officer_id = data["officer_id"]

    if officer_id is not None:
        try:
            officer_id = int(officer_id)

            if officer_id <= 0:
                raise ValueError

        except (TypeError, ValueError):
            return error(
                "officer_id must be a positive integer or null",
                400
            )

    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        columns = get_columns(cursor, "complaints")

        if "assigned_officer_id" not in columns:
            return error(
                "assigned_officer_id column is unavailable",
                500
            )

        cursor.execute("""
            SELECT complaint_id
            FROM complaints
            WHERE complaint_id = %s
        """, (complaint_id,))

        if not cursor.fetchone():
            return error("Complaint not found", 404)

        if officer_id is not None:
            cursor.execute("""
                SELECT officer_id
                FROM officers
                WHERE officer_id = %s
            """, (officer_id,))

            if not cursor.fetchone():
                return error("Officer not found", 404)

        cursor.execute("""
            UPDATE complaints
            SET assigned_officer_id = %s
            WHERE complaint_id = %s
        """, (officer_id, complaint_id))

        conn.commit()

        return jsonify({
            "message": "Complaint assignment updated successfully",
            "complaint_id": complaint_id,
            "assigned_officer_id": officer_id
        })

    except mysql.connector.Error:
        if conn:
            conn.rollback()

        app.logger.exception("Complaint assignment failed")
        return error("Unable to assign complaint", 500)

    finally:
        close_db(conn, cursor)


# ==================== FORGOT PASSWORD / OTP ====================

otp_storage = {}
reset_tokens = {}
otp_lock = Lock()

OTP_EXPIRY = 300
RESET_TOKEN_EXPIRY = 300
MAX_OTP_ATTEMPTS = 5


def normalize_contact(contact):
    return str(contact or "").strip().lower()


def valid_contact(contact):
    email_valid = re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        contact
    )

    phone_valid = re.fullmatch(
        r"\+?\d{10,15}",
        contact
    )

    return bool(email_valid or phone_valid)


def valid_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


# ==================== SEND OTP ====================

@app.route("/api/forgot-password/send-otp", methods=["POST"])
def send_forgot_password_otp():
    data = request.get_json(silent=True) or {}

    contact = normalize_contact(data.get("contact"))

    if not valid_contact(contact):
        return error(
            "Enter a valid mobile number or email.",
            400
        )

    otp = f"{secrets.randbelow(1000000):06d}"

    with otp_lock:
        otp_storage[contact] = {
            "otp": otp,
            "expires": time.time() + OTP_EXPIRY,
            "attempts": 0
        }

        # A newly requested OTP invalidates previous reset tokens
        # associated with this contact.
        expired_tokens = [
            token for token, record in reset_tokens.items()
            if record["contact"] == contact
        ]

        for token in expired_tokens:
            reset_tokens.pop(token, None)

    # DEVELOPMENT ONLY:
    # OTP appears in the backend terminal.
    # Do not use terminal logging as OTP delivery in production.
    app.logger.warning(
        "Development OTP generated for %s: %s",
        contact,
        otp
    )

    return jsonify({
        "message": "OTP generated. Check backend terminal for testing.",
        "expires_in": OTP_EXPIRY
    }), 200


# ==================== VERIFY OTP ====================

@app.route("/api/forgot-password/verify-otp", methods=["POST"])
def verify_forgot_password_otp():
    data = request.get_json(silent=True) or {}

    contact = normalize_contact(data.get("contact"))
    entered_otp = str(data.get("otp", "")).strip()

    if not contact or not re.fullmatch(r"\d{6}", entered_otp):
        return error("Enter a valid 6-digit OTP.", 400)

    with otp_lock:
        record = otp_storage.get(contact)

        if not record:
            return error("Request an OTP first.", 400)

        if time.time() > record["expires"]:
            otp_storage.pop(contact, None)
            return error(
                "OTP expired. Request a new one.",
                400
            )

        if record["attempts"] >= MAX_OTP_ATTEMPTS:
            otp_storage.pop(contact, None)
            return error(
                "Too many attempts. Request a new OTP.",
                429
            )

        record["attempts"] += 1

        if not secrets.compare_digest(
            entered_otp,
            record["otp"]
        ):
            return error("Incorrect OTP.", 400)

        otp_storage.pop(contact, None)

        reset_token = secrets.token_urlsafe(32)

        reset_tokens[reset_token] = {
            "contact": contact,
            "expires": time.time() + RESET_TOKEN_EXPIRY
        }

    return jsonify({
        "message": "OTP verified successfully.",
        "reset_token": reset_token,
        "expires_in": RESET_TOKEN_EXPIRY
    }), 200


# ==================== RESET PASSWORD ====================

@app.route(
    "/api/forgot-password/reset-password",
    methods=["POST"]
)
def reset_forgotten_password():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return error("JSON request body is required.", 400)

    reset_token = str(data.get("reset_token", "")).strip()
    new_password = str(data.get("new_password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    if not reset_token:
        return error(
            "Reset token is missing. Verify the OTP again.",
            400
        )

    if not new_password or not confirm_password:
        return error(
            "Enter and confirm your new password.",
            400
        )

    if not valid_password(new_password):
        return error(
            "Password must contain at least 8 characters, "
            "one uppercase letter, one number, and one special character.",
            400
        )

    if new_password != confirm_password:
        return error("Passwords do not match.", 400)

    # Check the token before doing database work.
    with otp_lock:
        token_record = reset_tokens.get(reset_token)

        if not token_record:
            return error(
                "Invalid or already used reset token. Verify OTP again.",
                400
            )

        if time.time() > token_record["expires"]:
            reset_tokens.pop(reset_token, None)
            return error(
                "Reset token expired. Verify OTP again.",
                400
            )

        contact = token_record["contact"]

    conn = cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # The currently confirmed account schema is officers only.
        # User/Admin tables have not been confirmed.
        cursor.execute("""
            SELECT officer_id
            FROM officers
            WHERE LOWER(email) = %s
               OR phone = %s
            LIMIT 1
        """, (contact, contact))

        officer = cursor.fetchone()

        if not officer:
            return error(
                "No matching officer account was found. "
                "User/Admin password reset is not configured yet.",
                404
            )

        password_hash = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE officers
            SET password_hash = %s
            WHERE officer_id = %s
        """, (
            password_hash,
            officer["officer_id"]
        ))

        if cursor.rowcount != 1:
            conn.rollback()
            return error("Password could not be updated.", 500)

        conn.commit()

        # Consume the token after a successful database update.
        with otp_lock:
            reset_tokens.pop(reset_token, None)

        return jsonify({
            "message": "Password reset successfully."
        }), 200

    except mysql.connector.Error:
        if conn:
            conn.rollback()

        app.logger.exception("Password reset failed")
        return error("Unable to reset password.", 500)

    finally:
        close_db(conn, cursor)


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )