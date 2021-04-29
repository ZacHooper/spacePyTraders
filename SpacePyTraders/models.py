class User ():
    """The Ship is awesome!"""
    def __init__(self, data=None, username=None, credits=None, ships=None, loans=None):
        # Regular Init
        self.username = username 
        self.credits = credits
        self.ships = [Ship(ship) for ship in ships['ships']] if isinstance(ships, dict) else ships
        self.loans = [Loan(loan) for loan in loan['loans']] if isinstance(loans, dict) else loans
        # Init with JSON
        if data is not None and isinstance(data, dict):
            if 'user' in data:
                data = data['user']
            self.username = data['username']
            self.credits = data['credits']
            self.ships = [Ship(ship) for ship in data['ships']]
            self.loans = [Loan(loan) for loan in data['loans']]
        # Init with User object
        if data is not None and isinstance(data, User):
            self.username = data.username
            self.credits = data.credits
            self.ships = data.ships
            self.loans = data.loans
        
    def asDict(self):
        return_dict = {'username': self.username, 'credits': self.credits}
        return_dict['ships'] = [ship.asDict() for ship in self.ships]
        return_dict['loans'] = [loan.asDict() for loan in self.loans]
        return return_dict
    
    def __repr__(self):
        return f"Username: {self.username}, Credits: {self.credits}, No of Ships: {len(self.ships)}, No of Loans: {len(self.loans)}"
    
    def __str__(self):
        return f"Username: {self.username}, Credits: {self.credits}, No of Ships: {len(self.ships)}, No of Loans: {len(self.loans)}"


class Ship ():
    """The Ships is Awesome!"""
    def __init__(self, data=None, id=None, manufacturer=None, kind=None, type=None, location=None, x=None, y=None, flightPlanId=None, speed=None, plating=None, weapons=None, maxCargo=None, spaceAvailable=None, cargo=None, **kwargs):
        """The ship class
        """
        # Regular init
        self.id = id
        self.manufacturer = manufacturer
        self.kind = kind
        self.type = type
        self.location = location
        self.x = x
        self.y = y
        self.flightPlanId = flightPlanId
        self.speed = speed
        self.plating = plating
        self.weapons = weapons
        self.maxCargo = maxCargo
        self.spaceAvailable = spaceAvailable
        self.cargo = cargo
        # If data is JSON
        if data is not None and isinstance(data, dict):
            if 'ship' in data:
                data = data['ship']
            if 'location' not in data:
                self.location = "IN TRANSIT"
                self.x = None
                self.y = None
            else:
                self.location = data['location']
                self.x = data['x']
                self.y = data['y']
            if 'flightPlanId' not in data:
                self.flightPlanId = None
            else:
                self.flightPlanId = data['flightPlanId']
            self.id = data['id']
            self.manufacturer = data['manufacturer']
            self.kind = data['class']
            self.type = data['type']
            self.speed = data['speed']
            self.plating = data['plating']
            self.weapons = data['weapons']
            self.maxCargo = data['maxCargo']
            self.spaceAvailable = data['spaceAvailable']
            self.cargo = data['cargo']
        # If data is a Ship object
        if data is not None and isinstance(data, Ship):
            self.id = data.id
            self.manufacturer = data.manufacturer
            self.kind = data.kind
            self.type = data.type
            self.location = data.location
            self.x = data.x
            self.y = data.y
            self.flightPlanId = data.flightPlanId
            self.speed = data.speed
            self.plating = data.plating
            self.weapons = data.weapons
            self.maxCargo = data.maxCargo
            self.spaceAvailable = data.spaceAvailable
            self.cargo = data.cargo

    def asDict(self):
        return self.__dict__
                
    def __repr__(self):
        return f"ID: {self.id}, Manufacturer: {self.manufacturer}, Class: {self.kind} " \
               f"Type: {self.type}, Location: {self.location}, X: {self.x} " \
               f"Y: {self.y}, Flight Plan ID: {self.flightPlanId}, Speed: {self.speed} " \
               f"Plating: {self.plating}, Weapons: {self.weapons}, Max Cargo: {self.maxCargo} " \
               f"Space Available: {self.spaceAvailable}, No of Goods in Cargo: {len(self.cargo)}"
    
    def __str__(self):
        return f"ID: {self.id}, Manufacturer: {self.manufacturer}, Class: {self.kind} " \
               f"Type: {self.type}, Location: {self.location}, X: {self.x} " \
               f"Y: {self.y}, Flight Plan ID: {self.flightPlanId}, Speed: {self.speed} " \
               f"Plating: {self.plating}, Weapons: {self.weapons}, Max Cargo: {self.maxCargo} " \
               f"Space Available: {self.spaceAvailable}, No of Goods in Cargo: {len(self.cargo)}"

class Loan ():
    """The Ship is awesome!"""
    def __init__(self, data=None, id=None, due=None, repaymentAmount=None, status=None, type=None):
        # Regular Init
        self.id = id 
        self.due = due
        self.repaymentAmount = repaymentAmount
        self.status = status
        self.type = type
        # Init with JSON
        if data is not None and isinstance(data, dict):
            if 'user' in data:
                data = data['user']
            self.id = data['id']
            self.due = data['due']
            self.repaymentAmount = data['repaymentAmount']
            self.status = data['status']
            self.type = data['type']
        # Init with User object
        if data is not None and isinstance(data, User):
            self.id = data.id
            self.due = data.due
            self.repaymentAmount = data.repaymentAmount
            self.status = data.status
            self.type = data.type
        
    def asDict(self):
        return {'id': self.id, 'due': self.due, 'repaymentAmount': self.repaymentAmount, 'status': self.status, 'type': self.type}
    
    def __repr__(self):
        return f"id: {self.id}, due: {self.due}, repaymentAmount: {self.repaymentAmount}, status: {self.status}, type: {self.type}"
    
    def __str__(self):
        return f"id: {self.id}, due: {self.due}, repaymentAmount: {self.repaymentAmount}, status: {self.status}, type: {self.type}"

class Location ():
    """The Ship is awesome!"""
    def __init__(self, data=None, symbol=None, type=None, name=None, x=None, y=None, allowsConstruction=None, structures=None):
        # Regular Init
        self.symbol = symbol 
        self.type = type
        self.name = name
        self.x = x
        self.y = y
        self.allowsConstruction = allowsConstruction
        self.structures = structures
        # Init with JSON
        if data is not None and isinstance(data, dict):
            if 'location' in data:
                data = data['location']
            self.symbol = data['symbol']
            self.type = data['type']
            self.name = data['name']
            self.x = data['x']
            self.y = data['y']
            self.allowsConstruction = data['allowsConstruction']
            self.structures = data['structures']
        # Init with User object
        if data is not None and isinstance(data, User):
            self.symbol = data.symbol
            self.type = data.type
            self.name = data.name
            self.x = data.x
            self.y = data.y
            self.allowsConstruction = data.allowsConstruction
            self.structures = data.structures
        
    def asDict(self):
        return {'symbol': self.symbol, 'type': self.type, 'name': self.name, 'x': self.x, 'y': self.y, 'allowsConstruction': self.allowsConstruction, 'structures': self.structures}
    
    def __repr__(self):
        return f"symbol: {self.symbol}, type: {self.type}, name: {self.name}, x: {self.x}, y: {self.y}, allowsConstruction: {self.allowsConstruction}, structures: {self.structures}"
    
    def __str__(self):
        return f"symbol: {self.symbol}, type: {self.type}, name: {self.name}, x: {self.x}, y: {self.y}, allowsConstruction: {self.allowsConstruction}, structures: {self.structures}"