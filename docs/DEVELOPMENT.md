# 🛠️ Development

[← Back to README](../README.md) · See also [Contributing](../CONTRIBUTING.md) · [Architecture](ARCHITECTURE.md)

## 🗂️ Project Structure

```
src/
├── app.py                        # 🚀 FastAPI entry point, SSE streaming, rate limiting
├── config/settings.py            # ⚙️ Env + subject.toml configuration dataclass
├── core/
│   ├── client_factory.py         # 🏭 Provider-aware client construction
│   ├── claude_chat_client.py     # 🤖 Anthropic adapter (OpenAI-compatible interface)
│   ├── nim_client.py             # 🟢 NVIDIA NIM wrapper (chat + embeddings)
│   ├── voyage_client.py          # 🚢 Voyage embedding wrapper
│   ├── neo4j_client.py           # 🕸️ Graph DB client with vector search
│   ├── db.py                     # 💾 SQLite persistence (conversations, logs, rate limits)
│   └── logger.py                 # 📋 Structured JSON logger with session auditing
├── ingestion/
│   ├── cli.py                    # 📥 Ingestion entry point (resume + repos)
│   ├── graph_builder.py          # 🔨 Code → Neo4j graph pipeline
│   ├── code_parser.py            # 🌳 Tree-sitter chunking (Python, JS, TS, TSX, Jupyter)
│   ├── context_generator.py      # 🪄 Sonnet contextual descriptions for embeddings
│   ├── skill_classifier.py       # 🏷️ Sonnet skill detection against taxonomy
│   ├── skill_taxonomy.py         # 📊 11 domains, 40+ categories, ~85 skills
│   └── resume_parser.py          # 📄 Resume extraction (PDF, DOCX, MD, TXT)
├── qa/
│   ├── agent.py                  # 🤖 ReAct agent with curation and conversation history
│   └── tools.py                  # 🔧 6 tools (search, evidence, gaps, repos, resume)
├── jd_match/
│   ├── agent.py                  # 📋 Job description match orchestrator
│   ├── parser.py                 # ✂️ Requirement extraction via LLM
│   └── matcher.py                # 🎯 Vector-based per-requirement matching
├── ui/
│   └── competency_map.py         # 📊 Graph visualization data (treemap, bars, tooltips)
├── static/
│   ├── chat.js                   # 💬 Chat SSE streaming + message rendering
│   ├── graph.js                  # 📈 D3 treemap/bars + reference modals
│   ├── jd.js                     # 📋 JD match modal + results UI
│   ├── fingerprint.js            # 🔒 Lightweight browser fingerprinting for rate limits
│   └── style.css                 # 🎨 Glassmorphic design system
├── templates/
│   └── index.html                # 🖥️ Single-page app shell
scripts/
├── reembed.py                    # 🔄 Context generation + embedding pipeline
└── deploy.sh                     # 🚀 Fresh VPS deployment script
```

## 🧪 Testing

```bash
uv run pytest tests/ -m "not e2e"         # unit tests (fast, need Neo4j running) ⚡
uv run pytest tests/test_qa.py            # QA agent (ReAct loop, curation, formatting, streaming)
uv run pytest tests/test_ingestion.py     # Parsing, graph building, skill extraction
uv run pytest tests/test_jd_match.py      # Requirement parsing, matching, confidence
uv run pytest tests/test_db.py            # SQLite persistence, rate limiting
uv run pytest tests/test_config.py        # subject.toml loading + name-rule rendering
```

Unit tests mock all external services — Neo4j and the LLM APIs — so they need no
running containers. The `-m "not e2e"` filter deselects the Playwright browser
suite under `tests/e2e/`, which needs a live server (`just dev`) and an optional
`BASE_URL`:

```bash
just dev                  # in one terminal — serves :7860
uv run pytest tests/e2e   # in another — runs the browser suite
```

Lint and format are enforced by `ruff` (and in CI):

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

## 🗄️ SQLite schema

The SQLite schema (`src/core/db.py`) is applied with `CREATE TABLE/INDEX IF NOT
EXISTS` on startup. **Changes are additive only** — there is no migration framework
and no down-migrations. Renaming/dropping a column or backfilling rows needs a
manual one-off script. Adopt a lightweight migration tool only if a destructive
schema change becomes necessary. (Neo4j is the primary store; SQLite holds
conversations, logs, rate limits, and the ingestion cost ledger.)

## 📋 Structured Logging

Every LLM call, embedding, tool execution, and curation decision is logged with session context, token counts, latency, and cost estimates. Full observability, zero guesswork 🔍

- **Console** — Colored human-readable output 🎨
- **File** — JSON lines at `logs/app.jsonl` 📁
- **SQLite** — Queryable via `/api/logs` endpoint 🗄️

```bash
LOG_LEVEL=DEBUG just dev  # verbose mode 🔊
```

**Cost estimation per model:**

| Model | Input ($/M tokens) | Output ($/M tokens) | Vibe |
|-------|-------------------:|--------------------:|------|
| Claude Sonnet | $3.00 | $15.00 | 💎 Premium |
| Claude Haiku 4.5 | $1.00 | $5.00 | ⚡ Sweet spot |
| Voyage-3.5 | $0.06 | — | 🪶 Featherweight |
| NIM (Nemotron + EmbedQA) | Free | Free | 🆓 Can't beat free |

Sample session summary:
```json
{
  "session_id": "6c418440fbb1",
  "llm_calls": 3,
  "embed_calls": 1,
  "tool_calls": 2,
  "total_input_tokens": 11634,
  "total_output_tokens": 1948,
  "total_cost_usd": 0.011,
  "total_latency_ms": 8600
}
```

☝️ That's a penny per question. Not bad for an AI-powered evidence engine.
