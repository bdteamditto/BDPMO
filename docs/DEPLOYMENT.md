# Current hosted application

The application has moved to [Sites with persistent D1](HOSTED_DEPLOYMENT.md). The local tunnel instructions below apply only to the legacy demo.

# Preview and deployment

The current review can run as a temporary HTTPS preview through Cloudflare Quick Tunnel. This is not an always-on hosted deployment: the URL stops working when the local server, tunnel, network connection, or computer stops. No production cutover is enabled.

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

## Preview-only demo provisioning

Keep a dedicated synthetic preview database outside the checkout. Set `PMO_ENV=preview`, `PMO_DB` to that database, `PMO_DEMO_USER` to the demo username, and inject `PMO_DEMO_PASSWORD` from a secret manager or interactive shell environment. Then run:

```sh
python3 server.py --provision-demo
unset PMO_DEMO_PASSWORD
PMO_SECURE_COOKIE=1 python3 server.py --host 127.0.0.1 --port 8765
```

In a separate terminal, run the official Cloudflare client:

```sh
cloudflared tunnel --url http://127.0.0.1:8765 --no-autoupdate --protocol http2
```

Use the returned HTTPS URL. Leave both processes running. No password is supplied in these examples or stored in Git. Provisioning stores only a salted PBKDF2 hash and refuses duplicate accounts. Short nonempty passwords are accepted only by the explicit demo provisioning command when `PMO_ENV=preview`; ordinary `--add-user` always keeps the 12-character minimum. Do not reuse a preview database in production.

For an always-on deployment, a Python hosting account with persistent disk and HTTPS is still required. The temporary tunnel is a review aid, not a substitute for that hosting.
