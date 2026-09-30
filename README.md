# BD PMO · Project Control

A Thai-language PMO workspace for tracking contract setup, procurement, plans, TOR deliveries, customer acceptance, billing, risks, documents, tasks, handover, and closure.

## Published application

[Open BD PMO](https://bd-pmo-workspace.bdteam1.chatgpt.site/). The app runs on Sites with a persistent D1 database; it does not depend on a laptop or temporary tunnel. Sign-in is required, and the Home page lists only projects where the signed-in account has membership. User accounts and the initial System Admin credential are provisioned outside Git; this repository contains no production passwords.

## Project workflow

- Home / My Projects shows project health, membership role, phase, and Current / Next work milestones from TOR.
- Overview is a short command center for delivery progress, the current and next milestones, items needing attention, and recent activity.
- Project workflow pages hold the contract-opening checklist, PR/PO and vendor readiness, plan and dependencies, TOR / delivery, customer acceptance, finance, risks/issues, documents/decisions, tasks, team handover, and closure checks.
- TOR keeps 17 stable fields, Read and Edit modes, row details, TSV paste, autosave feedback, payment allocation capped at 100%, and an audit history. Renaming a display header never changes the stored row field.
- System Admin manages accounts, password resets, access enable/disable, and membership across projects. Project OWNER and EDITOR membership rules are enforced by the API; the final OWNER cannot be removed.

## Local development

The original Python server remains available for local work with SQLite. It is separate from the published hosted app.

```sh
python3 server.py --add-user yourname
python3 server.py
python3 -m unittest discover -s tests -q
```

Run hosted API/core tests from `hosted/` and UI tests from the repository root:

```sh
cd hosted
node --test tests/*.test.mjs
cd ..
node --test tests/test_ui.cjs
```

## Data, permissions, and boundaries

Hosted project state and account hashes are stored in D1. Passwords are stored as salted PBKDF2 hashes with a server-side pepper; sessions are revocable and mutations require CSRF and origin checks. Changes, access grants, header renames, and user-management actions are audited. Evidence fields accept text and links. Binary file upload, scheduled email/push reminders, external accounting integration, and multi-level approvals are outside this release.

See [hosted deployment notes](docs/HOSTED_DEPLOYMENT.md), [requirements coverage](docs/REQUIREMENTS_REVIEW.md), and [validation results](docs/VALIDATION.md).
