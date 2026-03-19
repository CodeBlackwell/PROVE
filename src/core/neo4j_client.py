from neo4j import GraphDatabase


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def init_schema(self):
        with self.driver.session() as session:
            for label in ("Skill", "Repository", "Engineer"):
                session.run(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE"
                )
            session.run(
                "CREATE VECTOR INDEX code_embedding IF NOT EXISTS "
                "FOR (n:CodeSnippet) ON (n.embedding) "
                "OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}"
            )

    def vector_search(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        query = (
            "CALL db.index.vector.queryNodes('code_embedding', $top_k, $embedding) "
            "YIELD node, score "
            "RETURN properties(node) AS props, score"
        )
        with self.driver.session() as session:
            result = session.run(query, embedding=embedding, top_k=top_k)
            return [{"props": r["props"], "score": r["score"]} for r in result]

    def get_skill_evidence(self, skill_name: str) -> list[dict]:
        query = (
            "MATCH (s:Skill {name: $name})-[:EVIDENCED_BY]->(c:CodeSnippet) "
            "RETURN properties(c) AS props"
        )
        with self.driver.session() as session:
            result = session.run(query, name=skill_name)
            return [r["props"] for r in result]

    def get_competency_map(self) -> list[dict]:
        query = (
            "MATCH (s:Skill) "
            "OPTIONAL MATCH (s)-[r]-() "
            "RETURN properties(s) AS props, count(r) AS rel_count"
        )
        with self.driver.session() as session:
            result = session.run(query)
            return [{"props": r["props"], "rel_count": r["rel_count"]} for r in result]

    def close(self):
        self.driver.close()
