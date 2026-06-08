# PROVE Retrieval Eval

A small, reproducible eval for the query pipeline: does PROVE cite the right
evidence for known questions, and how do query models compare on quality, latency,
and cost?

This is the artifact behind the README's claim that **Haiku matches Sonnet** for
the query task at a fraction of the cost.

## What it measures

[`golden.json`](golden.json) holds hand-written question → expectation pairs,
grounded in the live knowledge graph:

- **`expect_skills`** — skill names that **all** must appear in the answer. The
  agent retrieves evidence for the queried skill, so a correct answer always
  surfaces it.
- **`expect_repos`** — repos where that skill's strongest evidence lives; **any
  one** must appear (the curator picks which repo's snippets are most impressive,
  so we don't pin a single one).

A case **passes** when all expected skills and at least one expected repo are
cited. Scoring is case-insensitive substring matching against the final answer
(which embeds the curated evidence, GitHub links, and skill headers).

## Running it

Requires a populated Neo4j (`docker compose up -d` + an ingest) and API keys in
`.env`. Makes real LLM calls (a few cents per run).

```bash
# Default: anthropic + voyage, query model = Haiku 4.5
uv run python eval/run.py --json eval/results-haiku.json

# Same questions, Sonnet as the query model
uv run python eval/run.py --model claude-sonnet-4-20250514 --json eval/results-sonnet.json
```

Flags: `--provider` (default `anthropic`), `--embed-provider` (default `voyage`),
`--model` (override the query model), `--json` (write per-case results).

## Results

> Run against the live graph on 2026-06-08. `pass` = all expected skills + a
> relevant repo cited. Cost is the logged per-question spend; latency is wall-clock.

| Query model | Pass rate | Total cost (10 Qs) | Avg latency |
|-------------|-----------|-------------------:|------------:|
| Haiku 4.5   | 10/10 (100%) | $0.19 | 18.6 s |
| Sonnet      | 10/10 (100%) | $0.55 | 41.4 s |

**Takeaway:** Haiku matches Sonnet on this bar (both 10/10) while running **~2.9×
cheaper** and **~2.2× faster** — consistent with using Haiku as the query model and
spending Sonnet's budget on one-time ingestion instead.

_Per-case results are in `results-haiku.json` / `results-sonnet.json`._

## Limitations

- Substring matching can't catch a wrong-but-named citation; it measures recall of
  expected evidence, not precision. Good enough to catch retrieval regressions and
  compare models on the same bar.
- Needs the maintainer's graph to reproduce the numbers above. The harness itself
  is generic — point it at any populated PROVE instance with its own `golden.json`.
- No negative/gap cases yet (e.g. "does Le know Rust?" → should decline). Worth
  adding with an `expect_absent` field.
