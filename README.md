# ShowMeOff

AI-powered engineering portfolio agent. Ingests your resume and code repositories, builds a Neo4j knowledge graph of skills and evidence, and answers employer questions with cited, grounded code examples.

## What It Does

A recruiter asks *"Does this engineer know Kubernetes?"* — ShowMeOff searches 22K+ indexed code snippets, finds real implementations, and responds with proficiency assessment, curated evidence, and GitHub links. No hallucination — every claim is backed by code.

**Three modes:**
- **QA Chat** — ReAct agent with 6 tools (vector search, skill lookup, gap analysis, repo overview)
- **JD Match** — Paste a job description, get per-requirement match scores with code evidence
- **Competency Map** — Interactive graph visualization of the skill taxonomy

## Architecture

```
Resume + Repos → Tree-sitter Parse → LLM Skill Classification → LLM Context Generation → Embedding → Neo4j

User Query → Embed Query → Vector Search → ReAct Agent (LLM + Tools) → Evidence Curation → Streamed Response
```

**Dual-provider system** — toggle between free (NVIDIA NIM) and quality (Anthropic + Voyage) backends via env vars:

| Capability | NIM Pipeline (free) | Anthropic Pipeline |
|---|---|---|
| Chat | Nemotron 49B | Claude Sonnet |
| Embeddings | EmbedQA 1B | Voyage-3.5 |
| Ingestion | Sonnet (if key set) → Nemotron fallback | Claude Sonnet |

## Quick Start

```bash
# 1. Start Neo4j
docker compose up -d

# 2. Install dependencies
uv sync

# 3. Configure (.env)
cp .env.example .env
# Add at minimum: NVIDIA_API_KEY
# For quality pipeline: ANTHROPIC_API_KEY, VOYAGE_API_KEY

# 4. Ingest your data
uv run python -m src.ingestion.cli \
  --resume path/to/resume.pdf \
  --github-user your-username

# 5. Run
just dev
# → http://127.0.0.1:7860
```

### Anthropic Pipeline

```bash
CHAT_PROVIDER=anthropic EMBED_PROVIDER=voyage just dev
```

### Re-embed with Contextual Descriptions

Each code snippet gets an LLM-generated contextual description that bridges the vocabulary gap between natural language queries and raw code. Re-embedding processes all providers in parallel:

```bash
uv run python scripts/reembed.py                        # auto-detects all available providers
uv run python scripts/reembed.py --providers voyage nim  # explicit
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHAT_PROVIDER` | `nim` | `nim` or `anthropic` |
| `EMBED_PROVIDER` | `nim` | `nim` or `voyage` |
| `NVIDIA_API_KEY` | — | Required for NIM pipeline |
| `ANTHROPIC_API_KEY` | — | Required for `anthropic` chat; enables Sonnet for ingestion when set |
| `VOYAGE_API_KEY` | — | Required for `voyage` embeddings |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Any Claude model ID |
| `NEO4J_URI` | `bolt://localhost:7687` | |
| `NEO4J_PASSWORD` | `showmeoff` | |
| `GITHUB_TOKEN` | — | For private repo access during ingestion |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Knowledge Graph

```
Engineer -[:OWNS]-> Repository -[:CONTAINS]-> File -[:CONTAINS]-> CodeSnippet -[:DEMONSTRATES]-> Skill
Domain -[:CONTAINS]-> Category -[:CONTAINS]-> Skill
Engineer -[:CLAIMS]-> Skill  (from resume)
Engineer -[:HELD]-> Role -[:AT]-> Company
```

Proficiency is computed from evidence density: **extensive** (10+ snippets across 2+ repos), **moderate** (3+), **minimal** (1+).

## Structured Logging

Every LLM call, embedding, tool execution, and curation decision is logged with session context, token counts, latency, and cost estimates.

- **Console**: colored human-readable output
- **File**: JSON lines at `logs/app.jsonl` for analysis

```bash
LOG_LEVEL=DEBUG just dev  # verbose mode
```

Sample session summary:
```json
{
  "session_id": "6c418440fbb1",
  "llm_calls": 3,
  "embed_calls": 1,
  "tool_calls": 2,
  "total_input_tokens": 11634,
  "total_output_tokens": 1948,
  "total_cost_usd": 0.064,
  "total_latency_ms": 34533
}
```

## Testing

```bash
uv run pytest tests/ -v              # all 33 tests
uv run pytest tests/test_qa.py -v    # just QA agent tests
```

## Project Structure

```
src/
├── app.py                      # FastAPI entry point, SSE streaming
├── config/settings.py          # Env-based configuration
├── core/
│   ├── client_factory.py       # Provider-aware client construction
│   ├── claude_chat_client.py   # Anthropic adapter (OpenAI-compatible interface)
│   ├── nim_client.py           # NVIDIA NIM wrapper
│   ├── voyage_client.py        # Voyage embedding wrapper
│   ├── neo4j_client.py         # Graph DB client with vector search
│   └── logger.py               # Structured JSON logger with session auditing
├── ingestion/
│   ├── cli.py                  # Ingestion entry point
│   ├── graph_builder.py        # Code → Neo4j graph pipeline
│   ├── code_parser.py          # Tree-sitter chunking
│   ├── context_generator.py    # LLM contextual descriptions for embeddings
│   ├── skill_classifier.py     # LLM skill detection
│   └── skill_taxonomy.py       # 11 domains, 50+ skills hierarchy
├── qa/
│   ├── agent.py                # ReAct agent with evidence curation
│   └── tools.py                # 6 tools (search, evidence, gaps, etc.)
└── jd_match/
    ├── agent.py                # Job description match agent
    ├── parser.py               # Requirement extraction
    └── matcher.py              # Vector-based requirement matching
```

## License

MIT
