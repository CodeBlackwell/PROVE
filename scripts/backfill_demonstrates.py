"""One-time backfill: create CodeSnippet-[:DEMONSTRATES]->Skill edges from existing data."""

from src.config.settings import get_settings
from src.core.neo4j_client import Neo4jClient
from src.ingestion.skill_keywords import SKILL_MAP


def main():
    settings = get_settings()
    client = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    with client.driver.session() as session:
        snippets = session.run(
            "MATCH (cs:CodeSnippet) RETURN cs.name AS name, cs.file_path AS fp, cs.content AS content"
        )
        created = 0
        for row in snippets:
            text = (row["content"] + " " + row["fp"]).lower()
            for skill, patterns in SKILL_MAP.items():
                if any(p.lower() in text for p in patterns):
                    session.run(
                        "MERGE (s:Skill {name: $skill}) WITH s "
                        "MATCH (cs:CodeSnippet {name: $name, file_path: $fp}) "
                        "MERGE (cs)-[:DEMONSTRATES]->(s)",
                        skill=skill, name=row["name"], fp=row["fp"],
                    )
                    created += 1
    print(f"Backfill complete: {created} DEMONSTRATES edges created")
    client.close()


if __name__ == "__main__":
    main()
