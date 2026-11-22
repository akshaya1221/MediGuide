# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose medical information, authentication tokens, credentials or uploaded files. Contact the repository owner privately with reproduction steps and the affected version.

## Production checklist

- Replace all example credentials and secrets.
- Use HTTPS and secure, HTTP-only cookies or a hardened token storage strategy.
- Configure narrow CORS origins.
- Set `FILE_ENCRYPTION_KEY` and use encrypted storage volumes.
- Run PostgreSQL on a private network with TLS and managed backups.
- Add malware scanning before document parsing.
- Apply request rate limits and upload quotas.
- Send structured audit events to protected, access-controlled storage.
- Define data retention, export and deletion procedures.
- Complete threat modeling, dependency scanning and penetration testing.
- Obtain clinical, privacy and regulatory review before any real-world deployment.

Never commit `.env` files, encryption keys, API keys, database dumps, uploaded records or screenshots containing patient information.
