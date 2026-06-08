# PROVE — OSS Maturity Gap Analysis

> Senior-engineering review of PROVE as an open-source project.
> Scope: reusability, OSS hygiene, testing, code structure, and positioning.
> Date: 2026-06-05 · Reviewed against commit `b912cc9`.

This document records (1) a **scoring matrix** of maturity dimensions and (2) a
**prioritized, actionable checklist**. Every finding cites a concrete file or
the absence of one so it can be verified and closed.

> **Progress (2026-06-08):** P0 hygiene complete (CI, ruff, mypy, pre-commit,
> community-health files, log cleanup, README split). P1 reusability landed via
> the *config-driven, keep-defaults* approach (`subject.toml`). Remaining: full
> asset decouple (deferred), testcontainers (P2), and the RAG eval set (P2).
> Completed items are checked off below.

---

## 1. Scoring Matrix

Scale: 🔴 missing/blocking · 🟡 partial/needs work · 🟢 solid.
Effort: S (<½ day) · M (1–2 days) · L (multi-day).

| # | Dimension | State | Severity | Effort | Evidence / Gap |
|---|-----------|:-----:|:--------:|:------:|----------------|
| 1 | **Reusability (multi-subject)** | 🔴 | Blocking | L | Subject identity hard-coded: name rules in `src/qa/agent.py:39`, `github_owner="codeblackwell"` default in `settings.py:39` + `agent.py:245,256,319`, domain/URLs in `src/app.py`. Cannot be run for another person without editing code. |
| 2 | **Continuous Integration** | 🔴 | Blocking | S | No `.github/workflows/`. No automated lint/test/build on push or PR. |
| 3 | **Lint / format / typecheck** | 🔴 | High | S | No ruff/black/mypy/pyright config in `pyproject.toml`. No `.pre-commit-config.yaml`. |
| 4 | **Test runnability (fresh clone)** | 🔴 | High | M | Unit tests require a live Neo4j (`test_qa.py`, `test_ingestion.py`, `test_jd_match.py`, `test_api_repos.py`). No testcontainers, no mocking at the `neo4j_client` boundary. |
| 5 | **E2E test isolation** | 🟡 | Medium | S | ~2,500 lines of Playwright target live `localhost:7860` (`tests/e2e/conftest.py:17`), unmarked, so they pollute the default `pytest` run. |
| 6 | **Coverage measurement** | 🔴 | Medium | S | No `pytest-cov`, no coverage reporting or threshold. |
| 7 | **RAG / answer-quality eval** | 🔴 | High | M | README claims A/B results (Haiku vs Sonnet) but no eval harness or golden-question set in repo. Highest-value missing artifact given the product. |
| 8 | **Community health files** | 🔴 | Medium | S | No `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, or `.github/ISSUE_TEMPLATE/`. Contributing = 2 lines in README. |
| 9 | **README scope** | 🟢 | — | — | Split 2026-06-08: lean 214-line README (hook + one diagram + quickstart + docs index); deep dives in `docs/`. |
| 10 | **Committed noise / artifacts** | 🟡 | Medium | S | Tracked: `ingestion.log`, `ingestion2.log`, `.DS_Store` (multiple). `*.log`/`.DS_Store` not in `.gitignore`. |
| 11 | **Personal artifacts in repo** | 🔴 | High | S | `LB_resume_2025.pdf`, `portfolio/` (a full second website), `portfolio/LeChristopher_Blackwell_Resume.pdf` ship in the repo — couples the tool to one person's infra. |
| 12 | **Module size / separation** | 🟡 | Medium | M | `src/app.py` (655 LOC) and `src/qa/agent.py` (669 LOC) are god modules mixing concerns. Exceeds the project's own 200-line norm. |
| 13 | **Health / readiness endpoint** | 🔴 | Medium | S | No `/healthz` checking Neo4j connectivity for the Docker/Caddy stack. |
| 14 | **DB migrations** | 🟡 | Low | M | SQLite schema created inline in `src/core/db.py`; no migration path. Acceptable now, undocumented as a limitation. |
| 15 | **Demo / seed dataset** | 🔴 | Medium | M | No anonymized seed graph. Cannot evaluate without first ingesting real data. No "clone → see it work" path. |
| 16 | **Secrets hygiene** | 🟢 | — | — | `.env` gitignored, `.env.example` present, `scripts/scrub_secrets.py` exists, rate limiting + fingerprinting in place. |
| 17 | **Deploy / infra** | 🟢 | — | — | Dockerfile, prod compose, Caddy, `scripts/deploy.sh`, backup/restore, Terraform in `infra/`. Solid. |
| 18 | **Observability (logging)** | 🟢 | — | — | Structured logger with per-model cost accounting, JSONL + SQLite sinks (`src/core/logger.py`). |
| 19 | **Provider abstraction** | 🟢 | — | — | Dual-provider client factory with shared `.chat()` interface; deliberate model tiering, documented. |
| 20 | **License** | 🟢 | — | — | Modified MIT (`LICENSE`) present and referenced. |

**Tally:** 🔴 9 · 🟡 5 · 🟢 6. The bones (16–20) are solid; the gaps cluster in
reusability (1, 11, 15) and OSS engineering hygiene (2–8).

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

- [ ] Make unit tests run with zero external services (testcontainers Neo4j or mock the client boundary).
- [ ] Mark E2E tests `@pytest.mark.e2e`; exclude from default `pytest`; add a gated CI job.
- [ ] Add `pytest-cov`; report coverage in CI; set a baseline threshold.
- [ ] Build a RAG eval set: golden questions → expected skills/repos cited.
- [ ] Add an eval runner script + document the Haiku-vs-Sonnet claim with reproducible numbers.

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

1. **Make the subject configurable** — removes the single-tenant ceiling (P1).
2. **CI + ruff + tests that run without Neo4j** — removes the "not maintained-grade" signal (P0/P2).
3. **Ship a RAG eval set** — turns quality claims into evidence, fitting for the product (P2).

---

## 5. Strengths (do not regress)

Dual-provider client factory · deliberate model tiering with documented rationale ·
rate limiting + fingerprinting · structured cost-accounting logger ·
`.env.example` + gitignored `.env` + `scrub_secrets.py` · Terraform infra ·
backup/restore + sync scripts · modified-MIT license.
