"""Re-embed all CodeSnippet nodes with contextual preambles. Idempotent."""

from tqdm import tqdm
from src.config.settings import Settings
from src.core.neo4j_client import Neo4jClient
from src.core.nim_client import NimClient
from src.ingestion.graph_builder import build_preamble

BATCH_SIZE = 50

FETCH_QUERY = """
MATCH (r:Repository)-[:CONTAINS]->(:File)-[:CONTAINS]->(cs:CodeSnippet)
OPTIONAL MATCH (cs)-[:DEMONSTRATES]->(sk:Skill)
RETURN cs.name AS name, cs.file_path AS file_path, cs.content AS content,
       cs.language AS language, r.name AS repo, collect(DISTINCT sk.name) AS skills
"""


def main():
    settings = Settings.load()
    neo = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    nim = NimClient(settings.nvidia_api_key)

    with neo.driver.session() as session:
        rows = list(session.run(FETCH_QUERY))

    print(f"Re-embedding {len(rows)} snippets in batches of {BATCH_SIZE}")

    for i in tqdm(range(0, len(rows), BATCH_SIZE)):
        batch = rows[i : i + BATCH_SIZE]
        texts = [
            build_preamble(r["name"], r["language"], r["file_path"], r["repo"], r["skills"])
            + "\nCode:\n" + r["content"]
            for r in batch
        ]
        embeddings = nim.embed(texts)

        with neo.driver.session() as session:
            for row, emb in zip(batch, embeddings):
                session.run(
                    "MATCH (cs:CodeSnippet {name: $name, file_path: $fp}) "
                    "SET cs.embedding = $embedding",
                    name=row["name"], fp=row["file_path"], embedding=emb,
                )

    neo.close()
    print("Done.")


if __name__ == "__main__":
    main()
