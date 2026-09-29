# Validation — 29 September 2026

Source base: `248ccb98909d364d82a28225553edfb7541e11ff` on `feat/tor-delivery-spreadsheet`.

- 19 Python tests passed with `python3 -m unittest discover -s tests -v`: project permissions, task lifecycle/dependencies, TOR editing, financial validation and rollback, audit, login/CSRF/logout, HTTP TOR persistence and payment calculation, static-file protection, and preview-only password provisioning.
- 4 JavaScript tests passed with `node --test tests/test_ui.cjs`: Read/Edit and VIEWER controls, derived payment/audit panel updates, rejected-save restoration, and preservation of newer typing. These use a minimal document stub, not a real browser.
- JavaScript syntax check passed with `node --check static/app.js`.
- A separate synthetic preview database was provisioned via environment variables. No plaintext demo credential or database is tracked.
- A Cloudflare Quick Tunnel registered successfully for the localhost service. This is a temporary HTTPS exposure, not persistent cloud hosting.
- Browser verification of both the external URL and localhost was blocked by saved browser permissions, including after explicit conversational permission. Login, TOR rendering, Read/Edit mode and cell editing on the live URL remain **unverified in a real browser**. The automated HTTP tests use an isolated test server/database.
- No merge or production cutover performed. Persistent always-on hosting remains pending a hosting account.
