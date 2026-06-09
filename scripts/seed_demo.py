#!/usr/bin/env python3
"""Seed a small synthetic PROVE graph so a fresh clone shows a working app.

Creates a fictional engineer (Ada Lovelace), two repos, and a handful of code
snippets across a few skills — enough for the homepage, competency treemap, repo
overview, and evidence lookups to render. Vector search (search_code) needs
embeddings; pass --embed to compute them with the configured EMBED_PROVIDER
(requires an API key), otherwise the structural demo works with no key.

Usage:
    uv run python scripts/seed_demo.py            # structural only, no key needed
    uv run python scripts/seed_demo.py --embed    # also compute embeddings
    uv run python scripts/seed_demo.py --reset     # wipe graph first (DESTRUCTIVE)

Run against an empty Neo4j (e.g. a fresh `docker compose up -d`).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import Settings  # noqa: E402
from src.core.client_factory import build_clients  # noqa: E402

ENGINEER = "Ada Lovelace"

# skill -> (domain, category)
SKILLS = {
    "FastAPI": ("Backend Engineering", "Web Frameworks"),
    "PostgreSQL": ("Backend Engineering", "Databases"),
    "Testing": ("Software Engineering", "Quality"),
    "Async Programming": ("Software Engineering", "Concurrency"),
    "Prompt Engineering": ("AI & Machine Learning", "LLM Integration"),
}

# A claimed-but-unproven skill (shows the gap/claims styling in the treemap).
CLAIMED = ["Kubernetes"]

REPOS = {
    "analytical-engine": {"default_branch": "main", "private": False},
    "lovelace-notes": {"default_branch": "main", "private": False},
}

# (repo, file_path, snippet_name, start_line, language, skill, content, context)
SNIPPETS = [
    (
        "analytical-engine",
        "app/api.py",
        "create_routes",
        12,
        "python",
        "FastAPI",
        "def create_routes(app):\n    @app.get('/programs')\n    async def list_programs():\n        return await store.all()",
        "Defines FastAPI routes for an analytical-engine program registry, using async handlers and a storage abstraction.",
    ),
    (
        "analytical-engine",
        "app/api.py",
        "health",
        30,
        "python",
        "FastAPI",
        "@app.get('/healthz')\nasync def health():\n    return {'status': 'ok'}",
        "FastAPI health endpoint returning liveness status for orchestrator probes.",
    ),
    (
        "analytical-engine",
        "app/store.py",
        "ProgramStore",
        8,
        "python",
        "PostgreSQL",
        "class ProgramStore:\n    async def all(self):\n        return await self.pool.fetch('SELECT * FROM programs')",
        "Async PostgreSQL access layer using a connection pool to fetch program records.",
    ),
    (
        "analytical-engine",
        "app/store.py",
        "save",
        20,
        "python",
        "Async Programming",
        "async def save(self, program):\n    async with self.pool.acquire() as conn:\n        await conn.execute('INSERT INTO programs(src) VALUES($1)', program.src)",
        "Demonstrates async context management and connection pooling for safe concurrent database writes.",
    ),
    (
        "analytical-engine",
        "tests/test_api.py",
        "test_list_programs",
        5,
        "python",
        "Testing",
        "async def test_list_programs(client):\n    resp = await client.get('/programs')\n    assert resp.status_code == 200",
        "Async integration test verifying the programs endpoint returns 200 with seeded data.",
    ),
    (
        "analytical-engine",
        "tests/test_store.py",
        "test_save_roundtrip",
        9,
        "python",
        "Testing",
        "async def test_save_roundtrip(store):\n    await store.save(Program(src='print(1)'))\n    assert len(await store.all()) == 1",
        "Round-trip test covering the PostgreSQL save/fetch path with async fixtures.",
    ),
    (
        "lovelace-notes",
        "notes/summarize.py",
        "summarize_note",
        14,
        "python",
        "Prompt Engineering",
        "def summarize_note(text, llm):\n    prompt = f'Summarize in two sentences:\\n{text}'\n    return llm.complete(prompt)",
        "Prompt-engineering helper that builds a constrained summarization prompt for an LLM client.",
    ),
    (
        "lovelace-notes",
        "notes/summarize.py",
        "extract_tags",
        28,
        "python",
        "Prompt Engineering",
        "def extract_tags(text, llm):\n    prompt = 'Return 3 topic tags as JSON for:\\n' + text\n    return json.loads(llm.complete(prompt))",
        "Uses a structured-output prompt to extract topic tags as JSON from note text.",
    ),
    (
        "lovelace-notes",
        "tests/test_summarize.py",
        "test_summarize",
        6,
        "python",
        "Testing",
        "def test_summarize(fake_llm):\n    out = summarize_note('long text', fake_llm)\n    assert out",
        "Unit test for the summarizer using a fake LLM stub to assert non-empty output.",
    ),
    (
        "lovelace-notes",
        "notes/server.py",
        "serve",
        4,
        "python",
        "FastAPI",
        "def serve():\n    app = FastAPI()\n    app.include_router(notes_router)\n    return app",
        "Wires a FastAPI application for the notes service via a modular router.",
    ),
]


def proficiency_for(snippet_count: int, repo_count: int) -> str:
    if snippet_count >= 10 and repo_count >= 2:
        return "extensive"
    if snippet_count >= 3:
        return "moderate"
    if snippet_count >= 1:
        return "minimal"
    return "none"


def seed(session, reset: bool):
    if reset:
        session.run("MATCH (n) DETACH DELETE n")

    session.run("MERGE (e:Engineer {name: $n})", n=ENGINEER)
    for repo, props in REPOS.items():
        session.run(
            "MERGE (r:Repository {name: $repo}) SET r += $props "
            "MERGE (e:Engineer {name: $eng}) MERGE (e)-[:OWNS]->(r)",
            repo=repo,
            props=props,
            eng=ENGINEER,
        )

    for skill, (domain, category) in SKILLS.items():
        session.run(
            "MERGE (d:Domain {name: $d}) MERGE (c:Category {name: $c}) MERGE (s:Skill {name: $s}) "
            "MERGE (d)-[:CONTAINS]->(c) MERGE (c)-[:CONTAINS]->(s)",
            d=domain,
            c=category,
            s=skill,
        )

    for snip in SNIPPETS:
        repo, path, name, line, lang, skill, content, context = snip
        session.run(
            "MERGE (r:Repository {name: $repo}) "
            "MERGE (f:File {path: $path}) MERGE (r)-[:CONTAINS]->(f) "
            "MERGE (cs:CodeSnippet {name: $name, file_path: $path}) "
            "SET cs.content = $content, cs.context = $context, cs.start_line = $line, "
            "    cs.end_line = $end, cs.language = $lang "
            "MERGE (f)-[:CONTAINS]->(cs) "
            "MERGE (s:Skill {name: $skill}) MERGE (cs)-[:DEMONSTRATES]->(s)",
            repo=repo,
            path=path,
            name=name,
            content=content,
            context=context,
            line=line,
            end=line + content.count("\n"),
            lang=lang,
            skill=skill,
        )

    # Rollups: per-skill proficiency/counts + per-repo DEMONSTRATES edges.
    for skill in SKILLS:
        row = session.run(
            "MATCH (cs:CodeSnippet)-[:DEMONSTRATES]->(s:Skill {name: $s}) "
            "MATCH (r:Repository)-[:CONTAINS]->(:File)-[:CONTAINS]->(cs) "
            "RETURN count(DISTINCT cs) AS snippets, count(DISTINCT r) AS repos",
            s=skill,
        ).single()
        prof = proficiency_for(row["snippets"], row["repos"])
        session.run(
            "MATCH (s:Skill {name: $s}) SET s.proficiency = $p, s.snippet_count = $sc, s.repo_count = $rc",
            s=skill,
            p=prof,
            sc=row["snippets"],
            rc=row["repos"],
        )
    session.run(
        "MATCH (r:Repository)-[:CONTAINS]->(:File)-[:CONTAINS]->(cs:CodeSnippet)-[:DEMONSTRATES]->(s:Skill) "
        "WITH r, s, count(cs) AS sc MERGE (r)-[d:DEMONSTRATES]->(s) SET d.snippet_count = sc"
    )

    for skill in CLAIMED:
        session.run(
            "MERGE (s:Skill {name: $s}) MERGE (e:Engineer {name: $eng}) MERGE (e)-[:CLAIMS]->(s)",
            s=skill,
            eng=ENGINEER,
        )


def add_embeddings(session, embed_client, embed_property: str):
    rows = session.run(
        "MATCH (cs:CodeSnippet) WHERE cs.context IS NOT NULL "
        "RETURN cs.name AS name, cs.file_path AS fp, cs.context AS ctx, cs.content AS content"
    ).data()
    for r in rows:
        vector = embed_client.embed([f"{r['ctx']}\n\n{r['content']}"])[0]
        session.run(
            f"MATCH (cs:CodeSnippet {{name: $name, file_path: $fp}}) SET cs.{embed_property} = $v",
            name=r["name"],
            fp=r["fp"],
            v=vector,
        )
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed", action="store_true", help="compute embeddings (needs API key)")
    parser.add_argument("--reset", action="store_true", help="wipe the graph first (DESTRUCTIVE)")
    args = parser.parse_args()

    settings = Settings.load()
    clients = build_clients(settings)
    neo4j = clients["neo4j_client"]
    neo4j.init_schema()

    with neo4j.driver.session() as session:
        seed(session, args.reset)
        n_skills = len(SKILLS)
        n_snips = len(SNIPPETS)
        if args.embed:
            n = add_embeddings(session, clients["embed_client"], neo4j.embed_property)
            print(f"Embedded {n} snippets ({neo4j.embed_property}).")

    print(
        f"Seeded demo graph: {ENGINEER}, {len(REPOS)} repos, {n_snips} snippets, {n_skills} skills."
    )
    print("Start the app with `just dev` and open http://127.0.0.1:7860")
    neo4j.close()


if __name__ == "__main__":
    main()
