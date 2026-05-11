# Stage Monitoring Tool - Backend

Python/FastAPI backend for the internship monitoring system.

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or using uv:
```bash
uv pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### 3. Seed test data

First, manually create an admin user (since registration requires authentication):

```python
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@school.be",
    password_hash=get_password_hash("admin123"),
    first_name="Admin",
    last_name="User",
    role="admin"
)
db.add(admin)
db.commit()
```

Then run the seed script:
```bash
python seed.py
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login with email/password
- `POST /auth/register` - Register new user (admin only)
- `GET /auth/me` - Get current user

### Internships
- `GET /internships` - List internships (role-filtered)
- `POST /internships` - Create new internship (student)
- `GET /internships/{id}` - Get internship details
- `PATCH /internships/{id}/status` - Update status (committee)
- `POST /internships/{id}/agreement` - Upload agreement PDF

### Logbooks
- `GET /internships/{id}/logbooks` - List logbooks
- `POST /internships/{id}/logbooks` - Create logbook
- `PATCH /logbooks/{id}` - Update logbook

### Evaluations
- `GET /internships/{id}/evaluations` - List evaluations
- `POST /internships/{id}/evaluations` - Create evaluation

### Competencies
- `GET /competencies` - List competencies
- `POST /competencies` - Create competency (admin)
- `PATCH /competencies/{id}` - Update competency (admin)
- `DELETE /competencies/{id}` - Deactivate competency (admin)

### Feedback
- `GET /internships/{id}/feedback` - List feedback
- `POST /internships/{id}/feedback` - Create feedback

### Dashboard
- `GET /internships/stats/dashboard` - Get dashboard statistics

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app entry point
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # Authentication utilities
│   └── routers/
│       ├── __init__.py
│       ├── auth.py      # Auth endpoints
│       ├── internships.py # Internship endpoints
│       └── competencies.py # Competency endpoints
├── tests/
├── uploads/             # File uploads directory
├── requirements.txt
├── seed.py              # Test data seeding
└── README.md
```

## Database

Uses SQLite by default (file-based, no setup needed). Change `SQLALCHEMY_DATABASE_URL` in `app/database.py` for PostgreSQL/MySQL.

## Environment Variables

Create a `.env` file for production:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./stage_monitoring.db
```

## Testing

```bash
pytest
```

## Notes

- Status transitions are validated (see `STATUS_FLOW` in `internships.py`)
- Special rule: internship can only go to "Lopend" status if agreement is uploaded
- File uploads stored in `uploads/agreements/`
- JWT tokens expire after 24 hours