import os
import tempfile

from pyvis.network import Network

NODE_COLORS = {"Skill": "#4285f4", "Repository": "#34a853", "Technology": "#ff9800"}


def build_competency_graph(neo4j_client):
    net = Network(height="600px", width="100%", notebook=False)
    net.toggle_physics(True)

    skills = neo4j_client.get_competency_map()
    skill_names = set()
    for s in skills:
        name = s["props"].get("name")
        if name:
            net.add_node(
                f"skill:{name}", label=name, color=NODE_COLORS["Skill"],
                size=max(10, s["rel_count"] * 5), title=f"Skill: {name}",
            )
            skill_names.add(name)

    tech_added = set()
    with neo4j_client.driver.session() as session:
        for r in session.run("MATCH (r:Repository) RETURN r.name AS name"):
            net.add_node(
                f"repo:{r['name']}", label=r["name"], color=NODE_COLORS["Repository"],
                size=20, title=f"Repository: {r['name']}",
            )

        for row in session.run(
            "MATCH (r:Repository)-[:USES]->(t:Technology) "
            "RETURN DISTINCT r.name AS repo, t.name AS tech"
        ):
            if row["tech"] not in tech_added:
                net.add_node(
                    f"tech:{row['tech']}", label=row["tech"], color=NODE_COLORS["Technology"],
                    size=15, title=f"Technology: {row['tech']}",
                )
                tech_added.add(row["tech"])
            net.add_edge(f"repo:{row['repo']}", f"tech:{row['tech']}", title="USES")

        for row in session.run(
            "MATCH (r:Repository)-[:CONTAINS]->(:File)-[:CONTAINS]->"
            "(:CodeSnippet)-[:DEMONSTRATES]->(s:Skill) "
            "RETURN DISTINCT r.name AS repo, s.name AS skill"
        ):
            if row["skill"] in skill_names:
                net.add_edge(f"repo:{row['repo']}", f"skill:{row['skill']}", title="DEMONSTRATES")

    tmp = tempfile.mktemp(suffix=".html")
    net.save_graph(tmp)
    with open(tmp) as f:
        html = f.read()
    os.unlink(tmp)
    return html
