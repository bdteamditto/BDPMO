# Validation — 30 September 2026

Branch: `feat/tor-delivery-spreadsheet`, draft PR #2. No merge or production cutover.

- **33 Python tests passed**: permissions, task lifecycle/dependencies, TOR edits, atomic bulk paste, payment allocation and rollback, audit, lifecycle modules, evidence rules, closure/reopening, back-to-back receipt allocation, record comments, cross-project reference rejection, Thai dates, delivery summaries, HTTP login/CSRF/logout and HTTP persistence across all new modules.
- **8 JavaScript tests passed**: Read/Edit and VIEWER controls; derived payment/audit updates; failed-draft retention; newer typing preservation; overview 3/5 progress independent of finance/acceptance; every module/form rendered against real backend metadata; date-input normalization and detail audit labels; visible dialog validation failures with retry.
- JavaScript syntax and Git whitespace checks passed.
- Frontend tests use a minimal document stub and backend-generated fixtures, not a browser. HTTP tests use a separate temporary database and server.
- Actual preview database backed up before update. Its five milestones now have three DELIVERED, one IN_PROGRESS and one NOT_DUE, per user confirmation. Derived progress is 60%; accepted count is zero until evidence is supplied; allocated payment percentages total 100%, without implying cash received.
- The old temporary tunnel expired. A replacement tunnel registered and the preview service was restarted. Saved browser access restrictions prevent claiming live-browser end-to-end verification.
- Only salted password hashes are stored in the external preview database. No plaintext demo credential or user records are committed.

Commands: `python3 -m unittest discover -s tests -q`, `node --test tests/test_ui.cjs`, `node --check static/app.js`, `git diff --check`.

See [requirements coverage and remaining work](REQUIREMENTS_REVIEW.md) and [deployment limitations](DEPLOYMENT.md).

## Hosted follow-up

See [HOSTED_DEPLOYMENT.md](HOSTED_DEPLOYMENT.md) for the persistent Sites deployment, 17 hosted backend/API tests, data parity checks and live browser verification. The earlier browser access restriction was resolved in the subsequent user-authorized test.
