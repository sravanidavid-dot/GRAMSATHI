from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)


# ==================== DATABASE ====================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="gramsathi_user",
        password="gramsathi123",
        database="gramsathi_db"
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
        "message": "GramaSathi Backend is running!"
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


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )