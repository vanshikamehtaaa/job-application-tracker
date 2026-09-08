import os
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from models import db, JobApplication

# ==============================================================================
# 1. APPLICATION SETUP & CONFIGURATION
# ==============================================================================

app = Flask(__name__)

# Secret key required for Flask session & flash alert messages
app.secret_key = os.getenv("SECRET_KEY", "job-tracker-secret-key-2026")

# Database configuration settings:
# We use PyMySQL to connect to a local or remote MySQL server.
# You can set these environment variables in your system or use the default values below.
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysqlpass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "job_tracker_db")

# SQLAlchemy MySQL connection string format:
# mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Disable SQLAlchemy event modification tracking to save memory and improve performance
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind the SQLAlchemy db instance from models.py to this Flask application
db.init_app(app)

# Automatically create database tables when the application starts (if they do not already exist)
with app.app_context():
    db.create_all()


# ==============================================================================
# 2. WEB UI ROUTES (HTML / JINJA2 TEMPLATES - NO JAVASCRIPT)
# ==============================================================================

# Route: GET /
# Description:
#   Renders the dashboard HTML page using Jinja2 templates.
#   It queries all job applications from the MySQL database and passes them
#   along with today's date to 'dashboard.html'. Zero JavaScript is used.
@app.route("/", methods=["GET"])
def dashboard():
    # Fetch all job application records ordered by applied_date descending
    applications = JobApplication.query.order_by(JobApplication.applied_date.desc()).all()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return render_template("dashboard.html", applications=applications, today=today_str)


# Route: POST /applications/add
# Description:
#   Handles standard HTML form submissions from the web dashboard.
#   Unlike REST APIs that receive JSON (request.get_json()), pure HTML forms send
#   URL-encoded form data, which Flask reads via 'request.form'.
#   After saving to MySQL, we redirect back to "/" so the new row appears immediately.
@app.route("/applications/add", methods=["POST"])
def add_application_form():
    company = request.form.get("company", "").strip()
    role = request.form.get("role", "").strip()

    if not company or not role:
        flash("Both Company and Role are required fields!", "error")
        return redirect(url_for("dashboard"))

    # Parse applied_date from HTML date input (format: YYYY-MM-DD)
    applied_date_str = request.form.get("applied_date")
    if applied_date_str:
        try:
            applied_date = datetime.datetime.strptime(applied_date_str, "%Y-%m-%d").date()
        except ValueError:
            applied_date = datetime.date.today()
    else:
        applied_date = datetime.date.today()

    status = request.form.get("status", "Applied").strip() or "Applied"
    job_link = request.form.get("job_link", "").strip() or None
    resume_version = request.form.get("resume_version", "").strip() or None

    new_app = JobApplication(
        company=company,
        role=role,
        applied_date=applied_date,
        status=status,
        job_link=job_link,
        resume_version=resume_version
    )

    try:
        db.session.add(new_app)
        db.session.commit()
        flash(f"Application for '{company} ({role})' added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to add application: {str(e)}", "error")

    # Redirect back to the dashboard (Post/Redirect/Get pattern)
    return redirect(url_for("dashboard"))


# Route: POST /applications/delete/<id>
# Description:
#   Handles deleting an application via a pure HTML form submit button.
#   Deletes the record from MySQL and redirects back to the dashboard.
@app.route("/applications/delete/<int:id>", methods=["POST"])
def delete_application_form(id):
    application = JobApplication.query.get_or_404(id)
    try:
        db.session.delete(application)
        db.session.commit()
        flash(f"Application #{id} for '{application.company}' deleted successfully.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete application: {str(e)}", "error")

    return redirect(url_for("dashboard"))


# ==============================================================================
# 3. REST API ENDPOINTS
# ==============================================================================

