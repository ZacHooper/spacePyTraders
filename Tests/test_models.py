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
        self.assertIsInstance(User(MOCKS['user']), User, "User model did not initiate properly")

    def test_user_init_user(self):
        self.assertIsInstance(User(User(MOCKS['user'])), User, "User model did not initiate properly")

class TestUserMethods(unittest.TestCase):
    def setUp(self):
        self.user = User(data=MOCKS['user'])

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
        self.assertIsInstance(Ship(MOCKS['ship']), Ship, "User model did not initiate properly")

    def test_ship_init_ship(self):
        self.assertIsInstance(Ship(Ship(MOCKS['ship'])), Ship, "User model did not initiate properly")

class TestShipMethods(unittest.TestCase):
    def setUp(self):
        self.ship = Ship(MOCKS['ship'])

    def test_ship_updates(self):
        self.ship.id = "Zac"
        self.assertEqual(self.ship.id, "Zac", "ID did not correctly update") 

class TestLoanInit(unittest.TestCase):
    def test_loan_init_manual(self):
        self.assertIsInstance(Loan(id="213456", due="2021-04-27T23:12:27.516Z", repaymentAmount=280000, 
                                    type="STARTUP"), Loan, "Loan model did not initiate properly")

    def test_loan_init_json(self):
        self.assertIsInstance(Loan(MOCKS['user_loan']), Loan, "Loan model did not initiate properly")

    def test_loan_init_loan(self):
        self.assertIsInstance(Loan(Loan(MOCKS['user_loan'])), Loan, "Loan model did not initiate properly")

class TestLoanMethods(unittest.TestCase):
    def setUp(self):
        self.loan = Loan(MOCKS['user_loan'])

    def test_loan_updates(self):
        self.loan.id = "Zac"
        self.assertEqual(self.loan.id, "Zac", "ID did not correctly update")

class TestLocationInit(unittest.TestCase):
    def test_location_init_manual(self):
        self.assertIsInstance(Location(symbol="OE-PM", type="PLANET", name="Prime", x=4, y=12), 
                              Location, "Location model did not initiate properly")

    def test_location_init_json(self):
        self.assertIsInstance(Location(MOCKS['location']), Location, "Location model did not initiate properly")

    def test_location_init_location(self):
        self.assertIsInstance(Location(Location(MOCKS['location'])), Location, "Location model did not initiate properly")

class TestLocationMethods(unittest.TestCase):
    def setUp(self):
        self.location = Location(MOCKS['location'])

    def test_loan_updates(self):
        self.location.id = "Zac"
        self.assertEqual(self.location.id, "Zac", "ID did not correctly update")


      
