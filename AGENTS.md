# Agent Instructions

## Project Direction

- Build a Dockerized, server-rendered Django app.
- Use SQLite as the v1 backend.
- Keep the product in one simple Django project app.
- Do not add React or a public REST API unless `docs/Architecture.md` is updated
  first.

## Required Context

- Always read `docs/Architecture.md` before making implementation decisions.
- If a requested change conflicts with `docs/Architecture.md`, update the
  architecture doc in the same change or ask for clarification.
- Use `docs/Requirements.md` for product behavior and acceptance criteria.

## Build Constraints

- Use Django ORM, templates, forms, auth, sessions, groups, permissions, and
  migrations.
- Keep authorization server-side in views, forms, querysets, and workflow
  helpers.
- Employees are evaluation subjects only in v1; they do not log in.
- Django superusers are technical operators, not product Admin users.
- SQLite must run as a single app instance with the database file on durable
  mounted storage.

## Expected Validation

- Run relevant Django tests before finishing implementation changes.
- For Docker changes, verify the image/build path and migration startup path
  when practical.
- If validation cannot be run, state why and name the unverified risk.
