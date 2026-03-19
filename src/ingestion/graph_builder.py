from pathlib import Path

from src.ingestion.code_parser import parse_file

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".env"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".cpp", ".c", ".h"}


def build_graph(repo_path, neo4j_client, nim_client):
    repo_path = Path(repo_path)
    repo_name = repo_path.name

    with neo4j_client.driver.session() as session:
        session.run(
            "MERGE (r:Repository {name: $name}) SET r.path = $path",
            name=repo_name, path=str(repo_path),
        )

        for file_path in _walk_code_files(repo_path):
            rel_path = str(file_path.relative_to(repo_path))
            session.run(
                "MATCH (r:Repository {name: $repo}) "
                "MERGE (f:File {path: $path}) "
                "MERGE (r)-[:CONTAINS]->(f)",
                repo=repo_name, path=rel_path,
            )

            chunks = parse_file(file_path)
            for chunk in chunks:
                embeddings = nim_client.embed([chunk.content])
                embedding = embeddings[0]

                session.run(
                    "MATCH (f:File {path: $file_path}) "
                    "MERGE (cs:CodeSnippet {name: $name, file_path: $file_path}) "
                    "SET cs.content = $content, cs.start_line = $start, "
                    "    cs.end_line = $end, cs.language = $lang, "
                    "    cs.embedding = $embedding "
                    "MERGE (f)-[:CONTAINS]->(cs)",
                    file_path=rel_path, name=chunk.name,
                    content=chunk.content, start=chunk.start_line,
                    end=chunk.end_line, lang=chunk.language,
                    embedding=embedding,
                )


def _walk_code_files(repo_path: Path):
    for item in sorted(repo_path.rglob("*")):
        if any(skip in item.parts for skip in SKIP_DIRS):
            continue
        if item.is_file() and item.suffix.lower() in CODE_EXTENSIONS:
            yield item
