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
V2_BASE_URL = "https://v2-0-0.alpha.spacetraders.io/"

with open('Tests/model_mocks.json','r') as infile:
    MOCKS = json.load(infile)

@pytest.fixture
def api():
    # logging.disable()
    return Api(USERNAME, TOKEN)

@pytest.fixture
def api_v2() -> Api:
    with open('tests/config.json', 'r') as infile:
        token = json.load(infile)['token']
    return Api(token=token, v2=True)

@pytest.fixture
def mock_endpoints():
    res = responses.RequestsMock()
    res.start()
    return res

class TestMakeRequestFunction(unittest.TestCase):
    def setUp(self):
        logging.disable()
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    @responses.activate
    def test_make_request_get(self):
        """Tests if the method will actually make a request call and if the right method is used. 
        """
        responses.add(responses.GET, "https://api.spacetraders.io/game/status", json=MOCKS['game_status'], status=200)
        responses.add(responses.POST, "https://api.spacetraders.io/game/status", json=MOCKS['game_status'], status=200)
        res = make_request("GET", "https://api.spacetraders.io/game/status", None, None)
        self.assertEqual(res.status_code, 200, "Either game is down or GET request failed to fire properly")
    
    def test_make_request_post(self):
        res = make_request("POST", f"https://api.spacetraders.io/users/{USERNAME}/token", headers={"authentication": "Bearer " + TOKEN}, params={"test":123})
        # Want the user already created error to be returned
        self.assertEqual(res.status_code, 409, "POST request failed to fire properly")

