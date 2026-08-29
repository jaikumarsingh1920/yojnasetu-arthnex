# YojnaSetu Backend Service

FastAPI backend application and relational database layer for YojnaSetu.

## Prerequisites

- Python 3.10+
- SQLite / PostgreSQL 14+

## Environment Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
   - **Linux/macOS**: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

## Database Migrations (Alembic)

Run database migrations to create relational schema tables:

```bash
python -m alembic upgrade head
```

To create new migrations after model changes:
```bash
python -m alembic revision --autogenerate -m "description_of_change"
```

## Data ETL & Database Seed

Populate the database with verified scheme datasets (`schemes_master_cleaned.csv`, `scheme_rules.csv`, `scheme_documents.csv`, `scheme_verification_report.csv`, `scheme_data_changelog.csv`):

```bash
python ../04data/scripts/seed_db.py
```

### Expected Seed Dataset Counts

- **Schemes**: 56 records (All `VERIFIED`)
- **Scheme Rules**: 57 records
- **Scheme Documents**: 20 records
- **Scheme Verifications**: 56 records
- **Scheme Changelogs**: 212 records

The seed script is idempotent and safely rerunnable without duplicating records.

## Running the Server

Start the Uvicorn development server:

```bash
uvicorn app.main:app --reload --port 8000
```

- **API Base**: `http://localhost:8000`
- **Health Check**: `GET http://localhost:8000/health`

## Running Tests

Execute pytest suite covering health check, database schema migrations, and ETL seed idempotency:

```bash
python -m pytest
```
