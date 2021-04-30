from dataclasses import dataclass, field

@dataclass
class User ():
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