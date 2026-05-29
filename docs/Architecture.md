# HR Performance Evaluation Platform - Architecture

## Stack

- Django monolith.
- Django ORM, templates, forms, auth, sessions, groups, permissions, and
  migrations.
- One Django project app for v1.
- No React.
- No public REST API in v1.
- SQLite for local development and deployment.
- Docker Compose single-instance deployment.

## App Structure

Keep the app simple:

- `models.py`: Employees, ManagerAssignments, EvaluationTemplates, Evaluations,
  and profile data if needed.
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

Use Django `Group` records for roles. The v1 group names are `VP`, `Manager`,
and `Employee`. A user is treated as a Manager only when they belong to the
`Manager` group. Each active product user must have exactly one business role.

## Authorization

Enforce authorization in views, forms, and querysets, not only in templates.

- All product routes require login.
- Managers see current and past evaluations they created.
- Managers create evaluations only for assigned Employees.
- Managers edit only their own `Draft` evaluations.
- VPs see evaluations awaiting review and finalized evaluations.
- VPs cannot edit evaluation content.
- Only VPs approve or return evaluations.
- VPs cannot deactivate their own account.
- Employees have no route access in v1.

## Data Model

- `User`: Django auth user for VPs and Managers. Role comes from exactly one
  Django `Group`.
- `Employee`: co-op student being evaluated. Fields: name, email, student ID if
  available, active flag, timestamps.
- `ManagerAssignment`: links one Manager `User` to one `Employee`. Fields:
  manager, employee, active flag, timestamps. Unique active assignment per
  manager/employee pair.
- `EvaluationTemplate`: versioned questionnaire definition. Fields: name, slug,
  version, active flag, finalized flag, JSON schema, timestamps. Finalized
  templates are immutable except for the active flag.
- `Evaluation`: one performance evaluation. Fields: manager, employee, state,
  template, response data, submitted/approved/returned metadata, timestamps.

Relationships:

- A Manager can have many assigned Employees.
- An Employee can have many Evaluations over time.
- An Evaluation belongs to exactly one Manager, one Employee, and one
  EvaluationTemplate version.
- VPs are not assigned to Employees; they access Evaluations by role.

Rules:

- Removing a `ManagerAssignment` prevents new evaluations for that Employee but
  does not change existing Evaluation ownership.
- Managers can start evaluations only from active finalized templates.
- Evaluation templates are authored as JSON in `EvaluationTemplate.schema`; adding
  a new template does not require code changes.
- Evaluations store answers as validated JSON keyed by the template schema.
- A finalized template cannot be edited; clone it into a new draft version for
  questionnaire changes.
- Template question types are select-one, select-many, and text.
- Built-in v1 templates are UW end-of-term evaluation and UW mid-term review.

## Workflow

States:

- `Draft`
- `In Review`
- `Approved`

Transitions:

- Manager submits own `Draft`: `Draft` -> `In Review`.
- Manager unlocks own `In Review`: `In Review` -> `Draft`.
- VP returns `In Review`: `In Review` -> `Draft`.
- VP approves `In Review`: `In Review` -> `Approved`.

Managers may preview their own `In Review` evaluations but cannot edit them
without unlocking them back to `Draft`. `Approved` evaluations are final. They
remain visible as read-only records and cannot be unlocked, returned, or edited.
Workflow state changes should go through explicit methods or service functions
that validate actor role, current state, ownership, and timestamps.

## Import And Export

Markdown export:

- Available to users who can view the evaluation.
- Includes all evaluation fields.
- Does not change workflow state.

PDF export:

- Available to users who can view the evaluation.
- Includes the same evaluation fields as Markdown export in a printable layout.
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

## Docker Compose

Required environment:

- `SECRET_KEY`
- `DEBUG=false`
- `ALLOWED_HOSTS`
- SQLite database path
- static files configuration
- secure cookie flags for HTTPS deployments
- CSRF trusted origins when behind HTTPS or a proxy

Deployment runs through `compose.yaml`. The Compose stack should build the
Django image, mount a durable SQLite volume, expose the web service, and run one
app container.

Container startup should run migrations and start Django with a production
WSGI/ASGI server. Static files are collected at image build time and served by
the Django container.

## Security

- Use Django password hashing.
- Keep CSRF enabled.
- Set `SESSION_COOKIE_SECURE=true` and `CSRF_COOKIE_SECURE=true` in production
  HTTPS deployments.
- Deactivation sets `is_active=false`.
- Do not log evaluation content or uploaded JSON payloads.

## Tests

Cover:

- login, logout, inactive users, and session-required routes;
- exactly-one-role enforcement;
- VP user management and self-deactivation prevention;
- Manager scoping and assignment checks;
- workflow transitions and edit locking;
- Markdown and PDF export access/content;
- JSON import/export round trip and malformed JSON handling;
- Docker build and migration startup.
