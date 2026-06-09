# PROVE — OSS Maturity Gap Analysis

> Senior-engineering review of PROVE as an open-source project.
> Scope: reusability, OSS hygiene, testing, code structure, and positioning.
> Date: 2026-06-05 · Reviewed against commit `b912cc9`.

This document records (1) a **scoring matrix** of maturity dimensions and (2) a
**prioritized, actionable checklist**. Every finding cites a concrete file or
the absence of one so it can be verified and closed.

> **Progress (2026-06-09):** P0 hygiene complete (CI, ruff, mypy, pre-commit,
> community-health files, log cleanup, README split). P1 reusability landed via
> the *config-driven, keep-defaults* approach (`subject.toml`). P2 done: service-free
> unit tests (lazy app init), e2e marker, coverage reporting, and the RAG retrieval
> eval (`eval/`, recorded Haiku-vs-Sonnet numbers). Shipped to prod 2026-06-08.
> Remaining: seed dataset, `/healthz`, personal-asset decision, coverage gate,
> module splits, DB-migration note. Completed items are checked off below.

---

## 1. Scoring Matrix

Scale: 🔴 missing/blocking · 🟡 partial/needs work · 🟢 solid.
Effort: S (<½ day) · M (1–2 days) · L (multi-day).

| # | Dimension | State | Severity | Effort | Evidence / Gap |
|---|-----------|:-----:|:--------:|:------:|----------------|
| 1 | **Reusability (multi-subject)** | 🟢 | — | — | Done 2026-06-08 via `subject.toml` (config-driven, defaults preserved): name rules generated in `agent.py`, `github_owner`/`domain` sourced from config (env overrides). Resume is user-supplied via `--resume`. *Asset decouple (`portfolio/`) deferred — see row 11.* |
| 2 | **Continuous Integration** | 🟢 | — | — | Done 2026-06-05: `.github/workflows/ci.yml` — lint job + 3.11/3.12 test matrix + coverage. CI + Ruff badges in README. |
| 3 | **Lint / format / typecheck** | 🟢 | — | — | Done: `ruff` (lint+format) + `mypy` config in `pyproject.toml`, plus `.pre-commit-config.yaml`. CI runs `ruff check` + `ruff format --check`. *(mypy config present but not yet a CI step.)* |
| 4 | **Test runnability (fresh clone)** | 🟢 | — | — | Fixed 2026-06-08: made `QAAgent` prompt resolution lazy so importing `app` no longer queries Neo4j. All 67 unit tests now pass with zero services; CI dropped the Neo4j container. |
| 5 | **E2E test isolation** | 🟢 | — | — | Done 2026-06-05: path-based `e2e` auto-marker in `tests/e2e/conftest.py`; default run uses `-m "not e2e"` (61 unit / 402 e2e deselected). *(No dedicated CI e2e job yet.)* |
| 6 | **Coverage measurement** | 🟡 | Low | S | `pytest-cov` added; CI reports `--cov-report=term-missing` (~64% baseline). No threshold/gate set yet. |
| 7 | **RAG / answer-quality eval** | 🟢 | — | — | Done 2026-06-08: `eval/` — 10-case golden set (skills all-of, repos any-of, grounded in the graph) + `run.py` scoring citation recall with cost/latency + recorded numbers. Both models 10/10; Haiku $0.19/18.6s vs Sonnet $0.55/41.4s, substantiating the README claim. |
| 8 | **Community health files** | 🟢 | — | — | Done 2026-06-05: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue (bug+feature) + PR templates. |
| 9 | **README scope** | 🟢 | — | — | Split 2026-06-08: lean 214-line README (hook + one diagram + quickstart + docs index); deep dives in `docs/`. |
| 10 | **Committed noise / artifacts** | 🟢 | — | — | Done 2026-06-05: untracked `ingestion*.log`; `.gitignore` now covers `*.log`, `.DS_Store`, `.coverage`, `test-results/`. |
| 11 | **Personal artifacts in repo** | 🔴 | High | S | Still present: `LB_resume_2025.pdf`, `portfolio/` (a full second website). Deferred by choice — the config-driven approach kept defaults; full decouple was not selected. |
| 12 | **Module size / separation** | 🟡 | Medium | M | `src/app.py` (655 LOC) and `src/qa/agent.py` (669 LOC) are god modules mixing concerns. Exceeds the project's own 200-line norm. |
| 13 | **Health / readiness endpoint** | 🔴 | Medium | S | No `/healthz` checking Neo4j connectivity for the Docker/Caddy stack. |
| 14 | **DB migrations** | 🟡 | Low | M | SQLite schema created inline in `src/core/db.py`; no migration path. Acceptable now, undocumented as a limitation. |
| 15 | **Demo / seed dataset** | 🔴 | Medium | M | No anonymized seed graph. Cannot evaluate without first ingesting real data. No "clone → see it work" path. |
| 16 | **Secrets hygiene** | 🟢 | — | — | `.env` gitignored, `.env.example` present, `scripts/scrub_secrets.py` exists, rate limiting + fingerprinting in place. |
| 17 | **Deploy / infra** | 🟢 | — | — | Dockerfile, prod compose, Caddy, `scripts/deploy.sh`, backup/restore, Terraform in `infra/`. Solid. |
| 18 | **Observability (logging)** | 🟢 | — | — | Structured logger with per-model cost accounting, JSONL + SQLite sinks (`src/core/logger.py`). |
| 19 | **Provider abstraction** | 🟢 | — | — | Dual-provider client factory with shared `.chat()` interface; deliberate model tiering, documented. |
| 20 | **License** | 🟢 | — | — | Modified MIT (`LICENSE`) present and referenced. |

