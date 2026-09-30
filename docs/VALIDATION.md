# Validation — 30 September 2026

Branch `feat/tor-delivery-spreadsheet`; PR #2 remains open as a draft and is not merged.

- **33 Python tests passed** for the local app's permission, task, TOR, payment, audit, lifecycle, HTTP, and persistence behavior.
- **26 hosted core/API tests passed** for D1-compatible persistence, authentication, CSRF/origin, membership visibility, Current/Next derivation, role rules, stable header rename, row-data preservation, audit, simple-password user create/reset/disable, payment bounds, task dependencies, and closure gates.
- **10 JavaScript UI tests passed** for Read/Edit permissions, payment/audit refresh, failed-draft retention, separate Home and Overview, Current/Next display, concise Overview, Team handover, System Admin, module forms, and visible validation errors.
- JavaScript syntax, hosted build, and Git whitespace checks passed.
- Live production checks passed on Sites version 10: login; Home membership filter and Current/Next; Overview at 3/5 deliveries and Current 4 / Next 5; TOR Read/Edit; header rename with row values preserved; cell edit; TSV paste; payment summary at 100%; audit history; Team membership and structured handover; and System Admin account form. Temporary test cell values and the test header were restored; the audit intentionally retains those test and restore events.
- Corrected production payment allocation to match the supplied example: work 2 / payment 1 / 20%, work 4 / payment 2 / 40%, work 5 / payment 3 / 40%. Contract value remains blank because the user did not provide an amount.
- Sites deployment succeeded at `https://bd-pmo-workspace.bdteam1.chatgpt.site/`; source commit `390fa5ba710f52434ce400c8634d1fa0ac52b94c`; saved version 10; deployment `appgdep_6abcf984ebf4819191161b4413aca791`.

Commands: `python3 -m unittest discover -s tests -q`; from `hosted/`, `node --test tests/*.test.mjs`; from the repository root, `node --test tests/test_ui.cjs`; `node --check hosted/public/app.js`, `hosted/lib/pmo/core.mjs`, and `hosted/lib/pmo/api.mjs`; and `git diff --check`.
