import os
import datetime
from flask import Flask, request, jsonify, render_template
from models import db, JobApplication



app = Flask(__name__)


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
# 2. WEB UI ROUTE (HTML / JINJA2 TEMPLATE)
# ==============================================================================

# Route: GET /
# Description:
#   Renders the dashboard HTML page using Jinja2 templates.
#   It queries all job applications from the MySQL database and passes them
#   to the 'dashboard.html' template. There is NO JavaScript used here or in the template.
@app.route("/", methods=["GET"])
def dashboard():
    # Fetch all job application records ordered by applied_date descending
    applications = JobApplication.query.order_by(JobApplication.applied_date.desc()).all()
    return render_template("dashboard.html", applications=applications)


# ==============================================================================
# 3. REST API ENDPOINTS
# ==============================================================================

# ------------------------------------------------------------------------------
# Endpoint 1: GET /api/applications
# Description:
#   Retrieves all job and internship applications from the database.
# Method: GET
# URL: http://127.0.0.1:5000/api/applications
# Expected Response:
#   - HTTP Status: 200 OK
#   - Response Body: JSON list of all job application objects
# ------------------------------------------------------------------------------
@app.route("/api/applications", methods=["GET"])
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
# URL: http://127.0.0.1:5000/api/applications
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
@app.route("/api/applications", methods=["POST"])
def create_application():
    # Check if the incoming request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()

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

@app.route("/api/applications/<int:id>", methods=["GET"])
def get_application_by_id(id):
    application = db.session.get(JobApplication, id)
    if not application:
        return jsonify({"error": f"Application with ID {id} not found."}), 404
    return jsonify(application.to_dict()), 200


@app.route("/api/applications/<int:id>", methods=["DELETE"])
def delete_application_by_id(id):
    application = db.session.get(JobApplication, id)
    if not application:
        return jsonify({"error": f"Application with ID {id} not found"}), 404
    try:
        db.session.delete(application)
        db.session.commit()
        return jsonify({"message": "Application deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete Application"}), 500


@app.route("/api/applications/<int:id>", methods=["PUT"])
def update_application_by_id(id):
    application = db.session.get(JobApplication, id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    data = request.get_json()
    try:
        if data.get("company"):
            application.company = data.get("company")
        if data.get("role"):
            application.role = data.get("role")
        if data.get("status"):
            application.status = data.get("status")
        if data.get("job_link"):
            application.job_link = data.get("job_link")
        if data.get("resume_version"):
            application.resume_version = data.get("resume_version")
        db.session.commit()
        return jsonify({"message": "Application updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update Application"}), 500

# ==============================================================================
# 4. APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Job/Internship Application Tracker...")
    print("Web Dashboard : http://127.0.0.1:5000/")
    print("GET Endpoint  : http://127.0.0.1:5000/api/applications")
    print("POST Endpoint : http://127.0.0.1:5000/api/applications")
    print("=" * 60)
    app.run(debug=True, port=5000)
    
