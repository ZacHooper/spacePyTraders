import unittest
import requests
import json
import responses
import logging
from SpacePyTraders.client import *
import pytest

TOKEN = "e8c9ac0d-e1ec-45e9-b808-d622a7717f46"
USERNAME = "JimHawkins"
BASE_URL = "https://api.spacetraders.io/"
V2_BASE_URL = "https://api.spacetraders.io/v2/"

with open('Tests/model_mocks.json','r') as infile:
    MOCKS = json.load(infile)


@pytest.fixture
def api_v2() -> Api:
    return Api(token=TOKEN)

@pytest.fixture
def mock_endpoints():
    res = responses.RequestsMock()
    res.start()
    return res

@pytest.mark.v2
def test_api_v2(api_v2):
    assert isinstance(api_v2, Api)

#
# Markets related tests
#

@pytest.mark.v2
def test_markets_init(api_v2):
    assert isinstance(Markets(token="12345"), Markets)
    assert isinstance(api_v2.markets, Markets)
    assert Markets(token="12345").token == "12345", "Did not set the token attribute correctly"

@pytest.mark.v2
def test_market_deploy_asset(api_v2: Api, mock_endpoints):
    """Needs a JSON Mock"""
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/deploy", json=MOCKS['agent_details'], status=200)
    r = api_v2.markets.deploy_asset("HMAS-1", "IRON_ORE")
    assert mock_endpoints.calls[0].request.params == {"tradeSymbol": "IRON_ORE"}
    assert isinstance(r, dict)

@pytest.mark.v2
def test_markets_trade_imports(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}trade/IRON_ORE/imports", json=MOCKS['trade_imports'], status=200)
    r = api_v2.markets.trade_imports('IRON_ORE')
    assert isinstance(r, dict)

@pytest.mark.v2
def test_markets_trade_exports(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}trade/IRON_ORE/exports", json=MOCKS['trade_exports'], status=200)
    r = api_v2.markets.trade_exports('IRON_ORE')
    assert isinstance(r, dict)

@pytest.mark.v2
def test_markets_trade_exchanges(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}trade/IRON_ORE/exchange", json=MOCKS['trade_exchanges'], status=200)
    r = api_v2.markets.trade_exchanges('IRON_ORE')
    assert isinstance(r, dict)

