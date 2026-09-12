# 💼 Job & Internship Application Tracker (REST API + Web UI)

A full-featured Flask web application and production-grade RESTful API designed to manage and track job and internship applications using Flask-SQLAlchemy and MySQL.

---

## 🚀 Tech Stack

- **Backend:** Python 3, Flask
- **Database ORM:** Flask-SQLAlchemy
- **Database:** MySQL (PyMySQL driver) / SQLite (in-memory test runner)
- **Frontend:** HTML5, CSS3, Jinja2 templates (Strictly **Zero JavaScript**)
- **Testing:** Python `unittest` suite (12 automated test cases)

---

## 📁 Project Structure

```text
job_app/
├── app.py              # Flask app, REST API endpoints, Web UI routes & DB config
├── models.py           # SQLAlchemy JobApplication model & to_dict() serialization
├── test_app.py         # Automated unit tests for all endpoints (100% pass)
├── templates/
│   └── dashboard.html  # Jinja2 web dashboard (pure HTML/CSS, no JS)
├── static/
│   └── style.css       # Clean, modern CSS styling and status badges
├── .env.example        # Environment variable configuration template
├── requirements.txt    # Python dependencies
└── README.md           # Comprehensive documentation
```

---

## 🔌 REST API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/applications` | List all applications |
| `POST` | `/api/applications` | Create a new application |
| `GET` | `/api/applications/<id>` | Retrieve a single application by ID |
| `PUT` | `/api/applications/<id>` | Update an existing application |
| `DELETE` | `/api/applications/<id>` | Delete an application by ID |
| `PATCH` | `/api/applications/<id>/status` | Quick update for application status |
| `GET` | `/api/applications/stats` | Summary statistics & status breakdown |
| `GET` | `/api/applications/search?q=...` | Keyword search across company and role |
| `GET` | `/api/applications/recent?days=7` | Filter applications submitted in last N days |
| `GET` | `/api/applications/status/<status>` | Filter applications by exact status |
| `GET` | `/api/applications/company/<company>`| Filter applications by exact company name |
| `GET` | `/api/applications/role/<role>` | Substring search for job title/role |

---

## 📖 API Documentation & Examples

### 1. `GET /api/applications`
Retrieve all tracked applications ordered by date.
- **Response:** `200 OK`
```json
[
  {
    "id": 1,
    "company": "Google",
    "role": "Software Engineer Intern",
    "applied_date": "2026-09-08",
    "status": "Applied",
    "job_link": "https://careers.google.com",
    "resume_version": "SWE_v1.0",
    "created_at": "2026-09-08 17:25:00"
  }
]
```

---

### 2. `POST /api/applications`
Create a new application.
- **Header:** `Content-Type: application/json`
- **Body:**
```json
{
  "company": "Microsoft",
  "role": "Software Engineer Intern",
  "applied_date": "2026-09-08",
  "status": "Applied",
  "job_link": "https://careers.microsoft.com",
  "resume_version": "v1.2"
}
```
- **Allowed Statuses:** `Applied`, `Interviewing`, `Offered`, `Rejected`
- **Response:** `201 Created`

---

### 3. `GET /api/applications/<int:id>`
Fetch a single application record by its database ID.
- **Response:** `200 OK` or `404 Not Found`

---

### 4. `PUT /api/applications/<int:id>`
Update any fields (`company`, `role`, `status`, `job_link`, `resume_version`) of an application.
- **Body:**
```json
{
  "status": "Interviewing",
  "role": "Senior Engineer"
}
```
- **Response:** `200 OK`

---

### 5. `DELETE /api/applications/<int:id>`
Delete an application permanently from the database.
- **Response:** `200 OK`
```json
{
  "message": "Application deleted"
}
```

---

### 6. `PATCH /api/applications/<int:id>/status`
Partially update just the status of an application.
- **Body:**
```json
{
  "status": "Offered"
}
```
- **Response:** `200 OK`

---

### 7. `GET /api/applications/stats`
Get analytics and summary metrics across all applications.
- **Response:** `200 OK`
```json
{
  "total_applications": 15,
  "unique_companies": 12,
  "status_breakdown": {
    "Applied": 8,
    "Interviewing": 4,
    "Offered": 2,
    "Rejected": 1
  }
}
```

---

### 8. `GET /api/applications/search?q=<query>`
Search across company names and roles using keyword matching.
- **Example:** `/api/applications/search?q=engineer`
- **Response:** `200 OK`

---

### 9. `GET /api/applications/recent?days=<days>`
Filter applications applied within the last N days (default is 7 days).
- **Example:** `/api/applications/recent?days=14`
- **Response:** `200 OK`

---

## 🧪 Running Automated Tests

A full automated test suite using `unittest` and an in-memory SQLite database is included:

```bash
python3 test_app.py
```

Expected output:
```text
Ran 12 tests in 0.178s
OK
```

---

## 🛠️ Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vanshikamehtaaa/job-application-tracker.git
   cd job-application-tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to your environment or export variables:
   ```bash
   cp .env.example .env
   # or export directly:
   export DB_USER=root
   export DB_PASSWORD=your_mysql_password
   export DB_NAME=job_tracker_db
   ```

4. **Start the Flask Application:**
   ```bash
   python3 app.py
   ```

5. **Open Web Dashboard:**
   Visit `http://127.0.0.1:5000/` in your browser.
