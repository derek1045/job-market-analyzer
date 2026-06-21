# Job Market Analyzer

A Python scraper that collects software engineering jobs from Greenhouse and Lever job boards and stores them in PostgreSQL.

## What it does

- Fetches job listings from public Greenhouse and Lever JSON APIs using Playwright
- Filters roles by software engineering keywords (backend, frontend, SRE, etc.)
- Saves matching jobs to PostgreSQL with: **title**, **company**, **location**, **url**
- Skips duplicate URLs on repeat runs; updates rows when title or location changes

## Requirements

- Python 3.11+
- PostgreSQL 15+ (local install, no Docker)
- Internet access for scraping

## Project structure

```
job-market-analyzer/
├── database.py         # SQLAlchemy engine, session, table creation
├── models.py           # Job model
├── scraper.py          # Scraper entrypoint
├── requirements.txt
├── setup.sql           # Full database setup (fresh install)
├── fix_permissions.sql # Fix PostgreSQL 15+ schema permissions
└── .env                # Your local DB connection (not committed)
```

## Setup

### 1. Clone and install dependencies

```powershell
cd job-market-analyzer
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\playwright install chromium
```

### 2. Install PostgreSQL

Download and install from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/).

### 3. Create the database

**Fresh install** — run as the `postgres` superuser:

```powershell
psql -U postgres -f setup.sql
```

Edit `setup.sql` first and set your password on the `CREATE USER` line.

**If the database already exists** but table creation fails with `permission denied for schema public`, run:

```powershell
psql -U postgres -f fix_permissions.sql
```

### 4. Configure environment

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql+psycopg2://job_analyzer:your_password@localhost:5432/job_market
```

Use the same password you set in `setup.sql`. If your password contains special characters (`@`, `#`, `%`), URL-encode them (e.g. `@` → `%40`).

## Usage

Run the scraper:

```powershell
.\.venv\Scripts\python scraper.py
```

Example output:

```
[Greenhouse] Stripe: found 85 software engineering jobs
[Greenhouse] Figma: found 25 software engineering jobs
...
Total matching jobs scraped: 322
Saved: 322 inserted, 0 updated, 0 unchanged/skipped
```

Run it again anytime to refresh listings. Existing URLs are not duplicated.

## View saved jobs

**psql:**

```powershell
psql -U job_analyzer -d job_market
```

```sql
SELECT title, company, location, url FROM jobs LIMIT 20;

SELECT company, COUNT(*) AS job_count
FROM jobs
GROUP BY company
ORDER BY job_count DESC;
```

**pgAdmin:** Databases → job_market → Schemas → public → Tables → jobs → View/Edit Data

## Adding companies

Edit the board lists at the top of `scraper.py`:

```python
GREENHOUSE_BOARDS = [
    {"token": "stripe", "company": "Stripe"},
    # token = slug from boards.greenhouse.io/{token}
]

LEVER_BOARDS = [
    {"token": "spotify", "company": "Spotify"},
    # token = slug from jobs.lever.co/{token}
]
```

## Default boards

| Platform   | Companies                                      |
|-----------|------------------------------------------------|
| Greenhouse | Stripe, Figma, Discord, Airbnb, Datadog       |
| Lever      | Netflix, Spotify, Palantir                      |

Some boards may return zero jobs or be skipped if a company changes ATS providers.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `DATABASE_URL is not set` | Create a `.env` file with your connection string |
| `password authentication failed` | Password in `.env` must match PostgreSQL user |
| `permission denied for schema public` | Run `psql -U postgres -f fix_permissions.sql` |
