# Hosted BD PMO — 30 September 2026

Application: https://bd-pmo-workspace.bdteam1.chatgpt.site

The application now runs on Sites/Cloudflare Workers with a persistent D1 database. It does not depend on the demo laptop or its Cloudflare Quick Tunnel.

`hosted/` contains the full deployable hosted source, including lockfile, build integration, schema-only Drizzle migration, backend port, UI and tests. The separate Sites source repository was published at commit `ddb2afca521cc6770c907d2442c701b8e7cc0dc1` (environment revision 2).

## Data and access

- Migrated one project and all 108 existing audit entries, preserving the latest user edits, memberships, comments, workflow data and financial allocations.
- Compared imported records and derived summaries with the original Python implementation before import.
- The URL exposes the login screen. Project data and writes require an authenticated application account and project membership.
- Production uses a new strong credential provisioned separately. The original demo credential is not accepted. Passwords and migration data are outside Git.
- Initial import is single-use and refuses overwrite. Its provisioning secret was removed after import.
- OWNER may create a separate account and assign a project role from สมาชิกและสิทธิ์. Existing role enforcement remains server-side.
- D1 persists projects, revision, account password hashes, hashed sessions and login limits. Concurrent conflicting mutations return a recoverable 409 instead of replacing another committed update.
- A backup of the original SQLite database was kept locally before migration. Do not continue editing the old demo database after cutover.

## Validation

- 17 hosted backend/API tests passed against SQLite-backed D1-compatible statements: storage, authentication, CSRF/origin, account provisioning, permissions, money rules, closure gates and concurrent updates.
- Original frontend tests also cover duplicate-free change/blur autosave and visible form errors.
- Local Worker runtime login and cell autosave were verified in a browser, including audit entries and restored test values.
- Sites deployment reached `succeeded` with the URL above. Final browser checks and cutover details are recorded in the PR.

## Remaining product work

File uploads, scheduled email escalation, accounting integrations and multi-level approval routing are not included. The deployment is persistent hosting for the implemented workspace; it is not a claim that every future roadmap item exists.
