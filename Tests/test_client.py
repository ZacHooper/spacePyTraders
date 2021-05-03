import unittest
from unittest import mock
import requests
import responses
import logging
from SpacePyTraders.client import *

TOKEN = "e283a204-f577-465f-89e4-8ff024c4344d"
USERNAME = "JimHawkins3"
BASE_URL = "https://api.spacetraders.io/"

with open('Tests/model_mocks.json','r') as infile:
    MOCKS = json.load(infile)

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


class TestUsersInit(unittest.TestCase):
    def test_users_init(self):
        self.assertIsInstance(Users("JimHawkins", "12345"), Users, "Failed to initiate the Users Class")
        self.assertEqual(Users("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Users("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestUsersMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.users = Users(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_loans_available(self):
        self.assertIsInstance(self.users.get_your_info(), dict, "API did not return dict as expected")

class TestLocationsInit(unittest.TestCase):
    def test_locations_init(self):
        self.assertIsInstance(Locations("JimHawkins", "12345"), Locations, "Failed to initiate the Locations Class")
        self.assertEqual(Locations("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Locations("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestLocationsMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.locations = Locations(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_location(self):
        self.assertIsInstance(self.locations.get_location("OE-PM-TR"), dict, "API did not return dict as expected")
    
    def test_get_ships_at_location(self):
        self.assertIsInstance(self.locations.get_ships_at_location("OE-PM-TR"), dict, "API did not return dict as expected")

    def test_get_locations_in_system(self):
        self.assertIsInstance(self.locations.get_system_locations("OE"), dict, "API did not return dict as expected")

class TestMarketplaceInit(unittest.TestCase):
    def test_marketplace_init(self):
        self.assertIsInstance(Marketplace("JimHawkins", "12345"), Marketplace, "Failed to initiate the Marketplace Class")
        self.assertEqual(Marketplace("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Marketplace("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestMarketplaceMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.marketplace = Marketplace(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_location(self):
        self.assertIsInstance(self.marketplace.get_marketplace("OE-PM-TR"), dict, "API did not return dict as expected")

class TestSellOrdersInit(unittest.TestCase):
    def test_sell_order_init(self):
        self.assertIsInstance(SellOrders("JimHawkins", "12345"), SellOrders, "Failed to initiate the SellOrders Class")
        self.assertEqual(SellOrders("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(SellOrders("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestSellOrdersMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.so = SellOrders(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_submit_flight_plan_fail(self):
        self.assertEqual(self.so.new_sell_order("12345", "FUEL", 5), False, "API call didn't fail when expected to")

class TestStructuresInit(unittest.TestCase):
    def test_structures_init(self):
        self.assertIsInstance(Structures("JimHawkins", "12345"), Structures, "Failed to initiate the Structures Class")
        self.assertEqual(Structures("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Structures("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestStructuresMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.structures = Structures(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_create_new_structure(self):
        self.assertEqual(self.structures.create_new_structure("OE-PM", "MINE"), False, "API call didn't fail when expected to")

    def test_deposit_goods(self):
        self.assertEqual(self.structures.deposit_goods("1234", "1234", "FUEL", 50), False, "API call didn't fail when expected to")

    def test_get_structure(self):
        self.assertEqual(self.structures.get_structure("1234"), False, "API call didn't fail when expected to")

    def test_get_users_structures(self):
        self.assertIsInstance(self.structures.get_users_structures()['structures'], list, "API call didn't fail when expected to")

    def test_transfer_goods(self):
        self.assertEqual(self.structures.transfer_goods("1234", "1234", "FUEL", 50), False, "API call didn't fail when expected to")

class TestSystemsInit(unittest.TestCase):
    def test_systems_init(self):
        self.assertIsInstance(Systems("JimHawkins", "12345"), Systems, "Failed to initiate the Systems Class")
        self.assertEqual(Systems("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Systems("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestSystemsMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.systems = Systems(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_systems(self):
        self.assertIsInstance(self.systems.get_systems()['systems'], list, "API call didn't return the expected list of systems")

class TestGetUserToken(unittest.TestCase):
    def test_get_user_token(self):
        self.assertIsNone(get_user_token("JimHawkins"), "Failed to handle a username that already exists")    

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