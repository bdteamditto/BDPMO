# BD PMO — hosted workspace

This is the hosted port of `bdteamditto/BDPMO` at `04907db`. It preserves the Thai workspace UI, project records, TOR spreadsheet, lifecycle forms, evidence checks, permissions, comments, notifications and audit history.

## Persistence and concurrency

Cloudflare D1 stores the workspace document, revision, accounts, sessions and login limits. Each mutation validates server-side and commits the complete workspace plus audit with a conditional revision update. Concurrent conflicting commits return 409 and the UI keeps the form or cell draft. This document model targets the current small-team workload; the complete history is retained, while the UI shows the latest 300 events per project.

The production database is provisioned separately. No project data, password or runtime secret is checked in. A one-time authenticated import refuses to overwrite an initialized workspace. Passwords are salted PBKDF2 hashes with a server-side pepper; sessions use hashed opaque tokens, CSRF and origin checks. Preview-only short passwords are not accepted by hosted account provisioning.

## Operations

- `.openai/hosting.json` declares the Site identity and logical D1 binding.
- Runtime secrets: `PMO_PASSWORD_PEPPER`, and `PMO_IMPORT_TOKEN` only during initial migration. Keep the pepper stable; changing it requires resetting account passwords.
- After importing, remove the import token using Sites environment management.
- OWNER can add existing members or create a new account through สมาชิกและสิทธิ์. New hosted passwords require at least 16 characters.
- `/api/export` requires a logged-in session and CSRF token and returns only projects the current user may access, with full audit history. It excludes passwords and sessions.
- Database migrations are generated with Drizzle and applied by Sites before deployment. Do not rewrite applied migration files.
- The original Python demo remains separate until the hosted migration is accepted; do not allow edits to both copies after cutover.

## Verification

`node --test tests/*.test.mjs` covers lifecycle operations, authorization, financial rules, atomic updates, D1-backed API persistence, login/logout, CSRF/origin, one-time import, account creation and optimistic concurrency. The source data migration was compared with the Python implementation for all project fields, milestones, members, history and derived summaries before import.

Build using the Sites workflow. The frontend remains the original maintained HTML/CSS/JavaScript interface served by Vinext; APIs run in a Cloudflare Worker with D1, independent of the user's computer.

This deployment does not add binary document uploads, accounting integration, scheduled email escalation or multi-level approval routing. Those remain separate product work.
