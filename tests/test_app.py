from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_services():
    with (
        patch("src.app.Settings") as mock_settings,
        patch("src.app.Neo4jClient") as mock_neo4j_cls,
        patch("src.app.NimClient") as mock_nim_cls,
        patch("src.app.build_competency_graph", return_value="<html>graph</html>"),
    ):
        mock_settings.load.return_value = MagicMock()
        mock_neo4j_cls.return_value = MagicMock()
        mock_nim_cls.return_value = MagicMock()
        yield {
            "neo4j": mock_neo4j_cls.return_value,
            "nim": mock_nim_cls.return_value,
        }


def test_app_creates(mock_services):
    from src.app import create_app

    app = create_app()
    assert app.title == "ShowMeOff"
    component_types = {type(b).__name__ for b in app.blocks.values()}
    assert "Tab" in component_types


def test_chat_interface(mock_services):
    from src.app import create_app

    app = create_app()
    component_types = {type(b).__name__ for b in app.blocks.values()}
    assert "Chatbot" in component_types
    assert "Textbox" in component_types
    chatbots = [b for b in app.blocks.values() if type(b).__name__ == "Chatbot"]
    assert len(chatbots) >= 1


def test_jd_match_tab(mock_services):
    from src.app import create_app

    app = create_app()
    component_types = {type(b).__name__ for b in app.blocks.values()}
    assert "Dataframe" in component_types
    assert "Button" in component_types
    assert "Number" in component_types
    dataframes = [b for b in app.blocks.values() if type(b).__name__ == "Dataframe"]
    assert dataframes[0].headers == ["Requirement", "Confidence", "Evidence Summary"]


def test_competency_map():
    from src.ui.competency_map import build_competency_graph

    mock_client = MagicMock()
    mock_client.get_competency_map.return_value = [
        {"props": {"name": "Python"}, "rel_count": 5},
        {"props": {"name": "FastAPI"}, "rel_count": 3},
    ]
    mock_session = MagicMock()
    mock_session.run.return_value = []
    mock_client.driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_client.driver.session.return_value.__exit__ = MagicMock(return_value=False)

    html = build_competency_graph(mock_client)
    assert "Python" in html
    assert "FastAPI" in html