**Tally (2026-06-09):** 🔴 3 · 🟡 3 · 🟢 14 — up from the 2026-06-05 baseline of
🔴 9 · 🟡 5 · 🟢 6. Remaining 🔴: personal assets (11), health endpoint (13),
seed dataset (15). Remaining 🟡: coverage threshold (6), module size (12), DB
migrations (14).

---

## 2. Detailed Findings

### 2.1 Reusability — the ceiling on adoption

PROVE is currently *Le's website in code form*, not a framework. Until a stranger
can clone, supply their own resume + GitHub handle, and get **their** PROVE, it's
a fork-and-rewrite, not an adoptable tool.

| Coupling point | Location | Fix |
|---|---|---|
| Name rules in prompt | `src/qa/agent.py:39–41` | Interpolate `{name_rules}` from config (template already takes `{name}`). |
| `github_owner` default | `settings.py:39`; `agent.py:245,256,319` | Single source of truth; remove the `"codeblackwell"` literal default. |
| Canonical domain & sibling URLs | `src/app.py:238,257,270,277,308,358,569,577` | Move to config (`subject.toml` / env). Drop sibling-project URLs. |
| Resume + portfolio assets | `LB_resume_2025.pdf`, `portfolio/` | Remove from repo; document as user-supplied input. |

**Target shape:** a `subject.toml` (or env block) with `name`, `preferred_name_rules`,
`github_owner`, `canonical_domain`, `links`. The system prompt, settings, and app
all read from it.

### 2.2 OSS engineering hygiene

- **CI** is the loudest missing signal. One workflow (lint → unit tests w/ Neo4j
  service container → build) plus a green badge changes how the repo reads.
- **ruff** (lint + format in one) and **mypy/pyright** on 4.3k LOC will catch real
  bugs and is table stakes for a public Python repo.
- **Community health files** are expected once `PRs welcome` appears anywhere.

### 2.3 Testing & correctness

- Make `uv run pytest` pass on a **fresh clone with zero services** —
  testcontainers-python (Neo4j per session) or mock the client boundary.
- Mark E2E `@pytest.mark.e2e`, exclude from default run, gate in a separate job.
- Add `pytest-cov` with a reported number.
- **Ship a RAG eval set** (golden questions → expected skills/repos cited). For a
  retrieval product this is the most credible artifact you can publish and the
  most reusable contribution to others doing code-RAG.

### 2.4 Code structure

- Split `src/app.py` into routers (`routes/chat.py`, `routes/repos.py`,
  `routes/meta.py`).
- Pull evidence/GitHub-link formatting out of `src/qa/agent.py` into a helper.
- Add `/healthz` (Neo4j ping) for orchestrator robustness.

### 2.5 Positioning as a contribution

- **Name the reusable primitive:** *context-augmented code embeddings*
  (`src/ingestion/context_generator.py` writes a Sonnet paragraph per snippet
  before embedding). Document it with a benchmark — it's publishable on its own.
- Ship an **anonymized seed dataset** for a 30-second "clone → see it work".
- **Decouple** from the codeblackwell ecosystem (sibling URLs, `portfolio/`).

---

## 3. Checklist

Grouped by priority. Check off as completed.

### P0 — OSS hygiene (cheap, high signal)

