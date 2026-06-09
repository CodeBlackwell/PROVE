# Context-Augmented Code Embeddings

[← Back to README](../README.md) · See also [How It Works](HOW_IT_WORKS.md) · [Architecture](ARCHITECTURE.md)

This is the one idea in PROVE most worth stealing for any code-RAG system. It's
small, model-agnostic, and it's what makes semantic search over a codebase
actually work.

## The problem

Recruiters, hiring managers, and engineers search in **outcome vocabulary** —
"OAuth experience", "rate limiting", "event-driven architecture". Code is written
in **implementation vocabulary** — `refresh_token`, `TokenBucket`, `emit()`. The
words rarely overlap. Embedding raw code and querying it with natural language
leaves a semantic gap: the vector for `def refresh_token(client, token):` lands
nowhere near the vector for "OAuth experience", because the surface tokens share
almost nothing.

Naive fixes don't close it:
- **Embed the raw code** → misses intent and domain vocabulary.
- **Embed the file path / function name** → too sparse, often misleading.
- **Keyword search** → brittle; requires the searcher to guess identifiers.

## The technique

At **ingestion time** (once per snippet), have a strong model write a dense
*context paragraph* describing what the code proves, in the searcher's vocabulary.
Then embed **`context + metadata + raw code`** as a single document.

```
embedding_input = f"{llm_context}\n\n{metadata_preamble}\n\n{raw_code}"
vector = embed(embedding_input)
```

The context paragraph is deliberately structured to capture four things
(`src/ingestion/context_generator.py`):

1. **What it does** — business/system purpose
2. **Engineering patterns** — design techniques used
3. **Skill keywords** — restated in standard industry terms (aligned to a taxonomy)
4. **Quality signals** — error handling, concurrency safety, type safety

Example — for `def refresh_token(client, token): ...` the model writes:

> *"Implements OAuth2 refresh token rotation using the client credentials grant.
> Demonstrates secure token lifecycle management with automatic retry on network
> failure. Shows production patterns: exponential backoff, thread-safe token
> caching, structured error propagation."*

Now the snippet's vector sits near queries like "OAuth experience", "secure token
handling", and "retry logic" — because those words are literally in the embedded
document, grounded in the actual code.

## Why it works

- **Bridges the vocabulary gap** at write time, not query time — every future
  query benefits from one-time work.
- **Keeps the code in the vector** — context alone would lose implementation
  detail; concatenating preserves both intent *and* specifics.
- **Taxonomy-aligned** — feeding the skill taxonomy into the context generator
  keeps the vocabulary consistent with how skills are stored and searched, so
  retrieval and classification reinforce each other.
- **Amortizes model cost** — the expensive model runs once per snippet at
  ingestion (where quality is permanent), while queries use a cheap model. See
  [ARCHITECTURE.md](ARCHITECTURE.md#-model-strategy).

## Cost model

Context generation is a fixed, one-time cost per snippet, paid at ingestion and
amortized over every subsequent query. PROVE uses Sonnet for it (highest-leverage
LLM work in the system); embeddings are then computed once per provider and stored
on the node (`embedding_voyage` / `embedding_nim`). Re-embedding is idempotent and
**refuses to embed a snippet that has no context** (`scripts/reembed.py`), which
keeps the invariant "every vector includes context" true across the whole graph.

## Evidence

End-to-end, the [retrieval eval](../eval/README.md) shows the pipeline answers
known questions with correct citations: **10/10** golden cases cite the expected
skills and a relevant repo, on both Haiku and Sonnet query models. That validates
the full path (context-augmented retrieval → ReAct → curation), not the embedding
step in isolation.

### Suggested ablation (not yet run)

To isolate the contribution of context augmentation specifically, re-embed the
graph two ways and compare retrieval on the same golden set:

1. **Baseline** — embed `raw_code` only.
2. **Augmented** — embed `context + metadata + raw_code` (current behavior).

Then run `eval/run.py` against each and compare citation recall (and, ideally,
mean reciprocal rank of the expected snippet). The harness and golden set already
exist; the only missing piece is a `--embed-mode {raw,augmented}` switch in
`reembed.py`. This is the natural next benchmark and would turn the qualitative
argument above into a number.
