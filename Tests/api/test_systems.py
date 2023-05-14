from Tests.fixtures import api, mock_endpoints, mock_responses, BASE_URL
from SpacePyTraders.client import Api, Systems
from SpacePyTraders.exceptions import ResourceNotFoundError, MarketNotFoundError
import pytest
import responses
import json


@pytest.mark.v2
def test_systems_init(api: Api):
    assert (
        Systems(token="12345").token == "12345"
    ), "Did not set the token attribute correctly"
    assert isinstance(Systems(token="12345"), Systems)
    assert isinstance(api.systems, Systems)


### Test List Systems ###
@pytest.mark.v2
def test_systems_list_systems(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems",
        json=mock_responses["list_systems"],
        status=200,
    )
    r = api.systems.list_systems()
    assert isinstance(r, dict)


### Get System ###
@pytest.mark.v2
def test_systems_view_system(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE",
        json=mock_responses["view_system"],
        status=200,
    )
    r = api.systems.get_system("X1-OE")
    assert isinstance(r, dict)


@pytest.mark.v2
def test_systems_view_system_not_found(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE",
        json={
            "error": {
                "message": "Resource with the given identifier does not exist.",
                "code": 404,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(ResourceNotFoundError):
        r = api.systems.get_system("X1-OE")


### List Waypoints ###
@pytest.mark.v2
def test_systems_list_waypoints(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints",
        json=mock_responses["list_waypoints"],
        status=200,
    )
    r = api.systems.list_waypoints("X1-OE")
    assert isinstance(r, dict)


### Get Waypoint ###
@pytest.mark.v2
def test_systems_view_waypoint(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints/X1-OE-PM",
        json=mock_responses["view_waypoints"],
        status=200,
    )
    r = api.systems.get_waypoint("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)


### Get market ###
@pytest.mark.v2
def test_systems_view_market(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints/X1-OE-PM/market",
        json=mock_responses["view_market"],
        status=200,
    )
    r = api.systems.get_market("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)


@pytest.mark.v2
def test_systems_view_market_not_found(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints/X1-OE-PM/market",
        json={
            "error": {
                "message": "No market found at location.",
                "code": 4603,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(MarketNotFoundError):
        r = api.systems.get_market("X1-OE", "X1-OE-PM")


### Get Shipyards ###
@pytest.mark.v2
def test_systems_view_shipyard(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints/X1-OE-PM/shipyard",
        json=mock_responses["view_market"],
        status=200,
    )
    r = api.systems.get_shipyard("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)


### Get Jump Gate ###
@pytest.mark.v2
def test_systems_view_jump_gate(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}systems/X1-OE/waypoints/X1-OE-PM/jump-gate",
        json=mock_responses["view_market"],
        status=200,
    )
    r = api.systems.get_jump_gate("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)


@pytest.mark.v2
def test_systems_chart_waypoint(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/ships/HMAS-1/chart",
        json=mock_responses["chart_waypoint"],
        status=200,
    )
    r = api.systems.chart_waypoint("HMAS-1")
    assert isinstance(r, dict)
