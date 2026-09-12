import os
import datetime
from flask import Flask, request, jsonify, render_template
from sqlalchemy import func, or_
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
    applications = db.session.get(JobApplication, id)
    if not applications:
        return jsonify({"error": f"Application with ID {id} not found."}), 404
    return jsonify(applications.to_dict()), 200


@app.route("/api/applications/<int:id>", methods=["DELETE"])
def delete_application_by_id(id):
    applications = db.session.get(JobApplication, id)
    if not applications:
        return jsonify({"error": f"Application with ID {id} not found"}), 404
    try:
        db.session.delete(applications)
        db.session.commit()
        return jsonify({"message": "Application deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete Application"}), 500


@app.route("/api/applications/<int:id>", methods=["PUT"])
def update_application_by_id(id):
    applications = db.session.get(JobApplication, id)
    if not applications:
        return jsonify({"error": "Application not found"}), 404
    data = request.get_json()
    try:
        if data.get("company"):
            applications.company = data.get("company")
        if data.get("role"):
            applications.role = data.get("role")
        if data.get("status"):
            applications.status = data.get("status")
        if data.get("job_link"):
            applications.job_link = data.get("job_link")
        if data.get("resume_version"):
            applications.resume_version = data.get("resume_version")
        db.session.commit()
        return jsonify({"message": "Application updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update Application"}), 500


@app.route("/api/applications/status/<status>", methods=["GET"])
def search_application_by_status(status):
    applications = JobApplication.query.filter_by(status=status).all()
    if not applications:
        return jsonify({"error": "No Application Found"}), 404
    application_data = [app_record.to_dict() for app_record in applications]
    return jsonify(application_data), 200


@app.route("/api/applications/company/<company>", methods=["GET"])
def search_application_by_company(company):
    applications = JobApplication.query.filter_by(company=company).all()
    if not applications:
        return jsonify({"error": "No Application Found"}), 404
    application_data = [app_data.to_dict() for app_data in applications]
    return jsonify(application_data), 200


@app.route("/api/applications/role/<role>", methods=["GET"])
def search_application_by_role(role):
    # Case-insensitive substring match for role (e.g. 'engineer' or 'frontend')
    applications = JobApplication.query.filter(JobApplication.role.ilike(f"%{role}%")).all()
    if not applications:
        return jsonify({"error": f"No applications found for role '{role}'"}), 404
    application_data = [app_data.to_dict() for app_data in applications]
    return jsonify(application_data), 200


@app.route("/api/applications/stats", methods=["GET"])
def get_application_stats():
    total = JobApplication.query.count()
    # Group by status to get breakdown counts
    status_counts = db.session.query(
        JobApplication.status, func.count(JobApplication.id)
    ).group_by(JobApplication.status).all()
    breakdown = {status: count for status, count in status_counts}

    unique_companies = db.session.query(func.count(func.distinct(JobApplication.company))).scalar() or 0

    return jsonify({
        "total_applications": total,
        "unique_companies": unique_companies,
        "status_breakdown": breakdown
    }), 200


@app.route("/api/applications/<int:id>/status", methods=["PATCH"])
def update_application_status(id):
    application = db.session.get(JobApplication, id)
    if not application:
        return jsonify({"error": f"Application with ID {id} not found"}), 404

    data = request.get_json()
    if not data or not data.get("status"):
        return jsonify({"error": "Missing 'status' in request body."}), 400

    new_status = str(data.get("status")).strip()
    if not new_status:
        return jsonify({"error": "'status' cannot be empty."}), 400

    try:
        application.status = new_status
        db.session.commit()
        return jsonify({
            "message": "Status updated successfully",
            "application": application.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update status", "details": str(e)}), 500


@app.route("/api/applications/search", methods=["GET"])
def search_applications():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Search query parameter 'q' is required. Example: /api/applications/search?q=google"}), 400

    applications = JobApplication.query.filter(
        or_(
            JobApplication.company.ilike(f"%{query}%"),
            JobApplication.role.ilike(f"%{query}%")
        )
    ).all()

    return jsonify({
        "query": query,
        "count": len(applications),
        "applications": [app_data.to_dict() for app_data in applications]
    }), 200


@app.route("/api/applications/recent", methods=["GET"])
def get_recent_applications():
    days_param = request.args.get("days", 7)
    try:
        days = int(days_param)
        if days <= 0:
            return jsonify({"error": "Parameter 'days' must be a positive number."}), 400
    except ValueError:
        return jsonify({"error": "Query parameter 'days' must be an integer."}), 400

    cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
    applications = JobApplication.query.filter(
        JobApplication.applied_date >= cutoff_date
    ).order_by(JobApplication.applied_date.desc()).all()

    return jsonify({
        "days": days,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
        "count": len(applications),
        "applications": [app_data.to_dict() for app_data in applications]
    }), 200



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
    
