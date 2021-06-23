from dataclasses import dataclass, field
import math

@dataclass
class User ():
    """
    The basic user object. Great way to store and access a user's credits, ships and loans.

    Args:
        username (str): The username of the user
        credits (int): How many credits does the user have
        ships (list): A list of the ships the user owns
        loans (list): A list of the loans the user has

    Returns:
        User: returns a user object
    """
    username: str
    credits: int
    ships: field(default_factory=list)
    loans: field(default_factory=list)

    def __post_init__(self):
        """Handles creating a list of the respective objects if only the dictionary is given. 
        This basically means from the get go a you could call `user.ships[0].id` and get the id of the ship back. 
        Rather than user.ships[0]['id']
        """
        if all(isinstance(ship, dict) for ship in self.ships):
            self.ships = [build_ship(ship) for ship in self.ships]

        if all(isinstance(loan, dict) for loan in self.loans):
            self.loans = [Loan(**loan) for loan in self.loans]


def build_ship(ship_dict):
    """Handles the creation of a ship class. The ship dict contains a 'class' key which needs to be changed for the class creation.
    The ship may also be in transit and that needs to be handled accordingly

    Args:
        ship_dict (dict): the dict version of a ship

    Returns:
        Ship: A ship object
    """
    # Handle if class key is present in dictionary
    if 'class' in ship_dict:
        ship_dict['kind'] = ship_dict.pop('class')

    if 'location' not in ship_dict:
        ship_dict['location'] = "IN_TRANSIT"
    return Ship(**ship_dict)

@dataclass
class Ship ():
    id: str
    manufacturer: str
    kind: str
    type: str
    location: str
    speed: int
    plating: int
    weapons: int
    maxCargo: int
    spaceAvailable: int
    cargo: field(default_factory=list)
    flightPlanId: str = None
    x: int = None
    y: int = None

    def __post_init__(self):
        """Handles creating a list of Cargo object in the ship
        """
        if all(isinstance(c, dict) for c in self.cargo):
            self.cargo = [Cargo(**c) for c in self.cargo]
    
    def calculate_fuel_required(self, dest_dist):
        calc_fuel = lambda d, p: round((d / 4) + p + 2)
        penalties = {
            "MK-I": 2,
            "MK-II": 3,
            "MK-III": 4
        }
        penalty = penalties[self.kind]
        return calc_fuel(dest_dist, penalty)

    def calculate_dist_from_ship(self, loc):
        return round(math.sqrt(math.pow((loc.x - self.x),2) + math.pow((loc.y - self.y),2)))

@dataclass
class Cargo ():
    good: str
    quantity: int
    totalVolume: int

@dataclass
class Loan ():
    id: str 
    due: str
    repaymentAmount: int
    status: str
    type: str
    
@dataclass
class Location ():
    symbol: str
    type: str
    name: str
    x: int
    y: int
    allowsConstruction: bool
    structures: field(default_factory=list)
    messages: list = None

@dataclass
class Marketplace (Location):
    marketplace: list = field(default_factory=list)

    def __post_init__(self):
        """Handles creating a list of Location object in the system
        """
        if all(isinstance(good, dict) for good in self.marketplace):
            self.marketplace = [Good(**good) for good in self.marketplace]

    def get_good(self, symbol):
        """Returns a Good object for the symbol provided

        Args:
            symbol (str): Symbol of the good Eg: "FUEL"

        Returns:
            Good: Good object for the symbol given
        """
        return next(good for good in self.marketplace if good.symbol == symbol)

@dataclass
class Good ():
    symbol: str
    volumePerUnit: int
    pricePerUnit: int
    spread: int
    purchasePricePerUnit: int
    sellPricePerUnit: int
    quantityAvailable: int

@dataclass
class System ():
    locations: field(default_factory=list)

    def __post_init__(self):
        """Handles creating a list of Location object in the system
        """
        if all(isinstance(loc, dict) for loc in self.locations):
            self.locations = [Location(**loc) for loc in self.locations]

    def get_location(self, symbol):
        """Returns a Location object for the symbol provided

        Args:
            symbol (str): Symbol of the location Eg: "OE-PM"

        Returns:
            Location: Location object for the symbol given
        """
        return next(loc for loc in self.locations if loc.symbol == symbol)

