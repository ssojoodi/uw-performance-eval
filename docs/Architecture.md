# HR Performance Evaluation Platform - Architecture

## Stack

- Django monolith.
- Django ORM, templates, forms, auth, sessions, groups, permissions, and
  migrations.
- One Django project app for v1.
- No React.
- No public REST API in v1.
- SQLite for local development and deployment.
- Dockerized single-instance deployment.

## App Structure

Keep the app simple:

- `models.py`: Employees, ManagerAssignments, Evaluations, and profile data if
  needed.
- `forms.py`: user management, assignments, evaluations, and import validation.
- `views.py`: authenticated pages and workflow actions.
- `services.py`: workflow transitions and import/export logic if views become
  too large.
- `templates/` and `static/`: server-rendered UI.

## Roles

Business roles:

- `VP`: manages users and assignments; views all evaluations; approves or
  returns evaluations.
- `Manager`: creates, edits, submits, imports, exports, and views only their own
  evaluations for assigned Employees.
- `Employee`: evaluation subject only; no login in v1.

Django superusers are technical operators, not a product Admin role.

Use Django `Group` records for roles. Each active product user must have exactly
one business role.

## Authorization

Enforce authorization in views, forms, and querysets, not only in templates.

- All product routes require login.
- Managers see only evaluations they created.
- Managers create evaluations only for assigned Employees.
- Managers edit only their own `Draft` evaluations.
- VPs see all evaluations.
- VPs cannot edit evaluation content.
- Only VPs approve or return evaluations.
- VPs cannot deactivate their own account.
- Employees have no route access in v1.

## Core Models

- `Employee`: co-op student being evaluated.
- `ManagerAssignment`: Manager-to-Employee assignment.
- `Evaluation`: Manager owner, Employee subject, UW form data, workflow state,
  timestamps, and reviewer metadata.

Removing a `ManagerAssignment` prevents new evaluations for that Employee. It
does not change ownership of existing evaluations.

Store stable UW form fields as normal model fields. Use a validated JSON field
only for form sections that are expected to change.

## Workflow

States:

- `Draft`
- `In Review`
- `Approved`

Transitions:

- Manager submits own `Draft`: `Draft` -> `In Review`.
- VP returns `In Review`: `In Review` -> `Draft`.
- VP approves `In Review`: `In Review` -> `Approved`.

`Approved` evaluations are locked. Workflow state changes should go through
explicit methods or service functions that validate actor role, current state,
ownership, and timestamps.

## Import And Export

Markdown export:

- Available to users who can view the evaluation.
- Includes all evaluation fields.
- Does not change workflow state.

JSON export:

- Available to users who can view the evaluation.
- Uses the same schema accepted by JSON import.

JSON import:

- Manager-only.
- Always creates a new `Draft` evaluation.
- Never overwrites an existing evaluation.
- Requires the selected Employee to be assigned to the importing Manager.
- Validates schema before saving.

Version the JSON schema.

## Persistence

SQLite is the v1 database.

- Store the SQLite file on a mounted Docker volume.
- Run one app instance while using SQLite.
- Use Django migrations for all schema changes.
- Back up the SQLite database from the mounted volume.
- Move to PostgreSQL if write contention, horizontal scaling, or managed
  availability becomes necessary.

## Docker

Required environment:

- `SECRET_KEY`
- `DEBUG=false`
- `ALLOWED_HOSTS`
- SQLite database path
- static files configuration
- CSRF trusted origins when behind HTTPS or a proxy

Container startup should run migrations, serve collected static files, and start
Django with a production WSGI/ASGI server.

## Security

- Use Django password hashing.
- Keep CSRF enabled.
- Set secure session/cookie settings in production.
- Deactivation sets `is_active=false`.
- Do not log evaluation content or uploaded JSON payloads.

## Tests

Cover:

- login, logout, inactive users, and session-required routes;
- exactly-one-role enforcement;
- VP user management and self-deactivation prevention;
- Manager scoping and assignment checks;
- workflow transitions and edit locking;
- Markdown export access/content;
- JSON import/export round trip and malformed JSON handling;
- Docker build and migration startup.
