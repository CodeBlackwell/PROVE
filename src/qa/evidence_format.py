"""Pure formatting helpers for QA answers and evidence display.

Extracted from agent.py so the agent module holds orchestration (ReAct loop,
tools, curation) and this module holds display logic. All functions here are
pure — no Neo4j, no LLM, no logger — and are covered by tests/test_qa.py.
"""

import re

MAX_EVIDENCE_SHOWN = 5
PROFICIENCY_WEIGHT = {"extensive": 3, "moderate": 2, "minimal": 1, "none": 0}


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _trim_answer(text: str, max_sentences: int = 6) -> str:
    """Trim verbose LLM answers to max_sentences.

    Architecture responses (mermaid diagrams) and structured responses
    (headers, bullet lists) are returned untrimmed.
    """
    if not text:
        return text
    # Never trim architecture responses with mermaid diagrams
    if "```mermaid" in text:
        return text
    # Never trim structured responses — the model used headers/lists intentionally
    # (e.g. weakness analysis, comparison answers)
    if "\n#" in text or "\n- " in text:
        return text
    # Otherwise cap by sentence count
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > max_sentences:
        return " ".join(sentences[:max_sentences])
    return text


def _compute_confidence(evidence: list[dict]) -> str:
    count = len(evidence)
    if count == 0:
        return "None"
    proficiencies = [e.get("proficiency") for e in evidence if e.get("proficiency")]
    if "extensive" in proficiencies:
        return "Strong"
    scores = [e["score"] for e in evidence if "score" in e]
    avg = sum(scores) / len(scores) if scores else 0
    if count >= 3 and avg >= 0.5:
        return "Strong"
    if avg >= 0.3:
        return "Partial"
    return "None"


def _sort_evidence(evidence: list[dict]) -> list[dict]:
    """Sort evidence by quality, then diversify across repos and files.

    First ranks by proficiency + score, deduplicates by file path (keeps
    best per file), then interleaves results from different repos so the
    curator sees variety rather than 20 snippets from the same skill.
    """
    ranked = sorted(
        evidence,
        key=lambda e: (
            PROFICIENCY_WEIGHT.get(e.get("proficiency", ""), 0),
            e.get("score", 0),
        ),
        reverse=True,
    )

    # Deduplicate by file — keep best snippet per file
    seen_files: set[str] = set()
    deduped = []
    for e in ranked:
        fp = e.get("file_path", "")
        if fp not in seen_files:
            seen_files.add(fp)
            deduped.append(e)

    # Interleave by repo to ensure diversity
    by_repo: dict[str, list[dict]] = {}
    for e in deduped:
        by_repo.setdefault(e.get("repo", "unknown"), []).append(e)

    diversified = []
    queues = list(by_repo.values())
    idx = 0
    while queues:
        queue = queues[idx % len(queues)]
        diversified.append(queue.pop(0))
        if not queue:
            queues.remove(queue)
        else:
            idx += 1

    return diversified


def _github_link(e: dict, github_owner: str = "codeblackwell") -> str:
    repo = e.get("repo", "")
    fp = e.get("file_path", "unknown")
    start = e.get("start_line", 0)
    if repo:
        return f"[{repo}/{fp}#L{start}](https://github.com/{github_owner}/{repo}/blob/main/{fp}#L{start})"
    return f"`{fp}:L{start}`"


def format_response(
    answer: str,
    evidence: list[dict],
    annotations: list[str] | None = None,
    curation: list[dict] | None = None,
    total_count: int | None = None,
    show_private_code: bool = False,
    github_owner: str = "codeblackwell",
) -> str:
    shown = evidence[:MAX_EVIDENCE_SHOWN]
    total = total_count if total_count is not None else len(evidence)
    lines = [answer, ""]
    if shown:
        lines.append("\n**Evidence:**")
        for i, e in enumerate(shown):
            link = _github_link(e, github_owner)
            cur = curation[i] if curation and i < len(curation) else None

            # Force "link" mode for private repo evidence unless owner opted in
            force_link = e.get("private") and not show_private_code

            if force_link or (cur and cur.get("mode") == "link"):
                explanation = (
                    cur["explanation"] if cur and cur.get("explanation") else e.get("context", "")
                )
                lines.append(f"\n{link}")
                if force_link:
                    lines.append("`[CODE REDACTED — PRIVATE REPO]`")
                if explanation:
                    lines.append(f"> {explanation}")
            else:
                content = e.get("content", "")
                ctx = e.get("context", "")
                explanation = (
                    cur["explanation"]
                    if cur
                    else (annotations[i] if annotations and i < len(annotations) else "")
                )
                if not explanation and ctx:
                    explanation = ctx
                lines.append(f"\n{link}")
                if explanation:
                    lines.append(f"> {explanation}")
                lines.append(f"```\n{content}\n```")
    confidence = _compute_confidence(evidence)
    lines.append(f"\nConfidence: {confidence} ({total} code example{'s' if total != 1 else ''})")
    return "\n".join(lines)
