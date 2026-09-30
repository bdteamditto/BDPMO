# BD PMO requirements coverage — 30 September 2026

This review tracks the requirements in the BD PMO conversation and the supplied TOR example against the hosted Sites app. The original Word source was not present in the synced `sources/` folder, so this review does not claim to have checked that missing file.

| Area | Implemented behavior |
| --- | --- |
| Home / My Projects | After sign-in the app opens Home first. It lists only project memberships, summarizes health, and shows role, phase, Current and Next TOR milestones. Current/Next advance as earlier TOR milestones reach a delivered/accepted state. |
| Overview | A concise project command center shows health, phase, delivery progress, current and next milestones, items needing attention, and recent activity. Detailed records remain on their own workflow pages. |
| Opening / Procurement / Planning | Contract information and opening checks; PR/PO, vendor, readiness, dependency and waiting fields; plan dates, owners, milestone readiness and task dependencies. |
| TOR / Delivery | Seventeen stable internal fields, editable display headers, Read/Edit modes, row details, row add/remove, TSV paste, autosave and visible feedback, payment summary, cell validation, retained failed drafts, comments, and per-change audit with actor and time. Header renames preserve existing row data. |
| Acceptance / Finance | Acceptance is separate from delivery and linked to TOR milestone records. Finance tracks invoices, customer receipts and vendor payments, linked milestones, evidence and back-to-back payment controls. TOR payment allocation is capped at 100%; payment amounts derive from contract value and percent, not from cash received. |
| Risk / Issue / Blocker | Records include type, owner, due date, status, action, resolution, waiting context, severity/impact, evidence, and audit. Open items appear in project attention summaries and block closure where applicable. |
| Documents / Decisions | Text/link evidence, references, related records and decision rationale. Binary file upload is not included in this release. |
| Tasks / My Work | TODO → IN_PROGRESS → WAITING → BLOCKED → REVIEW → DONE; owner, backup, due date, priority, dependencies, waiting/blocker context, next action, evidence, comments, @mentions, notifications, My Work and audit. |
| Team / Handover | OWNER/EDITOR/VIEWER membership with `addedBy` and `grantedBy`; structured handover for status, completed work, remaining work, next step, waiting for, and important links. Legacy handover notes remain readable. |
| Closure | Readiness covers tasks, delivery/acceptance, finance, open risks/issues, documents, lessons learned, and closure evidence. Required checks need evidence before project completion. |
| System Admin | Separate from project OWNER. Can create users, reset passwords, disable/enable accounts, inspect creator/timestamp, and add/change/remove project memberships. Simple passwords are accepted; passwords are hashed before storage. All admin and membership changes are audited. |
| Permissions | OWNER manages all project roles; EDITOR can add new EDITOR/VIEWER members but cannot change existing roles or set OWNER; VIEWER is read-only. The final OWNER is protected. System Admin can manage memberships across projects. |

## Release boundaries

Full binary file upload was explicitly not required for this round; evidence fields accept text or links and the document model remains extensible. External accounting integration and multi-level approval routing were not requested. In-app notifications, comments, @mentions, dependencies, and My Work remain available. Data not provided by the user—such as contract value, actual receipts, customer acceptance, assigned owners, or evidence—is not fabricated.

See [hosted deployment and live checks](HOSTED_DEPLOYMENT.md) and [validation results](VALIDATION.md).
