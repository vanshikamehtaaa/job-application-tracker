import unittest
import json
import datetime
from app import app, db, JobApplication


class JobTrackerTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database and test client before every test."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["WTF_CSRF_ENABLED"] = False

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        """Clean up database session and tables after every test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_sample_app(self, company="Google", role="Software Engineer", status="Applied"):
        """Helper to create a sample record in the test database."""
        job = JobApplication(
            company=company,
            role=role,
            applied_date=datetime.date.today(),
            status=status,
            job_link="https://careers.google.com",
            resume_version="v1.0"
        )
        db.session.add(job)
        db.session.commit()
        return job

    # --------------------------------------------------------------------------
    # Web UI Tests
    # --------------------------------------------------------------------------
    def test_dashboard_renders(self):
        """Ensure the HTML dashboard loads with 200 OK."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Job/Internship Application Tracker", response.data)

    def test_html_form_add_and_delete(self):
        """Ensure standard HTML form submission creates and deletes records."""
        # Add via form
        post_resp = self.client.post("/applications/add", data={
            "company": "Amazon",
            "role": "SDE Intern",
            "applied_date": "2026-09-10",
            "status": "Applied",
            "job_link": "",
            "resume_version": "v1"
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertIn(b"Amazon", post_resp.data)

        # Delete via form
        job = JobApplication.query.filter_by(company="Amazon").first()
        self.assertIsNotNone(job)

        del_resp = self.client.post(f"/applications/delete/{job.id}", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(JobApplication.query.filter_by(company="Amazon").first())

    # --------------------------------------------------------------------------
    # REST API CRUD Tests
    # --------------------------------------------------------------------------
    def test_create_application_success(self):
        """POST /api/applications creates a record."""
        payload = {
            "company": "Microsoft",
            "role": "Full Stack Intern",
            "status": "Applied"
        }
        response = self.client.post("/api/applications",
                                  data=json.dumps(payload),
                                  content_type="application/json")
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["application"]["company"], "Microsoft")
        self.assertEqual(data["application"]["role"], "Full Stack Intern")

    def test_create_application_invalid_status(self):
        """POST /api/applications rejects unknown status values."""
        payload = {
            "company": "Apple",
            "role": "iOS Developer",
            "status": "InvalidStatus"
        }
        response = self.client.post("/api/applications",
                                  data=json.dumps(payload),
                                  content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Invalid status", data["error"])

    def test_get_applications_list(self):
        """GET /api/applications returns list of records."""
        self._create_sample_app(company="Meta", role="Data Engineer")
        response = self.client.get("/api/applications")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["company"], "Meta")

    def test_get_application_by_id(self):
        """GET /api/applications/<id> returns specific application."""
        sample = self._create_sample_app()
        response = self.client.get(f"/api/applications/{sample.id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["id"], sample.id)

        # Non-existent ID
        not_found = self.client.get("/api/applications/999")
        self.assertEqual(not_found.status_code, 404)

    def test_update_application_put(self):
        """PUT /api/applications/<id> updates multiple fields."""
        sample = self._create_sample_app()
        payload = {
            "role": "Senior Engineer",
            "status": "Interviewing"
        }
        response = self.client.put(f"/api/applications/{sample.id}",
                                  data=json.dumps(payload),
                                  content_type="application/json")
        self.assertEqual(response.status_code, 200)

        updated = db.session.get(JobApplication, sample.id)
        self.assertEqual(updated.role, "Senior Engineer")
        self.assertEqual(updated.status, "Interviewing")

    def test_delete_application(self):
        """DELETE /api/applications/<id> deletes the application."""
        sample = self._create_sample_app()
        response = self.client.delete(f"/api/applications/{sample.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(db.session.get(JobApplication, sample.id))

    # --------------------------------------------------------------------------
    # Advanced Filter & Analytics Tests
    # --------------------------------------------------------------------------
    def test_patch_status_endpoint(self):
        """PATCH /api/applications/<id>/status updates only status."""
        sample = self._create_sample_app(status="Applied")
        response = self.client.patch(f"/api/applications/{sample.id}/status",
                                    data=json.dumps({"status": "Offered"}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.get(JobApplication, sample.id).status, "Offered")

        # Invalid status should return 400
        invalid_resp = self.client.patch(f"/api/applications/{sample.id}/status",
                                        data=json.dumps({"status": "Pending"}),
                                        content_type="application/json")
        self.assertEqual(invalid_resp.status_code, 400)

    def test_stats_endpoint(self):
        """GET /api/applications/stats returns counts and status breakdown."""
        self._create_sample_app(company="A", status="Applied")
        self._create_sample_app(company="B", status="Interviewing")
        self._create_sample_app(company="C", status="Interviewing")

        response = self.client.get("/api/applications/stats")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["total_applications"], 3)
        self.assertEqual(data["unique_companies"], 3)
        self.assertEqual(data["status_breakdown"]["Applied"], 1)
        self.assertEqual(data["status_breakdown"]["Interviewing"], 2)

    def test_search_endpoint(self):
        """GET /api/applications/search?q=term matches company or role."""
        self._create_sample_app(company="Netflix", role="Backend Python Engineer")
        self._create_sample_app(company="Spotify", role="Frontend React Engineer")

        # Search by keyword
        resp = self.client.get("/api/applications/search?q=Python")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["applications"][0]["company"], "Netflix")

    def test_search_by_status_and_company_routes(self):
        """Test status and company path filters."""
        self._create_sample_app(company="Stripe", status="Interviewing")

        status_resp = self.client.get("/api/applications/status/Interviewing")
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(len(status_resp.get_json()), 1)

        comp_resp = self.client.get("/api/applications/company/Stripe")
        self.assertEqual(comp_resp.status_code, 200)
        self.assertEqual(len(comp_resp.get_json()), 1)


if __name__ == "__main__":
    unittest.main()
