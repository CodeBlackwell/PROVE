# ⚙️ Configuration

[← Back to README](../README.md) · See also [Ingestion Guide](INGESTION.md) · [Deployment](DEPLOYMENT.md)

```bash
cp .env.example .env
```

## 🧑 Subject identity (`subject.toml`)

PROVE represents one engineer. Who that is — display name, how the agent is
allowed to refer to them, the GitHub owner for code links, and the canonical
domain — lives in **`subject.toml`** at the repo root. To run PROVE for someone
else, edit that file; no code changes needed.

```toml
name = "Ada Lovelace"
preferred_names = ["Ada"]        # leave [] to disable strict naming rules
forbidden_names = []
github_owner = "adalovelace"
domain = "prove.example.com"
```

The `DOMAIN` and `GITHUB_OWNER` env vars override the matching keys when set.

## 🔑 Required (pick at least one pipeline)

| Variable | Notes |
|----------|-------|
| `NVIDIA_API_KEY` | Required for NIM pipeline (free 🆓) |
| `ANTHROPIC_API_KEY` | Required for Anthropic chat; also enables Sonnet for ingestion |
| `VOYAGE_API_KEY` | Required for Voyage embeddings |

## 🔀 Pipeline Selection

| Variable | Default | Options |
|----------|---------|---------|
| `CHAT_PROVIDER` | `nim` | `nim` or `anthropic` |
| `EMBED_PROVIDER` | `nim` | `nim` or `voyage` |
| `CLAUDE_MODEL` | `claude-haiku-4-5-20251001` | Query model only — ingestion always uses Sonnet |

## 🗄️ Database and Graph

| Variable | Default | Notes |
|----------|---------|-------|
| `NEO4J_URI` | `bolt://localhost:7687` | Auto-set in `docker-compose.prod.yml` |
| `NEO4J_USER` | `neo4j` | |
| `NEO4J_PASSWORD` | `prove` | Change this in production! 🔐 |
| `DB_PATH` | `data/prove.db` | SQLite for conversations, logs, rate limits |

## 🐙 GitHub

| Variable | Default | Notes |
|----------|---------|-------|
| `GITHUB_TOKEN` | — | Enables private repo access during ingestion |
| `GITHUB_OWNER` | from `subject.toml` | Overrides `subject.toml` owner for GitHub links |
| `SHOW_PRIVATE_CODE` | `false` | When `false`, private repo code is redacted (context + links still shown) |

## 🚢 Deployment and Logging

| Variable | Default | Notes |
|----------|---------|-------|
| `DOMAIN` | from `subject.toml` | Your domain for Caddy auto-HTTPS + sitemap/canonical URLs |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CDN_BASE` | — | CloudFront CDN base URL (optional) |
