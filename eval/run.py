"""Retrieval eval for PROVE: run golden questions against the live graph, score citations.

Scores whether each answer cites the expected skills (ALL must appear) and a
relevant repo (ANY ONE must appear). Reports pass rate, latency, and cost — use
it to compare query models (e.g. Haiku vs Sonnet) on the same questions.

Usage:
    uv run python eval/run.py                          # anthropic + voyage, default model (Haiku)
    uv run python eval/run.py --model claude-sonnet-4-20250514
    uv run python eval/run.py --json eval/results-haiku.json

Requires a populated Neo4j and the relevant API keys. Makes real LLM calls.
"""

import argparse
import json
import time
from pathlib import Path

from src.config.settings import Settings
from src.core import logger
from src.core.client_factory import build_clients
from src.qa.agent import QAAgent

GOLDEN = Path(__file__).parent / "golden.json"


def score_case(answer: str, case: dict) -> dict:
    low = answer.lower()
    missing_skills = [s for s in case["expect_skills"] if s.lower() not in low]
    repos = case["expect_repos"]
    repo_ok = (not repos) or any(r.lower() in low for r in repos)
    return {
        "passed": not missing_skills and repo_ok,
        "missing_skills": missing_skills,
        "repo_ok": repo_ok,
    }


def run_case(agent: QAAgent, case: dict) -> dict:
    logger.start_session(query=case["question"], source="eval")
    started = time.perf_counter()
    answer = agent.answer(case["question"])
    wall_ms = int((time.perf_counter() - started) * 1000)
    summary = logger.end_session()
    result = score_case(answer, case)
    result.update(
        id=case["id"], wall_ms=wall_ms, cost_usd=round(summary.get("total_cost_usd", 0.0), 5)
    )
    return result


def build_agent(provider: str, embed_provider: str, model: str | None) -> QAAgent:
    settings = Settings.load()
    settings.chat_provider = provider
    settings.embed_provider = embed_provider
    if model:
        settings.claude_model = model
    clients = build_clients(settings)
    return QAAgent(
        clients["neo4j_client"],
        clients["chat_client"],
        clients["embed_client"],
        show_private_code=settings.show_private_code,
        github_owner=settings.github_owner,
        subject=settings.subject,
    )


def print_report(results: list[dict], model: str | None) -> None:
    print(f"\nPROVE retrieval eval — model={model or 'default (Haiku)'}\n")
    print(f"{'case':14} {'result':6} {'skills':7} {'repo':5} {'ms':>6} {'usd':>8}")
    print("-" * 50)
    for r in results:
        skills = "ok" if not r["missing_skills"] else "MISS"
        print(
            f"{r['id']:14} {'PASS' if r['passed'] else 'FAIL':6} {skills:7} "
            f"{'ok' if r['repo_ok'] else 'no':5} {r['wall_ms']:6d} {r['cost_usd']:8.4f}"
        )
    n = len(results)
    passed = sum(r["passed"] for r in results)
    print("-" * 50)
    print(
        f"pass: {passed}/{n} ({passed / n * 100:.0f}%)  "
        f"cost: ${sum(r['cost_usd'] for r in results):.4f}  "
        f"avg latency: {sum(r['wall_ms'] for r in results) // n} ms"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="anthropic")
    parser.add_argument("--embed-provider", default="voyage")
    parser.add_argument("--model", default=None, help="override CLAUDE_MODEL (query model)")
    parser.add_argument("--json", default=None, help="write per-case results to this path")
    args = parser.parse_args()

    cases = json.loads(GOLDEN.read_text())["cases"]
    agent = build_agent(args.provider, args.embed_provider, args.model)
    results = [run_case(agent, c) for c in cases]
    print_report(results, args.model)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
