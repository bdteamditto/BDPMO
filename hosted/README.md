# BD PMO hosted workspace

This is the Sites/Cloudflare Worker build of the PMO workspace in `bdteamditto/BDPMO`. The published app persists project state, memberships, accounts, sessions, audit events, and notifications in D1.

## Capabilities

Home / My Projects is membership-scoped. The workspace includes contract opening, procurement and vendor readiness, planning, a 17-field editable TOR sheet, acceptance, finance, risk/issue/blocker records, documents/decisions, tasks and dependencies, team handover, closure checks, and in-app notifications. Read/Edit permissions are enforced server-side. System Admin can create or reset users with simple passwords, enable/disable accounts, and manage all project memberships. Stored passwords are salted PBKDF2 hashes, never plaintext.

## Operations

- `.openai/hosting.json` identifies the existing Site and its logical D1 binding.
- Runtime values are managed through Sites; do not check secrets into source.
- Admin provisioning is authenticated and performed out of band. The initial production credential is not recorded in GitHub.
- Initial import is single-use and refuses to overwrite existing project data.
- Concurrent D1 writes use revision checks and return a recoverable conflict instead of silently replacing another update.
- The original local Python demo is not the published app; make hosted changes under this directory and update its UI tests.

## Validation and deployment

Run `node --test tests/*.test.mjs` from this directory. Run Python and UI tests from the repository root. Follow [hosted deployment notes](../docs/HOSTED_DEPLOYMENT.md) and the Sites workflow for publishing. Binary file upload, scheduled email escalation, accounting integrations, and multi-level approvals are outside this release.
