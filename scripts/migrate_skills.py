"""Retroactively classify existing CodeSnippets with Haiku and link to taxonomy.
Resumes from where it left off — skips snippets that already have DEMONSTRATES edges."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import dataclass

from src.config.settings import Settings
from src.core import HaikuClient, Neo4jClient
from src.ingestion.skill_classifier import classify_chunks, BATCH_SIZE
from src.ingestion.skill_taxonomy import TAXONOMY


@dataclass
class FakeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    name: str


def migrate():
    settings = Settings.load()
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    haiku = HaikuClient(settings.anthropic_api_key)

    neo4j.init_schema()
    neo4j.ensure_taxonomy(TAXONOMY)

    with neo4j.driver.session() as session:
        # Fetch only unclassified snippets (no DEMONSTRATES edges)
        records = list(session.run(
            "MATCH (cs:CodeSnippet) "
            "WHERE NOT (cs)-[:DEMONSTRATES]->() "
            "RETURN cs.name AS name, cs.file_path AS fp, "
            "cs.content AS content, cs.start_line AS start, cs.end_line AS end_line"
        ))
        print(f"Classifying {len(records)} unclassified snippets...")

        if not records:
            print("Nothing to migrate.")
            neo4j.close()
            return

        chunks = [
            FakeChunk(
                content=r["content"] or "",
                file_path=r["fp"] or "",
                start_line=r["start"] or 0,
                end_line=r["end_line"] or 0,
                name=r["name"] or "",
            )
            for r in records
        ]

        total_links = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            skills_per_chunk = classify_chunks(batch, haiku)
            for chunk, skills in zip(batch, skills_per_chunk):
                for skill in skills:
                    session.run(
                        "MERGE (s:Skill {name: $skill}) WITH s "
                        "MATCH (cs:CodeSnippet {name: $name, file_path: $fp}) "
                        "MERGE (cs)-[d:DEMONSTRATES]->(s) "
                        "SET d.snippet_lines = $lines",
                        skill=skill, name=chunk.name, fp=chunk.file_path,
                        lines=chunk.end_line - chunk.start_line + 1,
                    )
                    total_links += 1

            done = min(i + BATCH_SIZE, len(chunks))
            if done % 200 < BATCH_SIZE:
                print(f"  {done}/{len(chunks)} snippets classified ({total_links} links)")

    print(f"Migration complete: {total_links} DEMONSTRATES edges created")

    # Recompute rollups and proficiency
    with neo4j.driver.session() as session:
        repos = [r["name"] for r in session.run("MATCH (r:Repository) RETURN r.name AS name")]
    for repo in repos:
        neo4j.compute_repo_rollups(repo)
    neo4j.compute_proficiency()
    print("Rollups and proficiency computed")
    neo4j.close()


if __name__ == "__main__":
    migrate()
