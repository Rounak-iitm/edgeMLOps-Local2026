# Security Baseline

- API authentication is enabled by default.
- Keep the service bound to localhost unless the customer explicitly requires LAN exposure.
- Never commit `docker/.env` or API keys.
- Terminate TLS using an approved reverse proxy when crossing trust boundaries.
- Run containers as non-root with dropped capabilities and no-new-privileges.
- Keep the model store read-only inside the serving container.
- Patch the OS, Docker and Python dependencies according to the customer's vulnerability-management policy.
- Generate an SBOM for every release and scan both Python dependencies and container images.
- Restrict outbound network access; runtime inference does not require cloud access.
- Protect backups and audit logs with the customer's access-control and retention policies.
