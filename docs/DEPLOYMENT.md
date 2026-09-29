# Preview and deployment

No deployment integration was available in this session. No production cutover or deployment configuration has been activated.

## Local preview

Run `python3 server.py --add-user yourname`, then `python3 server.py`. This binds only to localhost. The repository contains no seeded identities, passwords, production records or credentials.

## Proposed hosted pilot

1. Use a Python 3.11+ service with a persistent volume, one application process and a dedicated preview database.
2. Set `PMO_DB` to that volume and `PMO_SECURE_COOKIE=1`.
3. Start `python3 server.py --host 0.0.0.0 --port 8000` behind HTTPS; allow inbound backend connections only from the proxy. Preserve the public Host header for origin checks.
4. Create pilot accounts via the CLI using unique passwords. Do not put passwords in GitHub, command arguments or logs.
5. Verify login/logout, member isolation, VIEWER denial, editor invite rules, last-owner protection, persistence across restarts and database backups.
6. Use a separate domain and synthetic data for preview. Do not repoint the existing production URL.
7. Obtain explicit approval before production cutover. Decide on SSO, account lifecycle, monitoring, login rate limiting behind proxy, backup/restore, conflict handling, scale, TLS and production HTTP hosting before that cutover.

The API provides session cookies, CSRF token checks, origin checks, login throttling, password hashing and a static-file allowlist. These are implementation controls, not a claim of a completed security review.
