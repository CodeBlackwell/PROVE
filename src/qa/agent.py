import json
import re
from typing import Generator

from src.core.haiku_client import HaikuClient
from src.core.neo4j_client import Neo4jClient
from src.core.nim_client import NimClient
from src.qa.tools import search_code, get_evidence, search_resume, find_gaps
from src.ui.competency_map import get_subgraph

SYSTEM_PROMPT_TEMPLATE = (
    "You are a QA agent representing {name}'s software engineering portfolio. "
    "You have access to their resume data and code repositories indexed with vector embeddings.\n\n"
    "Skills use a 3-tier hierarchy (Domain > Category > Skill) with proficiency levels "
    "(extensive, moderate, minimal, none) based on code evidence.\n\n"
    "STRATEGY: Use search_code for broad queries, search_resume for work history, "
    "get_evidence for specific skills, find_gaps for weaknesses. "
    "Always make at least 2 tool calls before answering.\n\n"
    "ANSWER FORMAT: Write a 2-3 sentence high-level assessment only. "
    "Do NOT discuss individual files, code details, or list bullet points — "
    "a detailed evidence section with annotated code snippets is appended automatically. "
    "Focus on overall proficiency, skill breadth, and a brief summary. "
    "If no evidence exists, say so."
)


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _compute_confidence(evidence: list[dict]) -> str:
    count = len(evidence)
    if count == 0:
        return "None"
    # Boost for extensive proficiency
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

MAX_EVIDENCE_SHOWN = 3

PROFICIENCY_WEIGHT = {"extensive": 3, "moderate": 2, "minimal": 1, "none": 0}


def _sort_evidence(evidence: list[dict]) -> list[dict]:
    return sorted(evidence, key=lambda e: (
        PROFICIENCY_WEIGHT.get(e.get("proficiency", ""), 0),
        e.get("score", 0),
    ), reverse=True)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search indexed code repositories by semantic similarity. Use this to find code examples for any topic.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_evidence",
            "description": "Get code snippets demonstrating a specific skill, including proficiency level and date range.",
            "parameters": {
                "type": "object",
                "properties": {"skill_name": {"type": "string", "description": "Skill name"}},
                "required": ["skill_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_resume",
            "description": "Search resume data: engineer name, job roles/titles, companies, dates. Use for work history questions.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_gaps",
            "description": "Check which skills have code evidence with proficiency levels, which are only resume claims, and which are missing. Returns hierarchy-aware results with domain/category context.",
            "parameters": {
                "type": "object",
                "properties": {"skills_csv": {"type": "string", "description": "Comma-separated skill names to check"}},
                "required": ["skills_csv"],
            },
        },
    },
]

MAX_TOOL_CALLS = 3
MAX_TOOL_RESULT_CHARS = 4000


def _github_link(e: dict) -> str:
    repo = e.get("repo", "")
    fp = e.get("file_path", "unknown")
    start = e.get("start_line", 0)
    if repo:
        return f"[{repo}/{fp}#L{start}](https://github.com/codeblackwell/{repo}/blob/main/{fp}#L{start})"
    return f"`{fp}:L{start}`"


def format_response(answer: str, evidence: list[dict], annotations: list[str] | None = None, total_count: int | None = None) -> str:
    shown = evidence[:MAX_EVIDENCE_SHOWN]
    total = total_count if total_count is not None else len(evidence)
    lines = [answer, ""]
    if shown:
        lines.append("\n**Evidence:**")
        for i, e in enumerate(shown):
            content = e.get("content", "")
            link = _github_link(e)
            note = annotations[i] if annotations and i < len(annotations) else ""
            lines.append(f"\n{link}")
            if note:
                lines.append(f"> {note}")
            lines.append(f"```\n{content}\n```")
    confidence = _compute_confidence(evidence)
    lines.append(f"\nConfidence: {confidence} ({total} code example{'s' if total != 1 else ''})")
    return "\n".join(lines)


ANNOTATE_PROMPT = (
    "You will receive a user question and numbered code snippets. "
    "For each snippet, write 1-2 sentences explaining how it is relevant to the question. "
    "Reply ONLY with a JSON array of strings, one per snippet. No markdown, no explanation."
)


