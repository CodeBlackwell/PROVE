"""Replace the ingested resume with a new PDF, preserving the Engineer node and its repos.

Usage: uv run python scripts/reparse_resume.py /abs/path/to/resume.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import Settings
from src.core.client_factory import build_clients
from src.ingestion.resume_parser import parse_resume


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: reparse_resume.py /abs/path/to/resume.pdf")
    new_resume = sys.argv[1]

    clients = build_clients(Settings.load())
    neo4j = clients["neo4j_client"]
    chat = clients["ingestion_chat_client"]

    with neo4j.driver.session() as session:
        eng = session.run("MATCH (e:Engineer) RETURN e.name AS name LIMIT 1").single()
        if not eng:
            sys.exit("No Engineer node found — run a full ingestion first.")
        name = eng["name"]
        # Drop old resume-derived structure; keep the Engineer node and its OWNS edges.
        session.run("MATCH (:Engineer)-[c:CLAIMS]->(:Skill) DELETE c")
        session.run("MATCH (:Engineer)-[:HELD]->(r:Role) DETACH DELETE r")
        session.run("MATCH (co:Company) WHERE NOT (co)<-[:AT]-() DETACH DELETE co")

    parse_resume(new_resume, neo4j, chat, engineer_name=name)

    with neo4j.driver.session() as session:
        row = session.run(
            "MATCH (e:Engineer {name: $n}) "
            "RETURN size([(e)-[:HELD]->(r) | r]) AS roles, "
            "size([(e)-[:CLAIMS]->(s) | s]) AS claims",
            n=name,
        ).single()
    print(f"Resume updated for {name}: {row['roles']} roles, {row['claims']} claims")
    neo4j.close()


if __name__ == "__main__":
    main()
