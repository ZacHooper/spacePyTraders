import unittest
import logging
import json
from SpacePyTraders.models import *

TOKEN = "0930cc36-7dc7-4cb1-8823-d8e72594d91e"
USERNAME = "JimHawkins"

with open('./Tests/model_mocks.json', 'r') as infile:
    MOCKS = json.load(infile)

class TestUserInit(unittest.TestCase):
    def test_user_init_manual(self):
        self.assertIsInstance(User(username="JimHawkins", credits=0, ships=[], loans=[]), User, "User model did not initiate properly")

    def test_user_init_json(self):
        self.assertIsInstance(User(**MOCKS['user']), User, "User model did not initiate properly")

    def test_user_init_user(self):
        user1 = User(**MOCKS['user'])
        user2 = user1
        self.assertIsInstance(user2, User, "User model did not initiate properly")

class TestUserMethods(unittest.TestCase):
    def setUp(self):
        self.user = User(**MOCKS['user'])

    def test_ships_are_ship_objects(self):
        self.assertTrue(all(isinstance(ship, Ship) for ship in self.user.ships), "Not all of the ships are a Ship Object")

    def test_loans_are_loan_objects(self):
        self.assertTrue(all(isinstance(loan, Loan) for loan in self.user.loans), "Not all of the loans are a Loan Object")

    def test_user_property_updates(self):
        self.user.username = "Zac"
        self.assertEqual(self.user.username, "Zac", "Username did not correctly update")

class TestShipInit(unittest.TestCase):
    def test_ship_init_manual(self):
        self.assertIsInstance(Ship(id="213456", manufacturer="Gravader", kind="MK-I", 
                                   type="GR-MK-I", location="OE-PM", x=-28, y=25, 
                                   flightPlanId=None, speed=1, plating=10, 
                                   weapons=5, maxCargo=100, spaceAvailable=99, 
                                   cargo=[]), Ship, "User model did not initiate properly")

    def test_ship_init_json(self):
        self.assertIsInstance(build_ship(MOCKS['ship']), Ship, "User model did not initiate properly")
    
    def test_ship_init_in_transit(self):
        self.assertIsInstance(build_ship(MOCKS['ship_in_transit']), Ship, "User model did not initiate properly")

class TestShipMethods(unittest.TestCase):
    def setUp(self):
        self.ship = build_ship(MOCKS['ship'])

    def test_ship_updates(self):
        self.ship.id = "Zac"
        self.assertEqual(self.ship.id, "Zac", "ID did not correctly update") 

    def test_cargo_are_cargo_objects(self):
        self.assertTrue(all(isinstance(cargo, Cargo) for cargo in self.ship.cargo), "Not all of the cargo are a Cargo Object")

class TestLoanInit(unittest.TestCase):
    def test_loan_init_manual(self):
        self.assertIsInstance(Loan(id="213456", due="2021-04-27T23:12:27.516Z", repaymentAmount=280000, 
                                    type="STARTUP", status="CURRENT"), Loan, "Loan model did not initiate properly")

    def test_loan_init_json(self):
        self.assertIsInstance(Loan(**MOCKS['user_loan']), Loan, "Loan model did not initiate properly")

class TestLoanMethods(unittest.TestCase):
    def setUp(self):
        self.loan = Loan(**MOCKS['user_loan'])

    def test_loan_updates(self):
        self.loan.id = "Zac"
        self.assertEqual(self.loan.id, "Zac", "ID did not correctly update")

class TestLocationInit(unittest.TestCase):
    def test_location_init_manual(self):
        self.assertIsInstance(Location(symbol="OE-PM", type="PLANET", name="Prime", 
                                       x=4, y=12, allowsConstruction=False, structures=[]), 
                              Location, "Location model did not initiate properly")

    def test_location_init_json(self):
        self.assertIsInstance(Location(**MOCKS['location']), Location, "Location model did not initiate properly")

class TestLocationMethods(unittest.TestCase):
    def setUp(self):
        self.location = Location(**MOCKS['location'])

    def test_loan_updates(self):
        self.location.id = "Zac"
        self.assertEqual(self.location.id, "Zac", "ID did not correctly update")

class TestCargoInit(unittest.TestCase):
    def test_cargo_init_manual(self):
        self.assertIsInstance(Cargo(good="FUEL", quantity=50, totalVolume=50), 
                              Cargo, "Cargo model did not initiate properly")

    def test_cargo_init_json(self):
        self.assertIsInstance(Cargo(**MOCKS['cargo']), Cargo, "Cargo model did not initiate properly")

class TestCargoMethods(unittest.TestCase):
    def setUp(self):
        self.cargo = Cargo(**MOCKS['cargo'])

    def test_cargo_updates(self):
        self.cargo.good = "Zac"
        self.assertEqual(self.cargo.good, "Zac", "Good did not correctly update")

class TestSystemInit(unittest.TestCase):
    def test_system_init(self):
        self.assertIsInstance(System(**MOCKS['system']), System, "System model did not initiate properly")

class TestSystemMethods(unittest.TestCase):
    def setUp(self):
        self.sys = System(**MOCKS['system'])

    def test_system_get_location(self):
        self.assertEqual(self.sys.get_location("OE-PM").symbol, "OE-PM", "Did not proprely return the OE-PM location object")

    def test_locs_care_locations_objects(self):
        self.assertTrue(all(isinstance(loc, Location) for loc in self.sys.locations), "Not all of the locations are a Location Object")



      