class QAAgent:
    def __init__(self, neo4j_client: Neo4jClient, nim_client: NimClient, haiku_client: HaikuClient | None = None):
        self.neo4j = neo4j_client
        self.nim = nim_client
        self.haiku = haiku_client
        self.system_prompt = self._resolve_prompt()

    def _resolve_prompt(self) -> str:
        with self.neo4j.driver.session() as session:
            result = session.run("MATCH (e:Engineer) RETURN e.name AS name LIMIT 1")
            record = result.single()
            name = record["name"] if record else "a software engineer"
        return SYSTEM_PROMPT_TEMPLATE.format(name=name)

    def _execute_tool(self, name: str, args: dict) -> str:
        dispatch = {
            "search_code": lambda: search_code(args["query"], self.neo4j, self.nim),
            "get_evidence": lambda: get_evidence(args["skill_name"], self.neo4j),
            "search_resume": lambda: search_resume(args["query"], self.neo4j, self.nim),
            "find_gaps": lambda: find_gaps(args["skills_csv"], self.neo4j),
        }
        result = dispatch.get(name, lambda: {"error": f"Unknown tool: {name}"})()
        return json.dumps(result)

    def _collect_entities(self, tool_name: str, args: dict, tool_result: str, entities: set):
        if tool_name == "get_evidence":
            entities.add(args.get("skill_name", ""))
        elif tool_name == "search_code":
            try:
                for item in json.loads(tool_result):
                    for skill in item.get("skills", []):
                        entities.add(skill)
            except (json.JSONDecodeError, TypeError):
                pass
        elif tool_name == "find_gaps":
            try:
                for item in json.loads(tool_result):
                    if item.get("skill"):
                        entities.add(item["skill"])
                    for rel in item.get("related_demonstrated", []):
                        entities.add(rel)
            except (json.JSONDecodeError, TypeError):
                pass

    def _collect_evidence(self, tool_result: str, evidence: list[dict]):
        try:
            parsed = json.loads(tool_result)
            if isinstance(parsed, list):
                evidence.extend(item for item in parsed if "file_path" in item)
        except (json.JSONDecodeError, TypeError):
            pass

    def _annotate_evidence(self, question: str, evidence: list[dict]) -> list[str] | None:
        if not self.haiku or not evidence:
            return None
        snippets = []
        for i, e in enumerate(evidence):
            fp = e.get("file_path", "?")
            preview = "\n".join(e.get("content", "").split("\n")[:8])
            snippets.append(f"{i + 1}. {fp}\n{preview}")
        user_msg = f"Question: {question}\n\nSnippets:\n" + "\n\n".join(snippets)
        try:
            raw = _strip_think(self.haiku.classify(ANNOTATE_PROMPT, user_msg))
            raw = re.sub(r"^```\w*\n|```$", "", raw.strip())
            return json.loads(raw)
        except (json.JSONDecodeError, Exception):
            return None

    def _assistant_msg(self, choice) -> dict:
        msg = {"role": "assistant", "content": choice.message.content}
        if choice.message.tool_calls:
            msg["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in choice.message.tool_calls
            ]
        return msg

    def answer(self, question: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
        ]
        all_evidence = []

        for _ in range(MAX_TOOL_CALLS):
            response = self.nim.chat(messages, tools=TOOL_DEFINITIONS)
            choice = response.choices[0]
            if not choice.message.tool_calls:
                sorted_ev = _sort_evidence(all_evidence)
                shown = sorted_ev[:MAX_EVIDENCE_SHOWN]
                annotations = self._annotate_evidence(question, shown)
                return format_response(_strip_think(choice.message.content or ""), sorted_ev, annotations, total_count=len(all_evidence))
            messages.append(self._assistant_msg(choice))
            for tc in choice.message.tool_calls:
                result = self._execute_tool(tc.function.name, json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result[:MAX_TOOL_RESULT_CHARS]})
                self._collect_evidence(result, all_evidence)

        response = self.nim.chat(messages)
        sorted_ev = _sort_evidence(all_evidence)
        shown = sorted_ev[:MAX_EVIDENCE_SHOWN]
        annotations = self._annotate_evidence(question, shown)
        return format_response(_strip_think(response.choices[0].message.content or ""), sorted_ev, annotations, total_count=len(all_evidence))

    def answer_stream(self, question: str) -> Generator[str | dict, None, None]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
        ]
        all_evidence = []
        entities: set[str] = set()

        for _ in range(MAX_TOOL_CALLS):
            response = self.nim.chat(messages, tools=TOOL_DEFINITIONS)
            choice = response.choices[0]
            if not choice.message.tool_calls:
                break
            messages.append(self._assistant_msg(choice))
            for tc in choice.message.tool_calls:
                yield f"Searching for: {tc.function.name}..."
                args = json.loads(tc.function.arguments)
                result = self._execute_tool(tc.function.name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result[:MAX_TOOL_RESULT_CHARS]})
                self._collect_evidence(result, all_evidence)
                self._collect_entities(tc.function.name, args, result, entities)
        else:
            response = self.nim.chat(messages)
            choice = response.choices[0]

        if entities:
            subgraph = get_subgraph(self.neo4j, list(entities))
            if subgraph["nodes"]:
                yield subgraph

        sorted_ev = _sort_evidence(all_evidence)
        shown = sorted_ev[:MAX_EVIDENCE_SHOWN]
        annotations = self._annotate_evidence(question, shown)
        yield format_response(_strip_think(choice.message.content or ""), sorted_ev, annotations, total_count=len(all_evidence))
