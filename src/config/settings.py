import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_SUBJECT_PATH = Path(__file__).resolve().parents[2] / "subject.toml"

_SUBJECT_DEFAULTS = {
    "name": "LeChristopher Blackwell",
    "preferred_names": ["Le", "LeChristopher"],
    "forbidden_names": ["Christopher", "Chris"],
    "github_owner": "codeblackwell",
    "domain": "prove.codeblackwell.ai",
}


@dataclass
class Subject:
    name: str
    preferred_names: list[str]
    forbidden_names: list[str]
    github_owner: str
    domain: str

    @classmethod
    def load(cls, path: Path = _SUBJECT_PATH) -> "Subject":
        data = tomllib.loads(path.read_text()) if path.exists() else {}
        merged = {**_SUBJECT_DEFAULTS, **data}
        return cls(**{k: merged[k] for k in _SUBJECT_DEFAULTS})


@dataclass
class Settings:
    nvidia_api_key: str
    anthropic_api_key: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    github_token: str
    embed_provider: str
    voyage_api_key: str
    chat_provider: str
    claude_model: str
    db_path: str
    show_private_code: bool
    github_owner: str
    domain: str
    cdn_base: str
    subject: Subject = field(default_factory=Subject.load)

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        subject = Subject.load()
        return cls(
            nvidia_api_key=os.getenv("NVIDIA_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "prove"),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            embed_provider=os.getenv("EMBED_PROVIDER", "nim"),
            voyage_api_key=os.getenv("VOYAGE_API_KEY", ""),
            chat_provider=os.getenv("CHAT_PROVIDER", "nim"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
            db_path=os.getenv("DB_PATH", "data/prove.db"),
            show_private_code=os.getenv("SHOW_PRIVATE_CODE", "false").lower()
            in ("true", "1", "yes"),
            github_owner=os.getenv("GITHUB_OWNER", subject.github_owner),
            domain=os.getenv("DOMAIN", subject.domain),
            cdn_base=os.getenv("CDN_BASE", "").rstrip("/"),
            subject=subject,
        )
