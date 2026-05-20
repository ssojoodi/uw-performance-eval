---
name: architecture-first
description: Use when working on this UW performance evaluation Django app, especially before implementation, refactors, auth, workflow, persistence, Docker, or import/export changes. Requires consulting docs/Architecture.md and keeping it aligned with code decisions.
---

# Architecture First

Before changing code or project structure:

1. Read `docs/Architecture.md`.
2. Check `docs/Requirements.md` for the relevant behavior.
3. Keep the implementation aligned with the architecture:
   - one simple Django project app;
   - server-rendered Django UI;
   - SQLite v1 backend;
   - Dockerized single-instance deployment;
   - server-side authorization;
   - no Employee login in v1.
4. If implementation needs to diverge, update `docs/Architecture.md` in the same
   change and explain the reason.

Prefer small, direct Django changes over new frameworks or unnecessary service
splits.
