import unittest
import requests
import responses
import logging
from SpacePyTraders.client import *
import pytest
from collections import namedtuple

TOKEN = "e8c9ac0d-e1ec-45e9-b808-d622a7717f46"
USERNAME = "JimHawkins"
BASE_URL = "https://api.spacetraders.io/"

with open('Tests/model_mocks.json','r') as infile:
    MOCKS = json.load(infile)

@pytest.fixture
def api():
    # logging.disable()
    return Api(USERNAME, TOKEN)

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

class TestShip(unittest.TestCase):
    def setUp(self):
        """Sets Up the test with the mock responses and disables logging
        """
        logging.disable()
        self.ships = Ships(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Buy ship
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/ships", json=MOCKS['buy_ship'], status=200)
        # Scrap Ship
        responses.add(responses.DELETE, f"{BASE_URL}users/{USERNAME}/ships/12345/", json={'ship':'scrap_ship - get actual response'}, status=200)
        # Get available Ships
        responses.add(responses.GET, f"{BASE_URL}game/ships", json=MOCKS['get_available_ships'], status=200)
        # Get specific ship
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/ships/12345", json=MOCKS['ship'], status=200)
        # Get all user's ships
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/ships", json=MOCKS['get_user_ships'], status=200)
        # Jettison Cargo
        responses.add(responses.PUT, f"{BASE_URL}users/{USERNAME}/ships/12345/jettison", json={'ship':'jettison_cargo - get actual response'}, status=200)
        # Transfer Cargo
        responses.add(responses.PUT, f"{BASE_URL}users/{USERNAME}/ships/12345/transfer", json={'ship':'transfer_cargo - get actual response'}, status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    # Init Ship Client Class
    # ----------------------
    def test_ships_init(self):
        """Tests that the User class will correctly initiate and that the properties can be updated
        """
        self.assertIsInstance(Ships("JimHawkins", "12345"), Ships, "Failed to initiate the Ships Class")
        self.assertEqual(Ships("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Ships("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")
    
    # Scrap Ship
    # ----------------------
    @responses.activate
    def test_ships_scrap_ship_endpoint(self):
        """Tests that the method uses the correct endpoint"""
        self.assertNotIsInstance(self.ships.scrap_ship("12345"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to buy a ship")
    
    @responses.activate
    def test_ships_scrap_ship_params(self):
        """Tests that no parameters are passed to the API"""
        self.ships.scrap_ship("12345")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters were supplied to the request when there shouldn't have been any")

    @responses.activate
    def test_ships_scrap_ship_missing_param(self):
        """Tests that an exception is raised when there are missing parameters"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.ships.scrap_ship()

    # Buy Ship
    # ----------------------
    @responses.activate
    def test_ships_buy_ship_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.buy_ship("OE-BO", "HM-MK-III"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to scrap a ship")
    
    @responses.activate
    def test_ships_buy_ship_params(self):
        """Tests that the correct parameter keys are being used for the API call"""
        self.ships.buy_ship("OE-BO", "HM-MK-III")
        self.assertEqual(responses.calls[0].request.params, {"location": 'OE-BO', "type": "HM-MK-III"}, "Incorrect parameters were supplied to the request")

    @responses.activate
    def test_ships_buy_ship_missing_param(self):
        """Tests that an exception is raised when required arguments are missing"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.ships.buy_ship("OE-BO")

    # Get Available Ships
    # ----------------------
    @responses.activate
    def test_ships_get_available_ships_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.get_available_ships("MK-III"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to list available ships")
    
    @responses.activate
    def test_ships_get_available_ships_params(self):
        """Tests that the correct parameter keys are being used for the API call"""
        self.ships.get_available_ships("MK-III")
        self.assertEqual(responses.calls[0].request.params, {"class": 'MK-III'}, "Incorrect parameters were supplied to the request")

    # Get Ship
    # ----------------------
    @responses.activate
    def test_ships_get_ship_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.get_ship("12345"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to get a ship's info")
    
    @responses.activate
    def test_ships_get_ship_params(self):
        """Tests that the correct parameter keys are being used for the API call"""
        self.ships.get_ship("12345")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters were supplied to the request when there shouldn't have been")

    @responses.activate
    def test_ships_get_ship_missing_param(self):
        """Tests that an exception is raised when required arguments are missing"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.ships.get_ship()
    
    # Get User's Ships
    # ----------------------
    @responses.activate
    def test_ships_get_user_ships_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.get_user_ships(), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to get a list of the user's ships")
    
    # Jettison Cargo from Ship
    # ----------------------
    @responses.activate
    def test_ships_jettison_cargo_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.jettinson_cargo("12345", "FUEL", 50), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to jettison a ship's cargo")
    
    @responses.activate
    def test_ships_jettison_cargo_params(self):
        """Tests that the correct parameter keys are being used for the API call"""
        self.ships.jettinson_cargo("12345", "FUEL", 50)
        self.assertEqual(responses.calls[0].request.params, {'good': 'FUEL', 'quantity': '50'}, "Parameters were supplied to the request when there shouldn't have been")

    @responses.activate
    def test_ships_jettison_cargo_missing_param(self):
        """Tests that an exception is raised when required arguments are missing"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.ships.jettinson_cargo("12345", "FUEL")

    # Transfer Cargo from Ship to Ship
    # ----------------------
    @responses.activate
    def test_ships_transfer_cargo_endpoint(self):
        """Test that the correct endpoint is being used"""
        self.assertNotIsInstance(self.ships.transfer_cargo("12345", "123456", "FUEL", 50), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint ({responses.calls[0].request.url}) was used to transfer a ship's cargo")
    
    @responses.activate
    def test_ships_transfer_cargo_params(self):
        """Tests that the correct parameter keys are being used for the API call"""
        self.ships.transfer_cargo("12345", "123456", "FUEL", 50)
        self.assertEqual(responses.calls[0].request.params, {'toShipId': '123456', 'good': 'FUEL', 'quantity': '50'}, "Parameters were supplied to the request when there shouldn't have been")

    @responses.activate
    def test_ships_transfer_cargomissing_param(self):
        """Tests that an exception is raised when required arguments are missing"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.ships.transfer_cargo("12345", "123456", "FUEL")    

class TestFlightPlan(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.fp = FlightPlans(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Submit Flight Plan
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/flight-plans", json=MOCKS['flight_plan'], status=200)
        # All active flight plans
        responses.add(responses.GET, f"{BASE_URL}game/systems/OE/flight-plans", json={'flightPlans': 'get the response'}, status=200)
        # Get active flight
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/flight-plans/456789", json={'flightPlans': 'get the response'}, status=200)
        
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_flight_plan_init(self):
        self.assertIsInstance(FlightPlans("JimHawkins", "12345"), FlightPlans, "Failed to initiate the FlightPlans Class")
        self.assertEqual(FlightPlans("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(FlightPlans("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Submit Flight Plan
    # ----------------------
    @responses.activate
    def test_submit_flight_plan_endpoint(self):
        """Tests that the method uses the correct endpoint"""
        self.assertNotIsInstance(self.fp.new_flight_plan("12345", "OE-PM-TR"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint was used to submit a flight plan")
    
    @responses.activate
    def test_submit_flight_plan_params(self):
        """Tests that no parameters are passed to the API"""
        self.fp.new_flight_plan("12345", "OE-PM-TR")
        self.assertEqual(responses.calls[0].request.params, {'destination': 'OE-PM-TR', 'shipId': '12345'}, "Parameters were supplied to the request when there shouldn't have been any")

    @responses.activate
    def test_submit_flight_plan_missing_param(self):
        """Tests that an exception is raised when there are missing parameters"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.fp.new_flight_plan("12345")

    # Get All Active Flight Plans
    # ----------------------
    @responses.activate
    def test_get_active_flight_plans_endpoint(self):
        """Tests that the method uses the correct endpoint"""
        self.assertNotIsInstance(self.fp.get_active_flight_plans("OE"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint () was used to get all flight plans")
    
    @responses.activate
    def test_get_active_flight_plans_params(self):
        """Tests that no parameters are passed to the API"""
        self.fp.get_active_flight_plans("OE")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters were supplied to the request when there shouldn't have been any")

    @responses.activate
    def test_get_active_flight_plans_param(self):
        """Tests that an exception is raised when there are missing parameters"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.fp.get_active_flight_plans()

    # Get an Active Flight Plan
    # ----------------------
    @responses.activate
    def test_get_active_flight_plan_endpoint(self):
        """Tests that the method uses the correct endpoint"""
        self.assertNotIsInstance(self.fp.get_flight_plan("456789"), 
                                 requests.exceptions.ConnectionError, 
                                 f"Incorrect endpoint was used to get a flight plan")
    
    @responses.activate
    def test_get_active_flight_plan_params(self):
        """Tests that no parameters are passed to the API"""
        self.fp.get_flight_plan("456789")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters were supplied to the request when there shouldn't have been any")

    @responses.activate
    def test_get_active_flight_plan_param(self):
        """Tests that an exception is raised when there are missing parameters"""
        with self.assertRaises(TypeError, msg="Error wasn't raised when there was a missing parameter"):
            self.fp.get_flight_plan()

class TestPurchaseOrder(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.po = PurchaseOrders(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()

        responses.add(responses.POST, f"https://api.spacetraders.io/users/{USERNAME}/purchase-orders",
                      json={'error': 'not found'}, status=200)

        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_purchase_order_init(self):
        self.assertIsInstance(PurchaseOrders("JimHawkins", "12345"), PurchaseOrders, "Failed to initiate the PurchaseOrders Class")
        self.assertEqual(PurchaseOrders("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(PurchaseOrders("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    @responses.activate
    def test_submit_purchase_order_url(self):
        self.assertNotIsInstance(self.po.new_purchase_order("12345", "FUEL", 5), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to make Purchase Order Request")

    @responses.activate                           
    def test_submit_purchase_order_params(self):
        self.po.new_purchase_order("12345", "FUEL", 5)
        self.assertEqual(responses.calls[0].request.params, {"shipId": '12345', "good": "FUEL", "quantity": '5'}, "Incorrect parameters were supplied to the request")

    @responses.activate                           
    def test_submit_purchase_order_missing_param(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.po.new_purchase_order("12345", "FUEL")
    
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

class TestLoans(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.loans = Loans(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Get Available Loans
        responses.add(responses.GET, f"{BASE_URL}game/loans", json={'loans':'Get response'}, status=200)
        # User's Loans
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/loans", json=MOCKS['user_loan'], status=200)
        # Pay off loan
        responses.add(responses.PUT, f"{BASE_URL}users/{USERNAME}/loans/12345", json={'pay_loan':'Get response'}, status=200)
        # Request Loan
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/loans", json=MOCKS['request_loan'], status=200)

    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_loans_init(self):
        self.assertIsInstance(Loans("JimHawkins", "12345"), Loans, "Failed to initiate the Loans Class")
        self.assertEqual(Loans("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Loans("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Get Available Loans
    # ----------------
    @responses.activate
    def test_get_loans_available_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.loans.get_loans_available(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get availabe loans") 

    # Get User Loans
    # ----------------
    @responses.activate
    def test_get_user_loans_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.loans.get_user_loans(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get user's loans") 

    # Pay Off Loan
    # ----------------
    @responses.activate
    def test_pay_off_loan_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.loans.pay_off_loan("12345"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to pay of user loan") 

    @responses.activate                           
    def test_pay_off_loan_params(self):
        self.loans.pay_off_loan("12345")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters were supplied when there shouldn't have been any")

    @responses.activate                           
    def test_pay_off_loan_missing_param(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.loans.pay_off_loan()

    # Request Loan
    # ----------------
    @responses.activate
    def test_request_loan_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.loans.request_loan("STARTUP"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to pay of user loan") 

    @responses.activate                           
    def test_request_loan_params(self):
        self.loans.request_loan("STARTUP")
        self.assertEqual(responses.calls[0].request.params, {'type': 'STARTUP'}, "Incorrect parameters supplied to request")

    @responses.activate                           
    def test_request_loan_missing_param(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.loans.request_loan()    

class TestUsers(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.users = Users(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Get User Info
        responses.add(responses.GET, f"{BASE_URL}my/account", json=MOCKS['user'], status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_users_init(self):
        self.assertIsInstance(Users("JimHawkins", "12345"), Users, "Failed to initiate the Users Class")
        self.assertEqual(Users("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Users("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Request Loan
    # ----------------
    @responses.activate
    def test_get_user_info(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.users.get_your_info(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get user info")     

class TestLocations(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.locations = Locations(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Get a location
        responses.add(responses.GET, f"{BASE_URL}game/locations/OE-PM", json=MOCKS['location'], status=200)
        # Get ships at a location
        responses.add(responses.GET, f"{BASE_URL}game/locations/OE-PM/ships", json={'get_location_ships':'get response'}, status=200)
        # Get locations in a system
        responses.add(responses.GET, f"{BASE_URL}game/systems/OE/locations", json=MOCKS['system'], status=200)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_locations_init(self):
        self.assertIsInstance(Locations("JimHawkins", "12345"), Locations, "Failed to initiate the Locations Class")
        self.assertEqual(Locations("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Locations("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Get a Location
    # ----------------
    @responses.activate
    def test_get_location_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.locations.get_location("OE-PM"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get a location") 

    @responses.activate                           
    def test_get_location_params(self):
        self.locations.get_location("OE-PM")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_get_location_missing_params(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.locations.get_location()   

    # Get ships at a Location
    # ----------------
    @responses.activate
    def test_get_ships_at_location_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.locations.get_ships_at_location("OE-PM"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get ships at a location") 

    @responses.activate                           
    def test_get_ships_at_location_params(self):
        self.locations.get_ships_at_location("OE-PM")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_get_ships_at_location_missing_params(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.locations.get_location()    
    
    # Get locations in a system
    # ----------------
    @responses.activate
    def test_get_locations_in_system_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.locations.get_system_locations("OE"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get locations in a system") 

    @responses.activate                           
    def test_get_locations_in_system_params(self):
        self.locations.get_system_locations("OE")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_get_locations_in_system_missing_params(self):
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.locations.get_system_locations()    

# Location Tests
# ----------------
@pytest.mark.locations
@pytest.mark.test
def test_get_marketplace(api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"https://api.spacetraders.io/game/locations/OE-PM/marketplace", json={"GET_EXAMPLE": "EXAMPLE"}, status=200)
    r = api.locations.get_marketplace("OE-PM")
    assert isinstance(r, dict)



class TestMarketplace(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.marketplace = Marketplace(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Get Marketplace
        responses.add(responses.GET, f"{BASE_URL}game/locations/OE-PM/marketplace", 
                      json=MOCKS['location_marketplace'], status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_marketplace_init(self):
        """Test initialisation of the Marketplace client Class"""
        self.assertIsInstance(Marketplace("JimHawkins", "12345"), Marketplace, "Failed to initiate the Marketplace Class")
        self.assertEqual(Marketplace("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Marketplace("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Get location's marketplace
    # ----------------
    @responses.activate
    def test_get_marketplace_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.marketplace.get_marketplace("OE-PM"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get a location's marketplace") 

    @responses.activate                           
    def test_get_marketplace_params(self):
        """Test that no parameters are pulled into the request"""
        self.marketplace.get_marketplace("OE-PM")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_get_marketplace_missing_params(self):
        """Test that an exception is raised if any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.marketplace.get_marketplace()     

class TestSellOrders(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.so = SellOrders(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Make a sell order
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/sell-orders", json={'sell_order':'get response'}, status=200)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_sell_order_init(self):
        self.assertIsInstance(SellOrders("JimHawkins", "12345"), SellOrders, "Failed to initiate the SellOrders Class")
        self.assertEqual(SellOrders("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(SellOrders("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

    # Get location's marketplace
    # ----------------
    @responses.activate
    def test_get_marketplace_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.so.new_sell_order("12345", "FUEL", 5), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to make a sell order") 

    @responses.activate                           
    def test_get_marketplace_params(self):
        """Test that the correct parameters are placed into the request"""
        self.so.new_sell_order("12345", "FUEL", 5)
        self.assertEqual(responses.calls[0].request.params, {'good':'FUEL', 'quantity':'5', 'shipId':'12345'}, "Incorrect parameters supplied for request")

    @responses.activate                           
    def test_get_marketplace_missing_params(self):
        """Test that an exception is raised when any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.so.new_sell_order("12345", "FUEL")

class TestStructures(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.structures = Structures(USERNAME, TOKEN)
        self.responses = responses.RequestsMock()
        self.responses.start()
        # Create a new structure
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/structures", json={'new_structure':'get response'}, status=200)
        # Deposit Goods Into Structure
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/structures/12345/deposit", json={'deposit_goods':'get response'}, status=200)
        # Get A structure
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/structures/12345", json={'get_strucutre':'get response'}, status=200)
        # Get a list of users structures
        responses.add(responses.GET, f"{BASE_URL}users/{USERNAME}/structures", json={'structure_list':'get response'}, status=200)
        # Transfer Goods from structure
        responses.add(responses.POST, f"{BASE_URL}users/{USERNAME}/structures/12345/transfer", json={'transfer_goods':'get response'}, status=200)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def test_structures_init(self):
        self.assertIsInstance(Structures("JimHawkins", "12345"), Structures, "Failed to initiate the Structures Class")
        self.assertEqual(Structures("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Structures("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")


    # Create Structure
    # ----------------
    @responses.activate
    def test_create_new_structure_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.structures.create_new_structure("OE-PM", "MINE"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to make a structure") 

    @responses.activate                           
    def test_create_new_structure_params(self):
        """Test that the correct parameters are placed into the request"""
        self.structures.create_new_structure("OE-PM", "MINE")
        self.assertEqual(responses.calls[0].request.params, {'location':'OE-PM', 'type':'MINE'}, "Incorrect parameters supplied for request")

    @responses.activate                           
    def test_create_new_structure_missing_params(self):
        """Test that an exception is raised when any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.structures.create_new_structure("OE-PM")


    # Deposit Goods in Structure
    # ----------------
    @responses.activate
    def test_deposit_goods_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.structures.deposit_goods("12345", "54321", "FUEL", 50), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to deposit goods into structure") 

    @responses.activate                           
    def test_deposit_goods_params(self):
        """Test that the correct parameters are placed into the request"""
        self.structures.deposit_goods("12345", "54321", "FUEL", 50)
        self.assertEqual(responses.calls[0].request.params, {'shipId':'54321', 'good':'FUEL', 'quantity':'50'}, "Incorrect parameters supplied for request")

    @responses.activate                           
    def test_deposit_goods_missing_params(self):
        """Test that an exception is raised when any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.structures.deposit_goods("1234", "1234", "FUEL")


    # Get Structure
    # ----------------
    @responses.activate
    def test_get_structure_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.structures.get_structure("12345"), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get structure") 

    @responses.activate                           
    def test_get_structure_params(self):
        """Test that the correct parameters are placed into the request"""
        self.structures.get_structure("12345")
        self.assertEqual(responses.calls[0].request.params, {}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_get_structure_missing_params(self):
        """Test that an exception is raised when any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.structures.get_structure()


    # Get User's Structures
    # ----------------
    @responses.activate
    def test_get_users_structures_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.structures.get_users_structures(), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to get list of user's structures")


    # Get Structure
    # ----------------
    @responses.activate
    def test_transfer_goods_endpoint(self):
        """Test that the correct endpoint is used"""
        self.assertNotIsInstance(self.structures.transfer_goods("12345", "54321", "FUEL", 50), 
                                 requests.exceptions.ConnectionError, 
                                 "Incorrect endpoint was used to transfer goods from structure") 

    @responses.activate                           
    def test_transfer_goods_params(self):
        """Test that the correct parameters are placed into the request"""
        self.structures.transfer_goods("12345", "54321", "FUEL", 50)
        self.assertEqual(responses.calls[0].request.params, {'shipId':'54321', 'good':'FUEL', 'quantity':'50'}, "Parameters supplied when there shouldn't have been any")

    @responses.activate                           
    def test_transfer_goods_missing_params(self):
        """Test that an exception is raised when any required arguments are missing"""
        with self.assertRaises(TypeError, msg="Type Error not raised when required parameter missing"):
            self.structures.transfer_goods("12345", "54321", "FUEL")

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
    mock_endpoints.add(responses.GET, f"https://api.spacetraders.io/game/systems/OE/flight-plans", json={'flightPlans': 'get the response'}, status=200) 
    r = api.systems.get_active_flight_plans("OE")
    assert isinstance(r, dict)

@pytest.mark.systems
def test_system_get_system_locations(api: Api, mock_endpoints):
    mock_endpoints.add(responses.GET, f"{BASE_URL}game/systems/OE/locations", json=MOCKS['system'], status=200)
    r = api.systems.get_system_locations("OE")
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
@pytest.fixture
def my():
    logging.disable()
    return My(USERNAME, TOKEN)

def test_my_account(my):
    responses.add(responses.GET, f"{BASE_URL}my/account", json=MOCKS['user'], status=200)
    assert my.account() is not False

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