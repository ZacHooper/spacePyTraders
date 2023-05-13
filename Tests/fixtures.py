import pytest
from SpacePyTraders.client import Api
import responses
import json
from typing import Generator

BASE_URL = "https://api.spacetraders.io/v2/"


@pytest.fixture
def api() -> Api:
    return Api(token="ABC123")


@pytest.fixture
def mock_endpoints() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as mock_endpoints:
        yield mock_endpoints


@pytest.fixture
def mock_responses() -> Generator[dict, None, None]:
    with open("Tests/model_mocks.json", "r") as infile:
        yield json.load(infile)
