# 🚢 Deployment

> *"Real artists ship."* — Steve Jobs

[← Back to README](../README.md) · See also [Configuration](CONFIGURATION.md)

## Production Stack

`docker-compose.prod.yml` runs three services:

| Service | Role | Exposed? |
|---------|------|----------|
| 🚀 **app** | FastAPI on :7860 | Internal only |
| 🕸️ **neo4j** | Neo4j 5 Community with healthcheck | Internal only |
| 🔒 **caddy** | Reverse proxy, auto-HTTPS via Let's Encrypt | :80, :443 |

Neo4j is never exposed to the internet. Caddy handles TLS automatically. Fort Knox vibes 🏰

## Deploy Commands

```bash
# Fresh VPS setup (Ubuntu 22.04+)
ssh root@your-server 'bash -s' < scripts/deploy.sh

# On the server: configure and start
nano .env  # Set DOMAIN, API keys, NEO4J_PASSWORD
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Update after code changes
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

## ❤️ Health check

`GET /healthz` returns `{"status":"ok","neo4j":"up"}` (HTTP 200) when the app can
reach Neo4j, or `{"status":"degraded","neo4j":"down"}` (HTTP 503) when it can't.
Use it for uptime monitors and container/orchestrator health probes.

```bash
curl -fsS https://prove.codeblackwell.ai/healthz
```

## 🛡️ Security

- 🔐 Caddy auto-provisions HTTPS via Let's Encrypt and adds security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- ⏱️ Rate limits: 20 chat requests/hour, 60 reads/hour per visitor (IP + browser fingerprint)
- 🏠 Localhost is exempt from rate limits for development
- 🙈 Private repo code is redacted by default (`SHOW_PRIVATE_CODE=false`) — context descriptions and GitHub links still shown, raw code withheld
- 🤫 Secrets live in `.env` on the server (never committed)

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
