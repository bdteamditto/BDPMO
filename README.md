# BD PMO · Project Control

A new implementation based on the PMO conversation requirements. This is **not recovered PMO 3.0 source** and does not claim feature parity with the unavailable original repository.

A Thai-language workspace for distributed teams: project status and lifecycle, guided next actions, tasks and dependencies, handover notes, My Work, comments/mentions, in-app notifications, membership management and audit history.

## Run locally

Requires Python 3.11+ and no third-party packages.

```sh
python3 server.py --add-user yourname
python3 server.py
```

The first command securely prompts for a password (at least 12 characters). Open http://127.0.0.1:8000, sign in and create a project. Create additional user accounts with the same CLI before adding them to projects. No default accounts or passwords are shipped.

```sh
python3 -m unittest discover -s tests -v
```

## Collaboration and persistence

Users connect to one server, which persists projects, memberships, comments, events and notifications in SQLite. Refresh the page to load other people's changes. Set `PMO_DB` to a persistent database path. Back up that database with SQLite's backup API. Sessions last eight hours and are intentionally invalidated on server restart.

The included server is for local review or a small controlled pilot. For remote access, deploy behind an HTTPS reverse proxy with `PMO_SECURE_COOKIE=1`, preserve the public Host header, restrict direct backend access, and use a persistent volume. See [deployment notes](docs/DEPLOYMENT.md). No production deployment is enabled.

## Access model

- OWNER manages settings and membership, including other owners. The last owner cannot be removed or demoted.
- EDITOR edits project work. When `allowEditorInvites` is enabled, an editor can add existing accounts as EDITOR or VIEWER; cannot change existing memberships or touch OWNER permissions.
- VIEWER is read-only, including comments and handover.
- All decisions are enforced on the server. Assignment does not grant access. Membership events record actor, before/after role and timestamp; memberships retain `addedBy` and `grantedBy`.

## Included workflows

Project health prioritizes Completed, Blocked, Overdue, At Risk, then On Track. The UI displays the reason. At Risk includes high-priority, waiting or due-in-three-days work. Dates use the server's calendar date. Phase changes are manual; closure requires Closure phase and all tasks done.

Tasks use TODO / IN_PROGRESS / WAITING / BLOCKED / REVIEW / DONE. Waiting and blocked states require context. Dependencies must be in the same project and cannot form cycles. A task cannot finish before its dependencies. Guided phase advice is recommended, not an automated phase gate or invoicing action.

Notifications are created for assignment and explicit whitespace-separated `@username` mentions. Notification access follows current membership. Email, timed due reminders, automated escalations, external invitations, document uploads, financial modules and per-phase approval gates are future work in [the roadmap](docs/ROADMAP.md).

## Review limitations

This first draft uses a single-process standard-library HTTP server, no SSO/password reset, no live updates and no optimistic conflict detection. Concurrent sequential saves to the same task are last-write-wins. Evidence is saved as text/links; files are not uploaded. Audit events are append-only through the application, but database administrators can modify the file. Project members can read project events. Production hardening and operational review are required before broader rollout.
