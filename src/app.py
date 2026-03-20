import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config.settings import Settings
from src.core import Neo4jClient, NimClient
from src.core.haiku_client import HaikuClient
from src.qa.agent import QAAgent

settings = Settings.load()
neo4j_client = Neo4jClient(uri=settings.neo4j_uri, user=settings.neo4j_user, password=settings.neo4j_password)
nim_client = NimClient(api_key=settings.nvidia_api_key)
haiku_client = HaikuClient(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
qa_agent = QAAgent(neo4j_client, nim_client, haiku_client)

app = FastAPI()
base = Path(__file__).parent
app.mount("/static", StaticFiles(directory=base / "static"), name="static")
templates = Jinja2Templates(directory=base / "templates")


@app.get("/")
def index(request: Request):
    with neo4j_client.driver.session() as s:
        r = s.run("MATCH (e:Engineer) RETURN e.name AS name LIMIT 1").single()
    name = r["name"] if r else "Engineer"
    return templates.TemplateResponse("index.html", {"request": request, "name": name})


@app.get("/api/chat")
def chat(q: str):
    def generate():
        for chunk in qa_agent.answer_stream(q):
            if isinstance(chunk, dict):
                yield f"event: graph\ndata: {json.dumps(chunk)}\n\n"
            else:
                sse = "".join(f"data: {line}\n" for line in chunk.split("\n"))
                yield sse + "\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
