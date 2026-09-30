# BD PMO scope review — 30 September 2026

Reviewed accessible BD PMO repository files, the project roadmap, prior migration notes, and the shared requirements conversation: https://chatgpt.com/share/6abbbb8f-55c8-83ec-9f1a-d61607a48bb6 . The synced project `sources/` directory was empty. The original referenced Word document was not available; this is not a claim that its contents were checked.

## Implemented in this preview

| Area | Available behavior |
| --- | --- |
| Overview | Current project phase, delivered milestone count and percent, current milestone, accepted count, overdue/blocked work, actual cash records, owner and recent changes. Delivery progress does not imply payment or customer acceptance. |
| Lifecycle | Contract → Procurement → Planning → Delivery → Acceptance → Billing → Closure. Required/recommended checklists with owner, date, evidence and notes. Advancing phase does not automatically mark earlier checks complete. |
| Opening | Contract review, project opening, guarantee, stamp duty and kickoff records. |
| Cost | Cost Sheet, approved budget, advance cash and forecast records. |
| Procurement | PR, PO, vendor contract, vendor progress and accounting report records. Alerts for vendor start before PO, end buffer under 15 days, and reporting deadlines. |
| Delivery | TOR spreadsheet with Read/Edit, typed date/number/status inputs, cell autosave, retained failed drafts, bounded TSV paste, payment allocation and per-cell audit. Row details include owner, next action, blocker, handover, evidence, comments and linked documents. |
| Finance | Invoice, RC, customer receipts and vendor payments. Completed back-to-back payments require a completed customer receipt, correct date order and sufficient unallocated receipt amount. |
| Risk | Severity, impact, mitigation, owner and status. High/critical active risks contribute to overview alerts. |
| Documents | Document and decision records with references, evidence, reasons and links to project records. |
| Closure | Final acceptance, assets, handover, lessons, warranty and guarantee release records. Closing requires completed tasks, accepted milestones, closed risks/finance and evidenced required acceptance/billing/closure checklists. |
| Collaboration | Tasks, backup owner, handover notes, dependencies, record comments, member-only mentions, assignment notifications and My Work. Backend permissions apply to every mutation. |

## Honest limits for the meeting

- This is a working preview, not a claim that the full roadmap is complete.
- Documents are references/links and text; binary upload and external document storage are not implemented.
- Notifications are in-app assignments and mentions. Scheduled reminders, email/push escalation, workload planning, live collaborative editing and accounting-system integration remain future work.
- Daily/weekly updates can be recorded as tasks or notes; there is no dedicated reporting workflow yet.
- Control forms capture records and rules; they do not implement multi-level approval routing or replace an accounting ledger.
- Browser access was subsequently available. Login, overview and cell-to-audit behavior were verified during the hosted migration; see HOSTED_DEPLOYMENT.md.
- Hosting now uses Sites and persistent D1. The old Quick Tunnel is a separate legacy demo; see HOSTED_DEPLOYMENT.md.
- User project data, credentials and preview database remain outside Git. Unprovided acceptance, amounts, payments, owners and evidence are not fabricated.
