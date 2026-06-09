from unittest.mock import MagicMock, patch


def test_healthz_ok_when_neo4j_reachable():
    import src.app as appmod

    with patch.dict(appmod.clients, {"neo4j_client": MagicMock()}):
        result = appmod.healthz()
    assert result == {"status": "ok", "neo4j": "up"}


def test_healthz_degraded_when_neo4j_down():
    import src.app as appmod

    bad = MagicMock()
    bad.driver.session.side_effect = Exception("connection refused")
    with patch.dict(appmod.clients, {"neo4j_client": bad}):
        result = appmod.healthz()
    assert result.status_code == 503


def test_competency_map():
    from src.ui.competency_map import build_competency_graph

    with patch("src.ui.competency_map.get_graph_data") as mock_get:
        mock_get.return_value = {
            "nodes": [
                {
                    "id": "skill:Python",
                    "label": "Python",
                    "color": "#7a8b6f",
                    "size": 18,
                    "level": 4,
                },
                {
                    "id": "skill:FastAPI",
                    "label": "FastAPI",
                    "color": "#7a8b6f",
                    "size": 14,
                    "level": 4,
                },
            ],
            "edges": [],
        }
        html = build_competency_graph(MagicMock())
    assert "Python" in html
    assert "FastAPI" in html
