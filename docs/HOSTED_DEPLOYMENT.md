# Hosted BD PMO — 30 September 2026

Application: [https://bd-pmo-workspace.bdteam1.chatgpt.site/](https://bd-pmo-workspace.bdteam1.chatgpt.site/)

The application runs on Sites/Cloudflare Workers with a persistent D1 database. It does not depend on a laptop or temporary tunnel. The login credential is provisioned outside GitHub; no plaintext password is stored in the repository.

## Data and access

- The migrated project, milestones, memberships, comments, workflow records and audit history persist in D1.
- Project data appears only for accounts with project membership. Project OWNER, EDITOR and VIEWER rules are checked by the API.
- System Admin account management is separate from project OWNER. It can create/reset users with simple passwords, enable/disable accounts, and manage project membership across all projects. Passwords are hashed before storage.
- Header, TOR cell, project, user, membership and workflow mutations write audit events. Concurrent D1 changes are guarded by revisions.
- Evidence is recorded as text or links; binary uploads and external integrations are not part of this release.

## Validation

Latest published release:

- Sites source commit: `390fa5ba710f52434ce400c8634d1fa0ac52b94c`
- Saved version: 10 (`appgprj_6abbf56a11a08191a8e38c8059988f25~appgver_7322d822bc5c8191bd363d8e6cfed97a`)
- Production deployment: `appgdep_6abcf984ebf4819191161b4413aca791` — succeeded
- URL: [https://bd-pmo-workspace.bdteam1.chatgpt.site/](https://bd-pmo-workspace.bdteam1.chatgpt.site/)

The live browser path passed: login → Home / My Projects → project Overview → TOR Read Mode → Edit Mode → header rename → cell edit → TSV paste → payment summary → audit history → Team / Membership → System Admin. The Home card and Overview both showed three completed delivery milestones (60%), Current milestone 4, and Next milestone 5. The TOR payment summary matched the supplied 20% / 40% / 40% allocation and totaled 100%. Header and paste tests were restored after validation; their audit entries remain as an accurate history. The Admin page showed account creation, password reset/disable controls, and cross-project role management; the create-user form was inspected and closed without adding a test account.

Project-startup and closure pages were also checked. The closure view correctly flags outstanding acceptance, finance, document, risk, and closeout evidence as incomplete. Contract value remains unspecified because no amount was supplied.

See [requirements coverage](REQUIREMENTS_REVIEW.md) and [validation](VALIDATION.md) for the full checklist and tests.
