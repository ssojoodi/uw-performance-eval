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

Use Docker Compose with one web container while SQLite is the backend. Publish
the container on a localhost-only port, then proxy your public subdomain to that
port from the host nginx.

On the server, copy `example.env` to `.env`, edit the values for the deployment,
then start Compose. Docker Compose reads `.env` automatically from the directory
containing `compose.yaml`.

```bash
cp example.env .env
docker compose up -d --build
```

Production `.env` should set:

```env
SECRET_KEY=...
DEBUG=false
ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SQLITE_PATH=data/db.sqlite3
WEB_PORT=8084
```

Mount `data/` on durable storage and back it up. The container runs migrations
on startup and serves packaged static files through Django.

### Create Initial Accounts

Create a Django superuser after the first deployment:

```bash
docker compose exec web python manage.py createsuperuser
```

Use that account only for technical administration at `/admin/`. In Django
admin, create product users under **Users** and assign each active product user
to exactly one group: `VP`, `Manager`, or `Employee`.

For v1, Employees are evaluation subjects and do not log in. Create student
records under **Employees**, then use **Manager assignments** to assign active
Employees to Manager users.