@pytest.mark.v2
def test_markets_list_markets(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/markets", json=MOCKS['list_markets'], status=200)
    r = api_v2.markets.list_markets('X1-OE')
    assert isinstance(r, dict)

@pytest.mark.v2
def test_markets_view_market(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/markets/X1-OE-PM", json=MOCKS['view_market'], status=200)
    r = api_v2.markets.view_market('X1-OE', 'X1-OE-PM')
    assert isinstance(r, dict)

#
# Trade related tests
#

@pytest.mark.v2
def test_trade_init(api_v2):
    assert isinstance(Trade(token="12345"), Trade)
    assert isinstance(api_v2.trade, Trade)
    assert Trade(token="12345").token == "12345", "Did not set the token attribute correctly"

@pytest.mark.v2
def test_trade_purchase_cargo(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/purchase", json=MOCKS['purchase_cargo'], status=200)
    r = api_v2.trade.purchase_cargo("HMAS-1", "IRON_ORE", 5)
    assert mock_endpoints.calls[0].request.params == {"tradeSymbol": "IRON_ORE", "units": '5'}
    assert isinstance(r, dict)

@pytest.mark.v2
def test_trade_sell_cargo(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/sell", json=MOCKS['sell_cargo'], status=200)
    r = api_v2.trade.sell_cargo("HMAS-1", "IRON_ORE", 5)
    assert mock_endpoints.calls[0].request.params == {"tradeSymbol": "IRON_ORE", "units": '5'}
    assert isinstance(r, dict)

#
# Navigation
#

@pytest.mark.v2
def test_navigation_init(api_v2):
    Navigation(token="12345").token == "12345", "Did not set the token attribute correctly"
    assert isinstance(Navigation(token="12345"), Navigation)
    assert isinstance(api_v2.navigation, Navigation)

@pytest.mark.v2
def test_navigation_dock_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/dock", json=MOCKS['dock_ship'], status=200)
    r = api_v2.navigation.dock_ship("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_orbit_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/orbit", json=MOCKS['orbit_ship'], status=200)
    r = api_v2.navigation.orbit_ship("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_jump_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/jump", json=MOCKS['jump_ship'], status=200)
    r = api_v2.navigation.jump_ship("HMAS-1", "X1-OE-PM")
    assert mock_endpoints.calls[0].request.params == {"destination": "X1-OE-PM"}
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_jump_cooldown(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}my/ships/HMAS-1/jump", json=MOCKS['jump_cooldown'], status=200)
    r = api_v2.navigation.jump_cooldown("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_refuel_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/refuel", json=MOCKS['refuel_ship'], status=200)
    r = api_v2.navigation.refuel_ship("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_navigate_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/navigate", json=MOCKS['navigate_ship'], status=200)
    r = api_v2.navigation.navigate_ship("HMAS-1", "X1-OE-PM")
    assert mock_endpoints.calls[0].request.params == {"destination": "X1-OE-PM"}
    assert isinstance(r, dict)

@pytest.mark.v2
def test_navigation_navigate_status(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}my/ships/HMAS-1/navigate", json=MOCKS['navigate_status'], status=200)
    r = api_v2.navigation.navigation_status("HMAS-1")
    assert isinstance(r, dict)

#
# Contract
#



#
# Extract
#

@pytest.mark.v2
def test_extract_init(api_v2):
    Extract(token="12345").token == "12345", "Did not set the token attribute correctly"
    assert isinstance(Extract(token="12345"), Extract)
    assert isinstance(api_v2.extract, Extract)

@pytest.mark.v2
def test_extract_extract_resources(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/extract", json=MOCKS['extract_resources'], status=200)
    r = api_v2.extract.extract_resource("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_extract_extract_cooldown(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}my/ships/HMAS-1/extract", json=MOCKS['extract_cooldown'], status=200)
    r = api_v2.extract.extraction_cooldown("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_extract_survey_waypoint(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/survey", json=MOCKS['survey_waypoint'], status=200)
    r = api_v2.extract.survey_waypoint("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_extract_survey_cooldown(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}my/ships/HMAS-1/survey", json=MOCKS['survey_cooldown'], status=200)
    r = api_v2.extract.survey_cooldown("HMAS-1")
    assert isinstance(r, dict)

#
# System V2 Test
#

@pytest.mark.v2
def test_systems_init(api_v2):
    Systems(token="12345").token == "12345", "Did not set the token attribute correctly"
    assert isinstance(Systems(token="12345"), Systems)
    assert isinstance(api_v2.systems, Systems)

@pytest.mark.v2
def test_systems_chart_waypoint(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships/HMAS-1/chart", json=MOCKS['chart_waypoint'], status=200)
    r = api_v2.systems.chart_waypoint("HMAS-1")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_systems_list_systems(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems", json=MOCKS['list_systems'], status=200)
    r = api_v2.systems.list_systems()
    assert isinstance(r, dict)

@pytest.mark.v2
def test_systems_view_system(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE", json=MOCKS['view_system'], status=200)
    r = api_v2.systems.get_system("X1-OE")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_systems_list_waypoints(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/waypoints", json=MOCKS['list_waypoints'], status=200)
    r = api_v2.systems.list_waypoints("X1-OE")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_systems_view_waypoint(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/waypoints/X1-OE-PM", json=MOCKS['view_waypoints'], status=200)
    r = api_v2.systems.view_waypoint("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)

#
# Shipyards
#

@pytest.mark.v2
def test_shipyard_init(api_v2):
    Shipyard(token="12345").token == "12345", "Did not set the token attribute correctly"
    assert isinstance(Shipyard(token="12345"), Shipyard)
    assert isinstance(api_v2.shipyard, Shipyard)

@pytest.mark.v2
def test_shipyard_purchase_ship(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}my/ships", json=MOCKS['purchase_ship'], status=200)
    r = api_v2.shipyard.purchase_ship("XYZ")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_shipyard_list_shipyards(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/shipyards", json=MOCKS['list_shipyards'], status=200)
    r = api_v2.shipyard.list_shipyards("X1-OE")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_shipyard_shipyard_details(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/shipyards/X1-OE-PM", json=MOCKS['shipyard_details'], status=200)
    r = api_v2.shipyard.shipyard_details("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)

@pytest.mark.v2
def test_shipyard_shipyard_lsitings(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}systems/X1-OE/shipyards/X1-OE-PM/ships", json=MOCKS['shipyard_listings'], status=200)
    r = api_v2.shipyard.shipyard_listings("X1-OE", "X1-OE-PM")
    assert isinstance(r, dict)

#
# Ships V2 Test
#