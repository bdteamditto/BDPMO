# Current hosted application

The live application is [BD PMO](https://bd-pmo-workspace.bdteam1.chatgpt.site/), hosted on Sites with a persistent D1 database. It continues to work when the original laptop or a temporary Cloudflare tunnel is offline. Sign-in and project membership are required to see project records.

The deployable source is in [`hosted/`](../hosted/); the original Python/SQLite server remains available for local development only. Do not treat its local accounts or database as production data.

## Local development

```sh
python3 server.py --add-user yourname
python3 server.py
```

The local Python server uses SQLite and its own account rules. It is not a fallback for the live Site.

## Hosted operations

- Site identity and D1 binding are recorded in `hosted/.openai/hosting.json`.
- Runtime credentials and provisioning secrets are configured through Sites and never stored in repository files.
- User passwords are salted PBKDF2 hashes with a server-side pepper. Admin create/reset/enable/disable operations are audited.
- Initial data import is single-use and refuses to overwrite an initialized workspace.
- D1 writes use revision checks so concurrent edits fail visibly instead of silently replacing saved data.
- Publish only saved, successfully built Site versions; keep the Site's current audience and the production URL.

See [hosted deployment record](HOSTED_DEPLOYMENT.md) and [validation](VALIDATION.md).
