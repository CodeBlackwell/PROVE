from src.core.neo4j_client import Neo4jClient
from src.ingestion.skill_taxonomy import CATEGORY_TO_DOMAIN, RESUME_SKILL_ALIASES, SKILL_HIERARCHY

MIN_SCORE = 0.3


def search_code(query: str, neo4j_client: Neo4jClient, embed_client) -> list[dict]:
    embedding = embed_client.embed([query], input_type="query")[0]
    results = neo4j_client.vector_search(embedding, top_k=25)
    return [
        {
            "file_path": r["props"].get("file_path", ""),
            "start_line": r["props"].get("start_line", 0),
            "end_line": r["props"].get("end_line", 0),
            "content": r["props"].get("content", ""),
            "context": r["props"].get("context", ""),
            "score": r["score"],
            "repo": r.get("repo"),
            "private": r.get("private", False),
            "skills": r.get("skills", []),
        }
        for r in results
        if r["score"] >= MIN_SCORE
    ]


def get_evidence(skill_name: str, neo4j_client: Neo4jClient) -> list[dict]:
    results = neo4j_client.get_skill_evidence(skill_name)
    return [
        {
            "file_path": r.get("file_path", ""),
            "start_line": r.get("start_line", 0),
            "end_line": r.get("end_line", 0),
            "content": r.get("content", ""),
            "context": r.get("context", ""),
            "first_seen": r.get("first_seen"),
            "last_seen": r.get("last_seen"),
            "proficiency": r.get("proficiency"),
            "repo": r.get("repo"),
            "private": r.get("private", False),
            "skill_name": skill_name,
        }
        for r in results
    ]


def find_gaps(skills_csv: str, neo4j_client: Neo4jClient) -> list[dict]:
    skills = [s.strip() for s in skills_csv.split(",") if s.strip()]
    if not skills:
        return []

    # Query 1: batch skill hierarchy lookup
    skill_info = _batch_skill_lookup(skills, neo4j_client)

    needs_category: list[tuple[str, str, str]] = []  # (skill, domain, category)
    needs_claims: list[str] = []
    results = []

    for skill in skills:
        info = skill_info.get(skill)
        if info and info.get("snippet_count", 0) > 0:
            results.append(
                {
                    "skill": skill,
                    "status": "demonstrated",
                    "code_examples": info["snippet_count"],
                    "proficiency": info.get("proficiency", "none"),
                    "domain": info.get("domain"),
                    "category": info.get("category"),
                }
            )
            continue
        hierarchy = SKILL_HIERARCHY.get(skill)
        if hierarchy:
            needs_category.append((skill, hierarchy[0], hierarchy[1]))
        else:
            needs_claims.append(skill)

    # Query 2: batch related-in-category lookup
    if needs_category:
        categories = list({cat for _, _, cat in needs_category})
        related_by_cat = _batch_related_in_categories(categories, neo4j_client)
        for skill, domain, category in needs_category:
            related = related_by_cat.get(category, [])
            if related:
                results.append(
                    {
                        "skill": skill,
                        "status": "not_found_but_related",
                        "code_examples": 0,
                        "domain": domain,
                        "category": category,
                        "related_demonstrated": related,
                    }
                )
            else:
                needs_claims.append(skill)

    # Query 3: batch claims check
    if needs_claims:
        claimed = _batch_claims_check(needs_claims, neo4j_client)
        for skill in needs_claims:
            if skill in claimed:
                alias = RESUME_SKILL_ALIASES.get(skill)
                alias_cat, alias_dom = None, None
                if alias and alias.startswith("cat:"):
                    alias_cat = alias[4:]
                    alias_dom = CATEGORY_TO_DOMAIN.get(alias_cat)
                elif alias:
                    hier = SKILL_HIERARCHY.get(alias)
                    if hier:
                        alias_dom, alias_cat = hier
                results.append(
                    {
                        "skill": skill,
                        "status": "claimed_only",
                        "code_examples": 0,
                        "domain": alias_dom,
                        "category": alias_cat,
                    }
                )
            else:
                results.append({"skill": skill, "status": "not_found", "code_examples": 0})
    return results


def _batch_skill_lookup(skill_names: list[str], neo4j_client: Neo4jClient) -> dict[str, dict]:
    with neo4j_client.driver.session() as session:
        result = session.run(
            "MATCH (d:Domain)-[:CONTAINS]->(c:Category)-[:CONTAINS]->(s:Skill) "
            "WHERE s.name IN $names "
            "RETURN s.name AS skill, d.name AS domain, c.name AS category, "
            "s.proficiency AS proficiency, s.snippet_count AS snippet_count",
            names=skill_names,
        )
        return {r["skill"]: dict(r) for r in result}


def _batch_related_in_categories(
    categories: list[str], neo4j_client: Neo4jClient
) -> dict[str, list[str]]:
    with neo4j_client.driver.session() as session:
        result = session.run(
            "MATCH (c:Category)-[:CONTAINS]->(s:Skill) "
            "WHERE c.name IN $cats AND s.proficiency IS NOT NULL AND s.proficiency <> 'none' "
            "RETURN c.name AS category, s.name AS skill",
            cats=categories,
        )
        out: dict[str, list[str]] = {}
        for r in result:
            out.setdefault(r["category"], []).append(r["skill"])
        return out


def _batch_claims_check(skill_names: list[str], neo4j_client: Neo4jClient) -> set[str]:
    with neo4j_client.driver.session() as session:
        result = session.run(
            "MATCH (:Engineer)-[:CLAIMS]->(s:Skill) WHERE s.name IN $names RETURN s.name AS skill",
            names=skill_names,
        )
        return {r["skill"] for r in result}


def get_repo_overview(repo_name: str, neo4j_client: Neo4jClient) -> dict:
    result = neo4j_client.get_repo_overview(repo_name)
    if not result:
        return {"error": f"Repository '{repo_name}' not found"}
    overview = {
        "name": result["name"],
        "file_count": result["file_count"],
        "sample_files": result["sample_files"],
        "top_skills": result["top_skills"],
    }
    if result.get("architecture"):
        overview["architecture"] = result["architecture"]
    return overview


def get_connected_evidence(
    skill_name: str, repo_name: str, neo4j_client: Neo4jClient
) -> list[dict]:
    snippets = neo4j_client.get_connected_snippets(skill_name, repo_name)
    return [
        {
            "file_path": s["file_path"],
            "snippet_name": s.get("snippet_name", ""),
            "start_line": s["start_line"],
            "end_line": s["end_line"],
            "content": s["content"],
            "context": s.get("context", ""),
            "proficiency": s["proficiency"],
            "repo": repo_name,
            "private": bool(s.get("private")),
            "related_skills": s.get("related_skills", []),
            "skill_name": skill_name,
        }
        for s in snippets
    ]


def search_resume(query: str, neo4j_client: Neo4jClient) -> list[dict]:
    cypher = (
        "MATCH (n) WHERE n:Engineer "
        "WITH n, [key IN keys(n) WHERE key <> 'embedding' | toString(n[key])] AS vals "
        "WHERE ANY(v IN vals WHERE toLower(v) CONTAINS toLower($term)) "
        "RETURN labels(n) AS labels, properties(n) AS props"
    )
    with neo4j_client.driver.session() as session:
        result = session.run(cypher, term=query)
        return [
            {"labels": r["labels"], **{k: v for k, v in r["props"].items() if k != "embedding"}}
            for r in result
        ]