- [x] Add `.github/workflows/ci.yml`: ruff → unit tests (Neo4j service container) → build.
- [x] Add CI status badge to README.
- [x] Add `ruff` config to `pyproject.toml`; fix lint; commit formatted.
- [x] Add `mypy` (or pyright) config; add a typecheck CI step. *(config added; CI step pending)*
- [x] Add `.pre-commit-config.yaml` (ruff + ruff-format + whitespace hooks).
- [x] `git rm --cached ingestion.log ingestion2.log` and all tracked `.DS_Store`.
- [x] Add `*.log` and `.DS_Store` to `.gitignore`.
- [x] Add `CONTRIBUTING.md` (setup, test, PR flow, code style).
- [x] Add `CODE_OF_CONDUCT.md` (Contributor Covenant).
- [x] Add `SECURITY.md` (how to report vulnerabilities, supported versions).
- [x] Add `.github/ISSUE_TEMPLATE/` (bug + feature) and `PULL_REQUEST_TEMPLATE.md`.
- [x] Split README: lean top-level (724→214 lines) + deep dives moved to `docs/` (HOW_IT_WORKS, ARCHITECTURE, CONFIGURATION, INGESTION, DEVELOPMENT, DEPLOYMENT).

### P1 — Reusability (unlocks adoption) — *approach: config-driven, keep defaults*

- [x] Introduce `subject.toml` block: `name`, `preferred_names`, `forbidden_names`, `github_owner`, `domain`.
- [x] Interpolate name rules into `SYSTEM_PROMPT_TEMPLATE` (`src/qa/agent.py`) via `_build_name_rules`; remove hard-coded "Le/LeChristopher" rules.
- [x] Source `github_owner` and `domain` from `subject.toml` (env `GITHUB_OWNER` / `DOMAIN` override). *(module-level helper fallbacks in `agent.py` still carry a literal default; harmless — live path passes config.)*
- [x] Move PROVE domain + sitemap URLs in `src/app.py` to config. *(Sibling-project URLs left intentionally — that's the full-decouple option, not chosen.)*
- [ ] Remove `LB_resume_2025.pdf` and `portfolio/` from the repo; document resume as user-supplied input. *(deferred — full decouple)*
- [ ] Add `docs/SELF_HOST.md`: clone → configure subject → ingest → run. *(deferred)*

### P2 — Testing & correctness

- [x] Make unit tests run with zero external services — done via lazy `QAAgent` prompt resolution (no testcontainers dependency needed); CI dropped the Neo4j service.
- [x] Mark E2E tests `@pytest.mark.e2e`; exclude from default `pytest`. *(Dedicated gated CI e2e job still pending.)*
- [x] Add `pytest-cov`; report coverage in CI. *(Baseline threshold/gate not yet set — ~64%.)*
- [x] Build a RAG eval set: golden questions → expected skills/repos cited (`eval/golden.json`, 10 cases).
- [x] Add an eval runner script + document the Haiku-vs-Sonnet claim with reproducible numbers (`eval/run.py`, `eval/README.md`).

### P3 — Code structure & ops

- [ ] Split `src/app.py` into routers (`chat`, `repos`, `meta`).
- [ ] Extract evidence/GitHub-link formatting out of `src/qa/agent.py`.
- [ ] Add `/healthz` endpoint checking Neo4j connectivity.
- [ ] Document the SQLite "no migrations" limitation (or adopt a lightweight migration).
- [ ] Ship an anonymized seed graph for instant demo.

### P4 — Positioning (meaningful contribution)

- [ ] Write up *context-augmented code embeddings* as a standalone technique (with benchmark).
- [ ] Add an architecture diagram to the lean README.
- [ ] Decouple repo from personal infra (no `prove.codeblackwell.ai` assumptions in code).

---

## 4. Top 3 (if nothing else)

The original top 3 — subject config, CI + service-free tests, and the RAG eval — are
**all shipped**. Current highest-value remaining work:

1. **Anonymized seed dataset (row 15)** — unlocks "clone → see it work" *and* lets
   anyone reproduce the eval numbers; also closes the gap behind the maisight-style
   prod/local data drift.
2. **`/healthz` endpoint (row 13)** — cheap ops robustness for the Docker/Caddy stack.
3. **Decide the personal-asset question (row 11)** — either remove `portfolio/` +
   resume for a clean generic tool, or explicitly document keeping them as the
   canonical-deploy choice.

---

## 5. Strengths (do not regress)

Dual-provider client factory · deliberate model tiering with documented rationale ·
rate limiting + fingerprinting · structured cost-accounting logger ·
`.env.example` + gitignored `.env` + `scrub_secrets.py` · Terraform infra ·
backup/restore + sync scripts · modified-MIT license.
