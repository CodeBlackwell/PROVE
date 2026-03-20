"""Ingest remaining repos and link OWNS edges."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import Settings
from src.core import HaikuClient, Neo4jClient, NimClient
from src.ingestion.graph_builder import build_graph
from src.ingestion.skill_taxonomy import TAXONOMY

REPOS_DIR = Path(__file__).resolve().parent.parent / "repos"


def main():
    settings = Settings.load()
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    nim = NimClient(settings.nvidia_api_key)
    haiku = HaikuClient(settings.anthropic_api_key)

    neo4j.init_schema()
    neo4j.ensure_taxonomy(TAXONOMY)

    # Get engineer name
    with neo4j.driver.session() as session:
        eng = session.run("MATCH (e:Engineer) RETURN e.name AS name LIMIT 1").single()
    engineer_name = eng["name"] if eng else "Unknown"
    print(f"Engineer: {engineer_name}")

    for repo_dir in sorted(REPOS_DIR.iterdir()):
        if not repo_dir.is_dir():
            continue
        print(f"\n=== {repo_dir.name} ===")
        build_graph(repo_dir, neo4j, nim, haiku)
        with neo4j.driver.session() as session:
            session.run(
                "MATCH (e:Engineer {name: $eng}), (r:Repository {name: $repo}) "
                "MERGE (e)-[:OWNS]->(r)",
                eng=engineer_name, repo=repo_dir.name,
            )
        print(f"  Done: {repo_dir.name}")

    neo4j.close()
    print("\n=== ALL DONE ===")


if __name__ == "__main__":
    main()
