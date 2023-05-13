from SpacePyTraders.client import Agent, Api
import pytest
from Tests.fixtures import api, mock_endpoints, mock_responses
import responses
from SpacePyTraders.exceptions import RegisterAgentExistsError


@pytest.mark.v2
def test_agent_init(api: Api):
    """Test initialisation of the Agent class"""
    assert isinstance(Agent(token="12345"), Agent)
    assert isinstance(api.agent, Agent)
    assert (
        Agent(token="12345").token == "12345"
    ), "Did not set the token attribute correctly"


@pytest.mark.v2
def test_agent_get_agent_details(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Test the get_my_agent method"""
    mock_endpoints.add(
        responses.GET,
        "https://api.spacetraders.io/v2/my/agent",
        json=mock_responses["agent_details"],
        status=200,
    )
    r = api.agent.get_my_agent()
    assert isinstance(r, dict)


@pytest.mark.v2
def test_agent_register_new_agent(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Test the register_new_agent method"""
    mock_endpoints.add(
        responses.POST,
        "https://api.spacetraders.io/v2/register",
        json=mock_responses["register_new_agent"],
        status=200,
    )
    r = api.agent.register_new_agent(symbol="string", faction="string")
    assert isinstance(r, dict)


@pytest.mark.v2
def test_agent_register_new_agent_already_exists(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """If the API returns the error code 4109, raise a RegisterAgentExistsError"""
    mock_endpoints.add(
        responses.POST,
        "https://api.spacetraders.io/v2/register",
        json={
            "error": {
                "message": "Agent already exists",
                "code": 4109,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(RegisterAgentExistsError):
        r = api.agent.register_new_agent(symbol="string", faction="string")
