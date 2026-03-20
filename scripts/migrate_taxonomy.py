"""Migrate existing graph data to taxonomy hierarchy.

Run after upgrading to taxonomy-based skill classification:
  python scripts/migrate_taxonomy.py
"""
from src.config.settings import Settings
from src.core import Neo4jClient
from src.ingestion.skill_taxonomy import TAXONOMY


def migrate():
    settings = Settings.load()
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)

    print("1. Creating schema constraints...")
    neo4j.init_schema()

    print("2. Building Domain → Category → Skill hierarchy...")
    neo4j.ensure_taxonomy(TAXONOMY)

    print("3. Backfilling snippet_lines on DEMONSTRATES edges...")
    with neo4j.driver.session() as session:
        session.run(
            "MATCH (cs:CodeSnippet)-[d:DEMONSTRATES]->(s:Skill) "
            "WHERE d.snippet_lines IS NULL AND cs.start_line IS NOT NULL "
            "SET d.snippet_lines = cs.end_line - cs.start_line + 1"
        )

    print("4. Computing repo rollups...")
    with neo4j.driver.session() as session:
        repos = [r["name"] for r in session.run("MATCH (r:Repository) RETURN r.name AS name")]
    for repo in repos:
        neo4j.compute_repo_rollups(repo)
        print(f"   - {repo}")

    print("5. Computing proficiency levels...")
    neo4j.compute_proficiency()

    print("6. Removing orphaned Technology nodes...")
    with neo4j.driver.session() as session:
        result = session.run(
            "MATCH (t:Technology) DETACH DELETE t RETURN count(t) AS removed"
        ).single()
        print(f"   Removed {result['removed']} Technology nodes")

    neo4j.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
