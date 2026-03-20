import json

NODE_COLORS = {
    "Engineer": "#c4956a", "Repository": "#6b8f9e",
    "Domain": "#8b7355", "Category": "#b8805a", "Skill": "#7a8b6f",
}
EDGE_COLORS = {
    "owns": "#a8a099", "domain": "#8b7355", "category": "#b8805a", "skill": "#7a8b6f",
}
PROFICIENCY_SIZE = {"extensive": 18, "moderate": 14, "minimal": 10}


def get_graph_data(neo4j_client):
    nodes, edges = [], []
    node_ids, edge_ids = set(), set()

    def add_node(nid, **kwargs):
        if nid not in node_ids:
            nodes.append({"id": nid, **kwargs})
            node_ids.add(nid)

    def add_edge(from_id, to_id, **kwargs):
        key = (from_id, to_id)
        if key not in edge_ids:
            edges.append({"from": from_id, "to": to_id, **kwargs})
            edge_ids.add(key)

    with neo4j_client.driver.session() as session:
        r = session.run("MATCH (e:Engineer) RETURN e.name AS name").single()
        if r:
            add_node(f"eng:{r['name']}", label=r["name"], color=NODE_COLORS["Engineer"], size=35)

        for r in session.run("MATCH (r:Repository) RETURN r.name AS name"):
            add_node(f"repo:{r['name']}", label=r["name"], color=NODE_COLORS["Repository"], size=22)

        for r in session.run("MATCH (e:Engineer)-[:OWNS]->(r:Repository) RETURN e.name AS eng, r.name AS repo"):
            add_edge(f"eng:{r['eng']}", f"repo:{r['repo']}", color=EDGE_COLORS["owns"])

        for r in session.run(
            "MATCH (d:Domain)-[:CONTAINS]->(c:Category)-[:CONTAINS]->(s:Skill) "
            "WHERE s.proficiency IS NOT NULL AND s.proficiency <> 'none' "
            "RETURN d.name AS domain, c.name AS category, s.name AS skill, s.proficiency AS proficiency"
        ):
            did, cid, sid = f"dom:{r['domain']}", f"cat:{r['category']}", f"skill:{r['skill']}"
            size = PROFICIENCY_SIZE.get(r["proficiency"], 10)
            add_node(did, label=r["domain"], color=NODE_COLORS["Domain"], size=26)
            add_node(cid, label=r["category"], color=NODE_COLORS["Category"], size=18)
            add_node(sid, label=r["skill"], color=NODE_COLORS["Skill"], size=size)
            add_edge(did, cid, color=EDGE_COLORS["domain"])
            add_edge(cid, sid, color=EDGE_COLORS["category"])

        for r in session.run(
            "MATCH (r:Repository)-[:DEMONSTRATES]->(s:Skill) "
            "WHERE s.proficiency IS NOT NULL AND s.proficiency <> 'none' "
            "RETURN r.name AS repo, s.name AS skill"
        ):
            add_edge(f"repo:{r['repo']}", f"skill:{r['skill']}", color=EDGE_COLORS["skill"], dashes=True)

        for r in session.run(
            "MATCH (e:Engineer)-[:CLAIMS]->(s:Skill) "
            "WHERE s.proficiency IS NULL OR s.proficiency = 'none' "
            "RETURN s.name AS skill"
        ):
            add_node(f"skill:{r['skill']}", label=r["skill"], color="#a8a099", size=8)

    for n in nodes:
        prefix = n["id"].split(":")[0]
        n["level"] = {"eng": 0, "repo": 1, "dom": 2, "cat": 3}.get(prefix, 4)

    return {"nodes": nodes, "edges": edges}


def get_subgraph(neo4j_client, skill_names: list[str]) -> dict:
    if not skill_names:
        return {"nodes": [], "edges": []}
    with neo4j_client.driver.session() as session:
        rows = session.run(
            "MATCH (d:Domain)-[:CONTAINS]->(c:Category)-[:CONTAINS]->(s:Skill) "
            "WHERE s.name IN $names AND s.proficiency IS NOT NULL AND s.proficiency <> 'none' "
            "OPTIONAL MATCH (r:Repository)-[:DEMONSTRATES]->(s) "
            "RETURN d.name AS domain, c.name AS category, s.name AS skill, "
            "s.proficiency AS proficiency, collect(DISTINCT r.name) AS repos",
            names=skill_names,
        )
        nodes, edges = [], []
        node_ids, edge_ids = set(), set()
        for r in rows:
            did, cid, sid = f"dom:{r['domain']}", f"cat:{r['category']}", f"skill:{r['skill']}"
            size = PROFICIENCY_SIZE.get(r["proficiency"], 10)
            for nid, label, color, sz in [
                (did, r["domain"], NODE_COLORS["Domain"], 26),
                (cid, r["category"], NODE_COLORS["Category"], 18),
                (sid, r["skill"], NODE_COLORS["Skill"], size),
            ]:
                if nid not in node_ids:
                    nodes.append({"id": nid, "label": label, "color": color, "size": sz})
                    node_ids.add(nid)
            for frm, to, opts in [(did, cid, {}), (cid, sid, {})]:
                if (frm, to) not in edge_ids:
                    edges.append({"from": frm, "to": to, **opts})
                    edge_ids.add((frm, to))
            for repo in r["repos"]:
                rid = f"repo:{repo}"
                if rid not in node_ids:
                    nodes.append({"id": rid, "label": repo, "color": NODE_COLORS["Repository"], "size": 22})
                    node_ids.add(rid)
                if (rid, sid) not in edge_ids:
                    edges.append({"from": rid, "to": sid, "dashes": True})
                    edge_ids.add((rid, sid))
    return {"nodes": nodes, "edges": edges}


def build_competency_graph(neo4j_client):
    import html as html_mod
    data = get_graph_data(neo4j_client)
    nodes, edges = data["nodes"], data["edges"]

    inner = f"""<!DOCTYPE html>
<html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
<style>body{{margin:0;background:#f5f0eb;}} #g{{width:100%;height:580px;}}</style>
</head><body>
<div id="g"></div>
<script>
new vis.Network(document.getElementById("g"),
  {{nodes:new vis.DataSet({json.dumps(nodes)}),edges:new vis.DataSet({json.dumps(edges)}) }},
  {{layout:{{hierarchical:{{enabled:true,direction:"UD",sortMethod:"directed",levelSeparation:140,nodeSpacing:180}}}},
    physics:{{hierarchicalRepulsion:{{springLength:180,nodeDistance:220}},stabilization:{{iterations:150}}}},
    nodes:{{font:{{size:13,color:"#2c2c2c",face:"sans-serif"}},borderWidth:2,shape:"dot"}},
    edges:{{smooth:{{type:"cubicBezier",forceDirection:"vertical",roundness:0.4}},width:1.5}},
    interaction:{{hover:true,zoomView:true,dragView:true,dragNodes:true}}
  }});
</script></body></html>"""
    escaped = html_mod.escape(inner, quote=True)
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:640px;border:none;"></iframe>'
