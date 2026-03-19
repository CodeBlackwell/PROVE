from unittest.mock import MagicMock, patch
import json

from src.qa.tools import search_code, get_evidence, search_resume
from src.qa.agent import QAAgent, format_response


def _mock_neo4j():
    client = MagicMock()
    client.vector_search.return_value = [
        {"props": {"file_path": "src/main.py", "start_line": 10, "end_line": 20, "content": "def hello():"}, "score": 0.95},
        {"props": {"file_path": "src/utils.py", "start_line": 1, "end_line": 5, "content": "import os"}, "score": 0.80},
    ]
    client.get_skill_evidence.return_value = [
        {"file_path": "src/app.py", "start_line": 5, "end_line": 15, "content": "class App:"},
    ]
    session = MagicMock()
    session.run.return_value = [
        {"labels": ["Engineer"], "props": {"name": "Chris", "email": "chris@test.com"}},
    ]
    client.driver.session.return_value.__enter__ = MagicMock(return_value=session)
    client.driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return client


def _mock_nim():
    client = MagicMock()
    client.embed.return_value = [[0.1] * 1024]
    return client


def _make_chat_response(content=None, tool_calls=None):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = tool_calls
    return response


def _make_tool_call(name, arguments, call_id="call_1"):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


def test_search_tools():
    neo4j = _mock_neo4j()
    nim = _mock_nim()

    results = search_code("python async", neo4j, nim)
    assert len(results) == 2
    assert results[0]["file_path"] == "src/main.py"
    assert results[0]["score"] == 0.95
    nim.embed.assert_called_once_with(["python async"])
    neo4j.vector_search.assert_called_once()

    results = get_evidence("Python", neo4j)
    assert len(results) == 1
    assert results[0]["file_path"] == "src/app.py"
    neo4j.get_skill_evidence.assert_called_once_with("Python")

    results = search_resume("Chris", neo4j, nim)
    assert len(results) == 1
    assert results[0]["labels"] == ["Engineer"]
    assert results[0]["name"] == "Chris"


def test_react_loop():
    neo4j = _mock_neo4j()
    nim = _mock_nim()

    tool_response = _make_chat_response(
        tool_calls=[_make_tool_call("search_code", {"query": "python"})]
    )
    final_response = _make_chat_response(content="The engineer demonstrates Python skills.")

    nim.chat = MagicMock(side_effect=[tool_response, final_response])

    agent = QAAgent(neo4j, nim)
    result = agent.answer("Does this engineer know Python?")

    assert "The engineer demonstrates Python skills." in result
    assert nim.chat.call_count == 2
    first_call_kwargs = nim.chat.call_args_list[0]
    tools_arg = first_call_kwargs[0][1] if len(first_call_kwargs[0]) > 1 else first_call_kwargs[1].get("tools")
    assert tools_arg is not None


def test_react_loop_max_calls():
    neo4j = _mock_neo4j()
    nim = _mock_nim()

    tool_resp = _make_chat_response(
        tool_calls=[_make_tool_call("search_code", {"query": "test"}, f"call_1")]
    )
    final_resp = _make_chat_response(content="Final answer after max calls.")

    nim.chat = MagicMock(side_effect=[tool_resp, tool_resp, tool_resp, final_resp])

    agent = QAAgent(neo4j, nim)
    result = agent.answer("complex question")

    assert "Final answer after max calls." in result
    assert nim.chat.call_count == 4


def test_response_formatting():
    evidence = [
        {"file_path": "src/a.py", "start_line": 1, "end_line": 10, "content": "class Foo:"},
        {"file_path": "src/b.py", "start_line": 5, "end_line": 15, "content": "def bar():"},
        {"file_path": "src/c.py", "start_line": 20, "end_line": 30, "content": "async def baz():"},
    ]
    result = format_response("Engineer knows Python.", evidence)
    assert "[src/a.py:L1-L10]" in result
    assert "[src/b.py:L5-L15]" in result
    assert "Confidence: Strong (3 code examples)" in result

    result = format_response("Some skill.", evidence[:1])
    assert "Confidence: Partial (1 code example)" in result

    result = format_response("No evidence found for this claim.", [])
    assert "Confidence: None (0 code examples)" in result
    assert "No evidence found" in result


def test_streaming():
    neo4j = _mock_neo4j()
    nim = _mock_nim()

    tool_response = _make_chat_response(
        tool_calls=[_make_tool_call("search_code", {"query": "python"})]
    )
    final_response = _make_chat_response(content="Streaming answer.")

    nim.chat = MagicMock(side_effect=[tool_response, final_response])

    agent = QAAgent(neo4j, nim)
    chunks = list(agent.answer_stream("Does this engineer know Python?"))

    assert any("Searching for:" in c for c in chunks)
    assert any("Streaming answer." in c for c in chunks)
    assert any("Confidence:" in c for c in chunks)
