import unittest
import logging
from SpaceTraders.client import *

TOKEN = "0930cc36-7dc7-4cb1-8823-d8e72594d91e"
USERNAME = "JimHawkins"

class TestMakeRequestFunction(unittest.TestCase):
    def setUp(self):
        logging.disable()
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_make_request_get(self):
        res = make_request("GET", "https://api.spacetraders.io/game/status", None, None)
        self.assertEqual(res.status_code, 200, "Either game is down or GET request failed to fire properly")
    
    def test_make_request_post(self):
        res = make_request("POST", "https://api.spacetraders.io/users/JimHawkins/token", None, None)
        # Want the user already created error to be returned
        self.assertEqual(res.status_code, 409, "POST request failed to fire properly")
    
    def test_make_request_bad_method(self):
        self.assertRaises(KeyError, make_request, "BLAH", "https://api.spacetraders.io/users/JimHawkins/token", None, None)

class TestClientClassInit(unittest.TestCase):
    def test_client_with_token_init(self):
        self.assertIsInstance(Client("JimHawkins", "12345"), Client, "Failed to initiate the Client Class")
        self.assertEqual(Client("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Client("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestShipInit(unittest.TestCase):
    def test_ships_init(self):
        self.assertIsInstance(Ships("JimHawkins", "12345"), Ships, "Failed to initiate the Ships Class")
        self.assertEqual(Ships("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Ships("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestShipMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.ships = Ships(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    def test_ships_scrap_ship(self):
        # This should fail as expected and return false
        self.assertEqual(self.ships.scrap_ship("12345"), False, "API call didn't fail when expected to")
    
    def test_ships_buy_ship(self):
        self.assertEqual(self.ships.buy_ship("OE-BO", "HM-MK-III"), False, "API call didn't fail when expected to")
    
    def test_get_available_ships(self):
        self.assertEqual(self.ships.get_available_ships("MK-IIII"), False, "API call didn't fail when expected to")

    def test_ships_get_ship_info(self):
        self.assertEqual(self.ships.get_ship("1234"), False, "API call didn't fail when expected to")
    
    def test_get_list_of_users_ships(self):
        self.assertIsInstance(self.ships.get_user_ships()['ships'], list, "API didn't return the expected list")

    def test_jettison_cargo(self):
        self.assertEqual(self.ships.jettinson_cargo("1234", "FUEL", 50), False, "API call didn't fail when expected to")

    def test_transfer_cargo(self):
        self.assertEqual(self.ships.transfer_cargo("1221345", "1234", "FUEL", 50), False, "API call didn't fail when expected to")

class TestFlightPlanInit(unittest.TestCase):
    def test_flight_plan_init(self):
        self.assertIsInstance(FlightPlans("JimHawkins", "12345"), FlightPlans, "Failed to initiate the FlightPlans Class")
        self.assertEqual(FlightPlans("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(FlightPlans("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestFlightPlanMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.fp = FlightPlans(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_submit_flight_plan_fail(self):
        self.assertEqual(self.fp.new_flight_plan("12345", "OE-PM-TR"), False, "API call didn't fail when expected to")

    def test_get_active_flight_plans_fail(self):
        self.assertEqual(self.fp.get_active_flight_plans("OEV"), False, "API call didn't fail when expected to")

    def test_get_active_flight_plan(self):
        self.assertEqual(self.fp.get_flight_plan("456789"), False, "API call didn't fail when expected to")

class TestPurchaseOrderInit(unittest.TestCase):
    def test_purchase_order_init(self):
        self.assertIsInstance(PurchaseOrders("JimHawkins", "12345"), PurchaseOrders, "Failed to initiate the PurchaseOrders Class")
        self.assertEqual(PurchaseOrders("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(PurchaseOrders("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestPurchaseOrderMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.po = PurchaseOrders(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_submit_flight_plan_fail(self):
        self.assertEqual(self.po.new_purchase_order("12345", "FUEL", 5), False, "API call didn't fail when expected to")

class TestGameInit(unittest.TestCase):
    def test_game_init(self):
        self.assertIsInstance(Game("JimHawkins", "12345"), Game, "Failed to initiate the Game Class")
        self.assertEqual(Game("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Game("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestGameMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.game = Game(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_game_status(self):
        self.assertIsInstance(self.game.get_game_status(), dict, "API did not return dict as expected")

class TestLoansInit(unittest.TestCase):
    def test_loans_init(self):
        self.assertIsInstance(Loans("JimHawkins", "12345"), Loans, "Failed to initiate the Loans Class")
        self.assertEqual(Loans("JimHawkins", "12345").username, "JimHawkins", "Did not set the username attribute correctly")
        self.assertEqual(Loans("JimHawkins", "12345").token, "12345", "Did not set the token attribute correctly")

class TestLoansMethods(unittest.TestCase):
    def setUp(self):
        logging.disable()
        self.loans = Loans(USERNAME, TOKEN)
    
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_get_loans_available(self):
        self.assertIsInstance(self.loans.get_loans_available(), dict, "API did not return dict as expected")

    def test_get_user_loans(self):
        self.assertIsInstance(self.loans.get_user_loans(), dict, "API did not return dict as expected")

    def test_pay_off_loan(self):
        self.assertEqual(self.loans.pay_off_loan("asdfasdf"), False, "API did not fail as expected")

    def test_request_loan(self):
        self.assertEqual(self.loans.pay_off_loan("asdfasdf"), False, "API did not fail as expected")

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

 