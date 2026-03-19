import pytest
from src.config.settings import Settings
from src.core import Neo4jClient, NimClient


@pytest.fixture
def settings():
    return Settings.load()


@pytest.fixture
def nim_client(settings):
    return NimClient(api_key=settings.nvidia_api_key)


@pytest.fixture
def neo4j_client(settings):
    client = Neo4jClient(uri=settings.neo4j_uri, user=settings.neo4j_user, password=settings.neo4j_password)
    yield client
    client.close()