# ------------------------------------------------------------------------------
# Endpoint 1: GET /api/applications
# Description:
#   Retrieves all job and internship applications from the database.
# Method: GET
# URL: http://127.0.0.1:5001/api/applications
# Expected Response:
#   - HTTP Status: 200 OK
#   - Response Body: JSON list of all job application objects
# ------------------------------------------------------------------------------
@app.route("/api/applications", methods=["GET"], strict_slashes=False)
def get_applications():
    # Query all job application records from MySQL
    applications = JobApplication.query.order_by(JobApplication.applied_date.desc()).all()

    # Convert each SQLAlchemy model instance into a Python dictionary using to_dict()
    applications_data = [app_record.to_dict() for app_record in applications]

    # Return the list as a JSON response with status code 200 (OK)
    return jsonify(applications_data), 200


# ------------------------------------------------------------------------------
# Endpoint 2: POST /api/applications
# Description:
#   Creates a new job or internship application record in the database.
# Method: POST
# URL: http://127.0.0.1:5001/api/applications
# Headers:
#   - Content-Type: application/json
# Expected Request Body (JSON):
#   {
#       "company": "Google",                      (Required, string)
#       "role": "Software Engineer Intern",       (Required, string)
#       "applied_date": "2026-09-08",             (Optional, string 'YYYY-MM-DD', defaults to today)
#       "status": "Applied",                      (Optional, string, defaults to 'Applied')
#       "job_link": "https://example.com/job",    (Optional, string)
#       "resume_version": "v1.2"                  (Optional, string)
#   }
# Expected Response:
#   - HTTP Status: 201 Created (or 400 Bad Request on validation failure)
#   - Response Body: JSON object containing the newly created record and a success message
# ------------------------------------------------------------------------------
@app.route("/api/applications", methods=["POST"], strict_slashes=False)
def create_application():
    # Check if the incoming request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()

    # Handle case where user accidentally wrapped the object in square brackets [ ... ]
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            data = data[0]
        else:
            return jsonify({"error": "Request body must be a JSON object {...}, not an empty list."}), 400

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object {...}"}), 400

    # Validation: Ensure 'company' and 'role' are provided and not empty
    company = data.get("company", "").strip() if data.get("company") else None
    role = data.get("role", "").strip() if data.get("role") else None

    if not company or not role:
        return jsonify({
            "error": "Missing required fields. Both 'company' and 'role' are required."
        }), 400

    # Parse 'applied_date' if supplied, otherwise fallback to today's date
    applied_date_str = data.get("applied_date")
    if applied_date_str:
        try:
            # Parse 'YYYY-MM-DD' format
            applied_date = datetime.datetime.strptime(applied_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({
                "error": "Invalid date format for 'applied_date'. Please use 'YYYY-MM-DD'."
            }), 400
    else:
        applied_date = datetime.date.today()

    # Optional fields with sane defaults
    status = data.get("status", "Applied").strip() if data.get("status") else "Applied"
    job_link = data.get("job_link")
    resume_version = data.get("resume_version")

    # Create a new JobApplication instance with the parsed values
    new_application = JobApplication(
        company=company,
        role=role,
        applied_date=applied_date,
        status=status,
        job_link=job_link,
        resume_version=resume_version
    )

    try:
        # Add the new record to the database session and commit the transaction
        db.session.add(new_application)
        db.session.commit()

        # Return the created record along with HTTP 201 (Created)
        return jsonify({
            "message": "Job application created successfully!",
            "application": new_application.to_dict()
        }), 201

    except Exception as e:
        # Rollback the session in case of any database error to keep data consistent
        db.session.rollback()
        return jsonify({
            "error": "Failed to create application record.",
            "details": str(e)
        }), 500


# ==============================================================================
# 4. APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    # Note: We use port 5001 by default because on macOS, port 5000 is often reserved by AirPlay
    port = int(os.getenv("PORT", 5001))
    print("=" * 60)
    print("Starting Job/Internship Application Tracker...")
    print(f"Web Dashboard : http://127.0.0.1:{port}/")
    print(f"GET Endpoint  : http://127.0.0.1:{port}/api/applications")
    print(f"POST Endpoint : http://127.0.0.1:{port}/api/applications")
    print("=" * 60)
    app.run(debug=True, port=port)
