# Private Metro team site — IT handoff

Deployment package is prepared, not published. No hosting or company identity credentials were provided. Keep SIAM data private.

1. Provision an approved Linux host with Docker Compose, at least 4 GiB app memory plus OS/proxy headroom; assess actual workbook size under load. Place this directory on the host.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, supply the corporate OIDC credentials/cookie secret privately, and assign verified-email roles. Make it readable by container UID 10001 without granting public access. Use a fresh random cookie secret. Register `https://YOUR-APPROVED-HOST/oauth2callback` as the identity-provider callback. Do not commit secrets.
3. Run `docker compose up --build -d`. The container listens through a host loopback binding only. Missing secrets prevent startup; absent role configuration denies application access.
4. Put the approved domain behind an HTTPS reverse proxy forwarding to `127.0.0.1:8501`; enable WebSocket upgrades, a suitable upload request limit (up to 200 MiB), and timeouts. Use the organization's supported proxy and TLS certificates. Permit only approved private/VPN users at the network boundary. The Compose package does not issue certificates or provision DNS.
5. Confirm local `/_stcore/health` returns `ok`, then test the HTTPS site in a browser: anonymous sign-in gate, rejected unlisted identity, approved analyst/executive identities, verified email claims, logout, synthetic workbook ingestion, reconciliation, reviewed query, and executive export restriction. Test simultaneously with two users and check data isolation. Health alone does not validate OIDC or analytics.
6. Never enable `METRO_LOCAL_MODE` in team deployments. The application refuses local bypass with `METRO_DEPLOYMENT=team`, non-loopback binding, or non-loopback client IP. Both roles can view their uploaded dataset; there is no shared central workbook/database or branch-level authorization. Each user uploads a workbook for their own session. Shared ingestion requires additional work.
7. Configure AI only with Metro approval; outbound question text requires a user opt-in. AI credentials are server-side. Real workbook, live OIDC, AI, TLS deployment, load limits, and container build have not been validated in this cloud session.

Personal Windows/macOS launchers are for single-machine use only. No live public service or company URL has been created by this package.
