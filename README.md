# Performance Evaluation Platform

Server-rendered Django app for managing employee performance evaluations through
Manager drafting, VP review/approval, and Markdown/PDF export.

v1 is intentionally small: one Django app, SQLite, Django templates/forms/auth,
and Docker Compose for single-instance deployment.

## Run Local

```bash
cp .env.example .env
uv pip install -r requirements.txt
uv run python manage.py migrate
uv run python manage.py runserver
```

Open `http://127.0.0.1:8000`.

For local Docker:

```bash
cp .env.example .env
docker compose up --build
```

The SQLite database is stored under `data/`.

## Deploy To Production

Use Docker Compose with one web container while SQLite is the backend.

Production environment should set:

```env
SECRET_KEY=...
DEBUG=false
ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SQLITE_PATH=data/db.sqlite3
WEB_PORT=8000
```

Mount `data/` on durable storage and back it up. The container runs migrations
on startup and collects static files at image build time.