class TestClientClassInit(unittest.TestCase):
    def test_client_with_token_init(self):
        """Tests that the Client class will correctly initiate and that the properties can be updated
        """
        self.assertIsInstance(Client("JimHawkins", "12345"), Client, "Failed to initiate the Client Class")
        self.assertEqual(Client("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Client("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestClientClassMethods(unittest.TestCase):
    def setUp(self):
        self.client = Client(USERNAME, TOKEN)
    
    def tearDown(self):
        pass

    @responses.activate
    def test_generic_endpoint_throttling_too_many_tries(self):
        """Tests that the method will correctly handle when throttling occurs and that it will throw an expection when
        it has retired a certain amount of times. """
        logging.disable()
        responses.add(responses.GET, "https://api.spacetraders.io/game/status", json={'error': {'code': 42901, 'message': 'Fail'}}, status=429)
        with self.assertRaises(TooManyTriesException):
            """Throttling handling will happen should stop after 10 times raising TooManyTriesException"""
            res = self.client.generic_api_call("GET", "game/status", token=self.client.token, throttle_time=0)
        logging.disable(logging.NOTSET)

    @responses.activate
    def test_generic_endpoint_breaking_warning_log(self):
        """Tests that the method will correctly use the warning log provided to it
        """
        responses.add(responses.GET, "https://api.spacetraders.io/game/status", json={'error': {'code': 6000, 'message': 'Fail'}}, status=600)
        with self.assertLogs(level='INFO') as cm:
            self.client.generic_api_call("GET", "game/status", warning_log="Game is currently down", token=self.client.token)
        self.assertEqual(cm.output[1], 'WARNING:root:Game is currently down', "Warning log message did not correctly be displayed on an unknown error code")    

# Ships Endpoints
# ----------------------
@pytest.mark.ships
def test_ships_init():
    """ Test that the class initiates properly """
    ship = Ships("JimHawkins", "12345")
    assert isinstance(ship, Ships)
    assert ship.username == "JimHawkins"
    assert ship.token == "12345"

@pytest.mark.ships
def test_ships_buy_ship(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/ships", json=MOCKS['buy_ship'], status=200)
    r = api.ships.buy_ship("OE-PM", "HM-MK-III")
    assert mock_endpoints.calls[0].request.params == {"location": "OE-PM", "type": "HM-MK-III"}
    assert isinstance(r, dict)

@pytest.mark.ships
def test_ships_get_users_ship(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/ships/12345", json=MOCKS['ship'], status=200)
    r = api.ships.get_ship("12345")
    assert isinstance(r, dict)

@pytest.mark.ships
def test_ships_get_users_ships(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/ships", json=MOCKS['get_user_ships'], status=200)
    r = api.ships.get_user_ships()
    assert isinstance(r, dict)

@pytest.mark.ships
def test_ships_jettison_cargo(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/ships/12345/jettison", json=MOCKS['jettison_cargo'], status=200)
    r = api.ships.jettinson_cargo("12345", "FUEL", 1)
    assert mock_endpoints.calls[0].request.params == {"good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

@pytest.mark.ships
def test_ships_scrap_ship(api: Api, mock_endpoints):
    mock_endpoints.add(responses.DELETE, f"{BASE_URL}my/ships/12345/", json=MOCKS['scrap_ship'], status=200)
    r = api.ships.scrap_ship("12345")
    assert isinstance(r, dict)

@pytest.mark.ships
def test_ships_transfer_cargo(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/ships/12345/transfer", json=MOCKS['transfer_cargo'], status=200)
    r = api.ships.transfer_cargo("12345", "54321", "FUEL", 1)
    assert mock_endpoints.calls[0].request.params == {"toShipId": "54321", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

# FlightPlan Endpoints
# ----------------------
@pytest.mark.flightplans
def test_flightplans_init():
    """ Test that the class initiates properly """
    fp = FlightPlans("JimHawkins", "12345")
    assert isinstance(fp, FlightPlans)
    assert fp.username == "JimHawkins"
    assert fp.token == "12345"

@pytest.mark.flightplans
def test_flightplans_get_flightplan(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/flight-plans/12345", json=MOCKS['flightplan'], status=200)
    r = api.flightplans.get_flight_plan("12345")
    assert isinstance(r, dict)
#match=responses.json_params_matcher({"shipId": "12345", "destination": "OE-PM"}),
@pytest.mark.flightplans
def test_flightplans_submit_flightplan(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/flight-plans", json=MOCKS['submit_flightplan'], status=200)
    r = api.flightplans.new_flight_plan("12345", "OE-PM")
    assert mock_endpoints.calls[0].request.params == {"shipId": "12345", "destination": "OE-PM"}
    assert isinstance(r, dict)

# PurchaseOrders Endpoints
# ----------------------
@pytest.mark.purchaseOrders
def test_purchaseOrder_init():
    """ Test that the class initiates properly """
    po = PurchaseOrders("JimHawkins", "12345")
    assert isinstance(po, PurchaseOrders)
    assert po.username == "JimHawkins"
    assert po.token == "12345"

@pytest.mark.purchaseOrders
def test_purchaseOrders_submit_order(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/purchase-orders",
                  json=MOCKS['purchase_order'], status=200)
    r = api.purchaseOrders.new_purchase_order("12345", "FUEL", 1)
    assert mock_endpoints.calls[0].request.params == {"shipId": "12345", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

    
class TestGame(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.game = Game(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Game Status
        responses.add(responses.GET, f"{BASE_URL}game/status", json=MOCKS['game_status'], status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_game_init(self):
        """Test if the Game class initialises properly"""
        self.assertIsInstance(Game("JimHawkins", "12345"), Game, "Failed to initiate the Game Class")
        self.assertEqual(Game("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Game("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")
    
    # Game Status
    # ----------------
    @responses.activate
    def test_get_game_status_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.game.get_game_status(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to game's status")    

# Loan Endpoints
# ----------------------
@pytest.mark.loans
def test_loans_init():
    """ Test that the class initiates properly """
    loan = Loans("JimHawkins", "12345")
    assert isinstance(loan, Loans)
    assert loan.username == "JimHawkins"
    assert loan.token == "12345"

@pytest.mark.loans
def test_loans_get_loans(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/loans", json=MOCKS['user_loan'], status=200)
    r = api.loans.get_user_loans()
    assert isinstance(r, dict)

@pytest.mark.loans
def test_loans_request_loans(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/loans", json=MOCKS['request_loan'], status=200)
    r = api.loans.request_loan("STARTUP")
    assert mock_endpoints.calls[0].request.params == {"type": "STARTUP"}
    assert isinstance(r, dict)

@pytest.mark.loans
def test_loans_pay_loans(api: Api, mock_endpoints):
    mock_endpoints.add(responses.PUT, f"{BASE_URL}my/loans/12345", json=MOCKS['pay_loan'], status=200)
    r = api.loans.pay_off_loan("12345")
    assert isinstance(r, dict)

# Location Tests
# ----------------
@pytest.mark.locations
def test_locations_init():
    location = Locations("JimHawkins", "12345")
    assert isinstance(location, Locations)
    assert location.username == "JimHawkins", "Username did not initiate correctly"
    assert location.token == "12345", "Token did not initiate correctly"

@pytest.mark.locations
def test_get_marketplace(api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"https://api.spacetraders.io/locations/OE-PM/marketplace", json={"GET_EXAMPLE": "EXAMPLE"}, status=200)
    r = api.locations.get_marketplace("OE-PM")
    assert isinstance(r, dict)

@pytest.mark.locations
def test_get_location_endpoint(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}locations/OE-PM", json=MOCKS['location'], status=200)
    r = api.locations.get_location("OE-PM")
    assert isinstance(r, dict)

@pytest.mark.locations
def test_get_location_ships_endpoint(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}locations/OE-PM/ships", json={'get_location_ships':'get response'}, status=200)
    r = api.locations.get_ships_at_location("OE-PM")
    assert isinstance(r, dict)

# SellOrders Endpoints
# ----------------------
@pytest.mark.sellOrders
def test_sellOrders_init():
    """ Test that the class initiates properly """
    po = SellOrders("JimHawkins", "12345")
    assert isinstance(po, SellOrders)
    assert po.username == "JimHawkins"
    assert po.token == "12345"

@pytest.mark.sellOrders
def test_sellOrders_submit_order(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/sell-orders",
                  json=MOCKS['sell_order'], status=200)
    r = api.sellOrders.new_sell_order("12345", "FUEL", 1)
    assert mock_endpoints.calls[0].request.params == {"shipId": "12345", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

# Structures Endpoints
# ----------------------
@pytest.mark.structures
def test_structures_init():
    """ Test that the class initiates properly """
    structure = Structures("JimHawkins", "12345")
    assert isinstance(structure, Structures)
    assert structure.username == "JimHawkins"
    assert structure.token == "12345"

@pytest.mark.structures
def test_strucutres_create_structure(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/structures", json=MOCKS['create_structures'], status=200)
    r = api.structures.create_new_structure("OE-PM", "MINE")
    assert mock_endpoints.calls[0].request.params == {"location": "OE-PM", "type": "MINE"}
    assert isinstance(r, dict)

@pytest.mark.structures
def test_strucutres_deposit_to_user_structure(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/structures/12345/deposit", json=MOCKS['deposit_to_user_structure'], status=200)
    r = api.structures.deposit_goods("12345", "54321", "FUEL", "1")
    assert mock_endpoints.calls[0].request.params == {"shipId": "54321", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

@pytest.mark.structures
def test_structures_transfer_to_ship(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/structures/12345/transfer", json=MOCKS['transfer_to_ship_'], status=200)
    r = api.structures.transfer_goods("12345", "54321", "FUEL", "1")
    assert mock_endpoints.calls[0].request.params == {"shipId": "54321", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

@pytest.mark.structures
def test_structures_get_user_structure(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/structures/12345", json=MOCKS['get_user_structure'], status=200)
    r = api.structures.get_structure("12345")
    assert isinstance(r, dict)

@pytest.mark.structures
def test_structures_get_user_structures(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/structures", json=MOCKS['get_user_structures'], status=200)
    r = api.structures.get_users_structures()
    assert isinstance(r, dict) 

@pytest.mark.structures
def test_strucutres_deposit_to_a_structure(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}structures/12345/deposit", json=MOCKS['deposit_to_a_structure'], status=200)
    r = api.structures.deposit_goods("12345", "54321", "FUEL", "1", user_owned=False)
    assert mock_endpoints.calls[0].request.params == {"shipId": "54321", "good": "FUEL", "quantity": "1"}
    assert isinstance(r, dict)

@pytest.mark.structures
def test_structures_get_a_structure(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}structures/12345", json=MOCKS['get_a_structure'], status=200)
    r = api.structures.get_structure("12345", user_owned=False)
    assert isinstance(r, dict)


class TestSystems(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.systems = Systems(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Get System
        responses.add(responses.GET, f"{BASE_URL}game/systems", json=MOCKS['system'], status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_systems_init(self):
        self.assertIsInstance(Systems("JimHawkins", "12345"), Systems, "Failed to initiate the Systems Class")
        self.assertEqual(Systems("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Systems("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Get System
    # ----------------
    @responses.activate
    def test_get_systems_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.systems.get_systems(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get system") 

# System Endpoints
# ----------------
@pytest.mark.systems
def test_system_get_active_flightplans(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"https://api.spacetraders.io/systems/OE/flight-plans", json={'flightPlans': 'get the response'}, status=200) 
    r = api.systems.get_active_flight_plans("OE")
    assert isinstance(r, dict)

@pytest.mark.systems
def test_system_get_system_locations(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}systems/OE/locations", json=MOCKS['system'], status=200)
    r = api.systems.get_system_locations("OE")
    assert isinstance(r, dict)

@pytest.mark.systems
def test_system_get_system_docked_ships(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}systems/OE/ships", json=MOCKS['system_docked_ships'], status=200)
    r = api.systems.get_system_docked_ships("OE")
    assert isinstance(r, dict)

@pytest.mark.systems
def test_system_get_a_system(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}systems/OE", json=MOCKS['get_system'], status=200)
    r = api.systems.get_system("OE")
    assert isinstance(r, dict)

@pytest.mark.systems
def test_system_get_available_ships(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}systems/OE/ship-listings", json=MOCKS['system_ship_listings'], status=200)
    r = api.systems.get_available_ships("OE")
    assert isinstance(r, dict)

class TestLeaderboard(unittest.TestCase):
    """Tests API calls related to the Game/Leaderboard"""
    def setUp(self):
        logging.disable()
        self.leaderboard = Leaderboard(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Endpoints
        responses.add(responses.GET, "https://api.spacetraders.io/game/leaderboard/net-worth")
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_leaderboard_init(self):
        self.assertIsInstance(Leaderboard("JimHawkins", "12345"), Leaderboard, "Failed to initiate the Leaderboard Class")
        self.assertEqual(Leaderboard("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Leaderboard("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")    

    @responses.activate
    def test_submit_purchase_order_url(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.leaderboard.get_player_net_worths(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get net-worth leaderboard") 

# Account Endpoints
# ----------------
@pytest.mark.account
def test_account_init():
    account = Account("JimHawkins", "12345")
    assert isinstance(account, Account)
    assert account.username == "JimHawkins", "Did not set the username attribute correctly"
    assert account.token == "12345", "Did not set the token attribute correctly"

@pytest.mark.account
def test_account_get_info(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}my/account", json=MOCKS['user'], status=200)
    assert api.account.info() is not False

# Types Endpoints
# ----------------
@pytest.mark.types
def test_types_init():
    assert isinstance(Types("JimHawkins", "12345"), Types)
    assert Types("JimHawkins", "12345").username == "JimHawkins", "Did not set the username attribute correctly"
    assert Types("JimHawkins", "12345").token == "12345", "Did not set the token attribute correctly"

@pytest.mark.types
def test_types_get_goods(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}types/goods", json=MOCKS['types_goods'], status=200)
    r = api.types.goods()
    assert isinstance(r, dict)

@pytest.mark.types
def test_types_loans(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}types/loans", json=MOCKS['types_loans'], status=200)
    r = api.types.loans()
    assert isinstance(r, dict)

@pytest.mark.types
def test_types_structures(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}types/structures", json=MOCKS['types_structures'], status=200)
    r = api.types.structures()
    assert isinstance(r, dict)

@pytest.mark.types
def test_types_ships(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}types/ships", json=MOCKS['get_available_ships'], status=200)
    r = api.types.ships()
    assert isinstance(r, dict)

# Warp Jump Endpoints
# ----------------

@pytest.mark.warpjump
def test_warp_jump_init():
    assert isinstance(WarpJump("JimHawkins", "12345"), WarpJump)
    assert WarpJump("JimHawkins", "12345").username == "JimHawkins", "Did not set the username attribute correctly"
    assert WarpJump("JimHawkins", "12345").token == "12345", "Did not set the token attribute correctly"

@pytest.mark.warpjump
def test_warp_jump_attempt_jump(api: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{BASE_URL}my/warp-jumps", json=MOCKS['warp_jump'], status=200)
    r = api.warpjump.attempt_jump("12345")
    assert mock_endpoints.calls[0].request.params == {"shipId": "12345"}
    assert isinstance(r, dict)

#
# ALL V2 API TESTS GO BELOW HERE
#

@pytest.mark.v2
def test_api_v2(api: api_v2):
    assert isinstance(api, Api)

#
# Agent Class Related Tests
#

@pytest.mark.v2
def test_agent_init(api_v2):
    assert isinstance(Agent(token="12345", v2=True), Agent)
    assert isinstance(api_v2.agent, Agent)
    assert Agent(token="12345", v2=True).token == "12345", "Did not set the token attribute correctly"

@pytest.mark.v2
def test_agent_get_agent_details(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{V2_BASE_URL}my/agent", json=MOCKS['agent_details'], status=200)
    r = api_v2.agent.get_my_agent_details()
    assert isinstance(r, dict)

@pytest.mark.v2
def test_agent_register_new_agent(api_v2: Api, mock_endpoints):
    mock_endpoints.add(responses.POST, f"{V2_BASE_URL}agents", json=MOCKS['register_new_agent'], status=200)
    r = api_v2.agent.register_new_agent('spacePyTrader', 'COMMERCE_REPUBLIC')
    assert mock_endpoints.calls[0].request.params == {"symbol": "spacePyTrader", "faction": "COMMERCE_REPUBLIC"}
    assert isinstance(r, dict)

#
# Markets related tests
#

@pytest.mark.v2
def test_markets_init(api_v2):
    assert isinstance(Markets(token="12345", v2=True), Markets)
    assert isinstance(api_v2.markets, Markets)
    assert Markets(token="12345", v2=True).token == "12345", "Did not set the token attribute correctly"

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
    assert isinstance(Trade(token="12345", v2=True), Trade)
    assert isinstance(api_v2.trade, Trade)
    assert Trade(token="12345", v2=True).token == "12345", "Did not set the token attribute correctly"

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