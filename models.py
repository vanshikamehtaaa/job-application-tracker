import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance.
# We initialize it here without binding to a specific app yet,
# so that app.py can import 'db' and bind it using db.init_app(app).
db = SQLAlchemy()


class JobApplication(db.Model):
    """
    JobApplication Model:
    Represents the 'job_applications' table in our MySQL database.
    Each instance of this class corresponds to a single row in the table.
    """
    __tablename__ = "job_applications"

    # Primary key: Unique identifier for each application, auto-incremented by the database
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Name of the company (Required field)
    company = db.Column(db.String(120), nullable=False)

    # Job title or internship role applied for (Required field)
    role = db.Column(db.String(120), nullable=False)

    # Date when the application was submitted (defaults to today's date if not provided)
    applied_date = db.Column(db.Date, default=datetime.date.today, nullable=False)

    # Status of the application (e.g., 'Applied', 'Interviewing', 'Offered', 'Rejected')
    status = db.Column(db.String(50), default="Applied", nullable=False)

    # Link to the job posting or portal (Optional)
    job_link = db.Column(db.String(255), nullable=True)

    # Version or name of the resume used (e.g., 'SWE_v2', 'Backend_2026') (Optional)
    resume_version = db.Column(db.String(50), nullable=True)

    # Timestamp when this record was added to our database
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def to_dict(self):
        """
        Helper method to serialize the model object into a Python dictionary.
        This makes it very easy to return JSON in Flask REST APIs using jsonify().
        """
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "applied_date": self.applied_date.strftime("%Y-%m-%d") if self.applied_date else None,
            "status": self.status,
            "job_link": self.job_link,
            "resume_version": self.resume_version,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def __repr__(self):
        """Readable string representation for debugging in Python shell."""
        return f"<JobApplication id={self.id} company='{self.company}' role='{self.role}'>"
