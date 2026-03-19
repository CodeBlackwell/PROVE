import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    nvidia_api_key: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        return cls(
            nvidia_api_key=os.getenv("NVIDIA_API_KEY", ""),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "showmeoff"),
        )
