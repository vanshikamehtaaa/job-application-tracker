# 💼 Job/Internship Application Tracker

A clean, beginner-friendly Flask web application to track job and internship applications using Flask-SQLAlchemy and MySQL.

---

## 🚀 Tech Stack

- **Backend:** Python, Flask
- **Database ORM:** Flask-SQLAlchemy
- **Database:** MySQL (via PyMySQL driver)
- **Frontend:** HTML, CSS, Jinja2 templates (Strictly **NO JavaScript**)

---

## 📁 Project Structure

```text
job_tracker/
├── app.py              # Flask app, routes, DB configuration
├── models.py           # SQLAlchemy JobApplication model & to_dict() serialization
├── templates/
│   └── dashboard.html  # Jinja2 dashboard table (pure HTML/CSS, no JS)
├── static/
│   └── style.css       # Clean, modern CSS styles and badges
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 🔌 REST API Endpoints

### 1. `GET /api/applications`
Returns all job and internship applications as JSON.

- **Method:** `GET`
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

### 2. `POST /api/applications`
Creates a new job application record in the database.

- **Method:** `POST`
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
- **Response:** `201 Created`
```json
{
  "message": "Job application created successfully!",
  "application": {
    "id": 2,
    "company": "Microsoft",
    "role": "Software Engineer Intern",
    "applied_date": "2026-09-08",
    "status": "Applied",
    "job_link": "https://careers.microsoft.com",
    "resume_version": "v1.2",
    "created_at": "2026-09-08 18:00:00"
  }
}
```

---

## 🛠️ Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vanshikamehtaaa/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure MySQL:**
   Ensure MySQL is running and set your database connection in `app.py` or via environment variables:
   ```bash
   export DB_USER=root
   export DB_PASSWORD=yourpassword
   export DB_NAME=job_tracker_db
   ```

4. **Run the Flask application:**
   ```bash
   python app.py
   ```

5. **Open Dashboard:**
   Visit `http://127.0.0.1:5001/` in your browser.
