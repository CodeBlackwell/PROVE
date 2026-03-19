from src.core.neo4j_client import Neo4jClient
from src.core.nim_client import NimClient


def search_code(query: str, neo4j_client: Neo4jClient, nim_client: NimClient) -> list[dict]:
    embedding = nim_client.embed([query])[0]
    results = neo4j_client.vector_search(embedding, top_k=5)
    return [
        {
            "file_path": r["props"].get("file_path", ""),
            "start_line": r["props"].get("start_line", 0),
            "end_line": r["props"].get("end_line", 0),
            "content": r["props"].get("content", ""),
            "score": r["score"],
        }
        for r in results
    ]


def get_evidence(skill_name: str, neo4j_client: Neo4jClient) -> list[dict]:
    results = neo4j_client.get_skill_evidence(skill_name)
    return [
        {
            "file_path": r.get("file_path", ""),
            "start_line": r.get("start_line", 0),
            "end_line": r.get("end_line", 0),
            "content": r.get("content", ""),
        }
        for r in results
    ]


def search_resume(query: str, neo4j_client: Neo4jClient, nim_client: NimClient) -> list[dict]:
    cypher = (
        "MATCH (n) WHERE n:Engineer OR n:Role OR n:Company "
        "WITH n, [key IN keys(n) WHERE key <> 'embedding' | toString(n[key])] AS vals "
        "WHERE ANY(v IN vals WHERE toLower(v) CONTAINS toLower($query)) "
        "RETURN labels(n) AS labels, properties(n) AS props"
    )
    with neo4j_client.driver.session() as session:
        result = session.run(cypher, query=query)
        return [
            {"labels": r["labels"], **{k: v for k, v in r["props"].items() if k != "embedding"}}
            for r in result
        ]
