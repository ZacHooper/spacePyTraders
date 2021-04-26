import requests
import logging
import json


URL = "https://api.spacetraders.io/"
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def make_request(method, url, headers, params):
    """Checks which method to use and then makes the actual request to Space Traders API

    Args:
        method (str): The HTTP method to use
        url (str): The URL of the request
        headers (dict): the request headers holding the Auth
        params (dict): parameters of the request

    Returns:
        Request: Returns the request

    Exceptions:
        Exception: Invalid method - must be GET, POST, PUT or DELETE
    """
    # Define the different HTTP methods
    methods = {
        "POST": requests.post(url, headers=headers, params=params),
        "GET": requests.get(url, headers=headers, params=params),
        "PUT": requests.put(url, headers=headers, params=params),
        "DELETE": requests.delete(url, headers=headers, params=params)
    }

    # If an Invalid method provided throw exception
    if method not in methods:
        logging.exception(f'Invalid method provided: {method}')

    return methods[method]   

def get_user_token(username):
    """Trys to create a new user and return their token

    Args:
        username (str): Username to user

    Returns:
        str: Token if user valid else None
    """
    url = f"https://api.spacetraders.io/users/{username}/token"
    try:
        res = make_request("POST", url, None, None)
        if res.ok:
            return res.json()['token']
        else:
            logging.exception(f"Code: {res.json()['error']['code']}, Message: {res.json()['error']['message']}")
            return None
    except Exception as e:
        return e

class Client ():
    def __init__(self, username, token=None):
        """The Client class handles all user interaction with the Space Traders API. 
        The class is initiated with the username and token of the user. 
        If the user does not provide a token the 'create_user' method will attempt to fire and create a user with the username provided. 
        If a user with the name already exists an exception will fire. 

        Args:
            username (str): Username of the user
            token ([type]): The personal auth token for the user. If None will invoke the 'create_user' method
        """
        self.username = username
        self.token = token

    def generic_api_call(self, method, endpoint, params=None, token=None, warning_log=None):
        """Function to make consolidate parameters to make an API call to the Space Traders API. 
        Handles any throttling or error returned by the Space Traders API. 

        Args:
            method (str): The HTTP method to use. GET, POST, PUT or DELETE
            endpoint (str): The API endpoint
            params (dict, optional): Any params required for the endpoint. Defaults to None.
            token (str, optional): The token of the user. Defaults to None.

        Returns:
            Any: depends on the return from the API but likely JSON
        """
        headers = {'Authorization': 'Bearer ' + token}
        # Make the request to the Space Traders API
        try:
            r = make_request(method, URL + endpoint, headers, params) 
            # If an error returned from api 
            if 'error' in r.json():
                error = r.json()
                code = error['error']['code']
                message = error['error']['message']
                logging.warning(f"An error has occurred when hitting: {r.request.method} {r.url} with parameters: {params}. Error: " + str(error))
                
                # If throttling error
                if code == 42901:
                    logging.info("Throttle limit was reached. Pausing to wait for throttle")
                    time.sleep(10)
                    # Recall this method to make the request again. 
                    return generic_api_call(method, endpoint, params, token, warning_log)
                # Retry if server error
                if code == 500 or code == 409:
                    logging.info("Server errors. Pausing before trying again.")
                    time.sleep(10)
                    # Recall this method to make the request again. 
                    return generic_api_call(method, endpoint, params, token, warning_log)
                
                # Unknown handling for error
                logging.warning(warning_log)
                logging.exception(f"Something broke the script. Code: {code} Error Message: {message} ")
                return False
            # If successful return r
            return r
        except Exception as e:
            return e

class FlightPlans(Client):
    # Get all active flights
    def get_active_flight_plans(self, symbol):
        """Get all the currently active flight plans in the system given. This is for all global accounts

        Args:
            symbol (str): Symbol of the system. OE or XV

        Returns:
            dict : dict containing a list of flight plans for each system as the key
        """
        endpoint = f"game/systems/{symbol}/flight-plans"
        warning_log = F"Unable to get flight plans for system: {symbol}."
        logging.info(f"Getting the flight plans in the {symbol} system")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get Existing Flight
    def get_flight_plan(self, flightPlanId):
        """Get the details of a currently active flight plan

        Args:
            flightPlanId (str): ID of the flight plan

        Returns:
            dict : dict containing the details of the flight plan
        """
        endpoint = f"users/{self.username}/flight-plans/{flightPlanId}"
        warning_log = F"Unable to get flight plan: {flightPlanId}."
        logging.info(f"Getting flight plan: {flightPlanId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Create Flight Plan
    def new_flight_plan(self, shipId, destination):
        """Submit a new flight plan for a ship

        Args:
            shipId (str): ID of the ship to fly
            destination (str): Symbol of the locatino to fly the ship to
        """
        endpoint = f"users/{self.username}/flight-plans"
        params = {"shipId": shipId, "destination": destination}
        warning_log = F"Unable to create Flight Plan for ship: {shipId}."
        logging.info(f"Creating flight plan for ship: {shipId} to destination: {destination}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Game (Client):
    # Get game status
    def get_game_status(self):
        """Check to see if game is up
        """
        endpoint = f"game/status"
        warning_log = F"Game is currently down"
        logging.info(f"Checking if game is up")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Loans (Client):
    # Get available loans
    def get_loans_available(self):
        """Gets the list of loans available

        Returns:
            dict: dict containing a list of loans
        """
        endpoint = f"game/loans"
        warning_log = F"Unable to retrieve the loans available"
        logging.info(f"Retrieving the loans currently available")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get user's loans
    def get_user_loans(self):
        """Gets the list of loans available

        Returns:
            dict: dict containing a list of loans
        """
        endpoint = f"users/{self.username}/loans"
        warning_log = F"Unable to retrieve the loans of the user"
        logging.info(f"Retrieving the loans of the user: {self.username}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Pay off loan
    def pay_off_loan(self, loanId):
        """Pays of the loan with ID provided

        Args:
            loanId (str): ID of the loan to pay off

        Returns:
            dict: Success or fail message
        """
        endpoint = f"users/{self.username}/loans/{loanId}"
        warning_log = F"Unable to pay off loan: {loanId}"
        logging.info(f"Paying off loan")
        res = self.generic_api_call("PUT", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Request new loan
    def request_loan(self, type):
        """Request a new loan

        Args:
            type (str): The type of loan - e.g. STARTUP

        Returns:
            dict: The loan taken
        """
        endpoint = f"users/{self.username}/loans"
        warning_log = F"Unable to take loan of type: {type}"
        logging.info(f"Requesting {type} loan")
        params = {"type": type}
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Locations (Client):
    # Get Location
    def get_location(self, symbol):
        """Get info on a location with the provided Symbol

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing info about a location
        """
        endpoint = f"game/locations/{symbol}"
        warning_log = F"Unable to get info for the location: {symbol}"
        logging.info(f"Getting location info for {symbol}")
        res = self.generic_api_call("GET", endpoint,token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get Ships at Location
    def get_ships_at_location(self, symbol):
        """Get the ships docked at a location

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing a JSON list of the ships docked at the location. 
        """
        endpoint = f"game/locations/{symbol}/ships"
        warning_log = F"Unable to get ships docked at the location: {symbol}"
        logging.info(f"Getting the ships docked at: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False    

    # Get System's Locations
    def get_system_locations(self, symbol):
        """Get locations in the defined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict containing a JSON list of the locations in the system
        """
        endpoint = f"game/systems/{symbol}/locations"
        warning_log = F"Unable to get the locations in the system: {symbol}"
        logging.info(f"Getting the locations in system: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False  

class Marketplace (Client):
    # Get Location's marketplace
    def get_marketplace(self, symbol):
        """Get the marketplace for the location provided

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing details of the location and a JSON list of the items available in the marketplace
        """
        endpoint = f"game/locations/{symbol}/marketplace"
        warning_log = F"Unable to get the marketplace for the location: {symbol}"
        logging.info(f"Getting the marketplace for location: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False  

class PurchaseOrders (Client):
    def new_purchase_order(self, shipId, good, quantity):
        """Makes a purchase order to the location the ship is currently located at. 

        Args:
            shipId (str): ID of the ship to load the goods onto
            good (str): Symbol of the good to purchase
            quantity (int): How many units of the good to purchase
        """
        endpoint = f"users/{self.username}/purchase-orders"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to make purchase order for ship: {shipId}, good: {good} & quantity: {quantity}"
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class SellOrders (Client):
    # Sell Orders
    def new_sell_order(self, shipId, good, quantity):
        """Makes a sell order to the location the ship is currently located at. 

        Args:
            shipId (str): ID of the ship to offload the goods from
            good (str): Symbol of the good to sell
            quantity (int): How many units of the good to sell
        """
        endpoint = f"users/{self.username}/sell-orders"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to make sell order for ship: {shipId}, good: {good} & quantity: {quantity}"
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Ships (Client):
    def buy_ship(self, location, type):
        """Buys a ship of the type provided and at the location provided. 
        Certain ships can only be bought from specific locations. Use get_available_ships to see full list.

        Args:
            location (str): symbol of the location the ship to buy is
            type (str): type of ship you want to buy e.g. GR-MK-III
        """
        endpoint = f"users/{self.username}/ships"
        params = {"location": location, "type": type}
        warning_log = F"Unable to buy ship type: {type}, at location: {location}."
        logging.info(f"Buying ship of type: {type} at location: {location}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get available ships
    def get_available_ships(self, type=None):
        """Get the avialable ships to purchase across all systems

        Args:
            type (str, optional): Filter the list of ships to the class level. eg 'MK-II' (Note: those are capital i's). Defaults to None.

        Returns:
            dict: A dict containing a JSON list of ships that are available. 

        API LINK: https://api.spacetraders.io/#api-ships-ships
        """
        endpoint = f"game/ships"
        params = {"class": type}
        warning_log = F"Unable to get available ships. Class Filter: {type}"
        logging.info(f"Getting available ships to purchase. Filter: {type}")
        res = self.generic_api_call("GET", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get Ship
    def get_ship(self, shipId):
        """Get info on the ship

        Args:
            shipId (str): The shipId of the ship you want to get info on

        Returns:
            dict: A dict containing the info about the ship

        API LINK: https://api.spacetraders.io/#api-ships-GetShip
        """
        endpoint = f"users/{self.username}/ships/{shipId}"
        warning_log = F"Unable to get info fo ship: {shipId}"
        logging.info(f"Getting info on ship: {shipId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get Users ships
    def get_user_ships(self):
        """Get a list of all the ships you own

        Returns:
            dict: A JSON list of the ships you own. Each item is a return from the get_ship_info endpoint.

        API Link: https://api.spacetraders.io/#api-ships-GetShips
        """
        endpoint = f"users/{self.username}/ships"
        warning_log = F"Unable to get list of owned ships."
        logging.info(f"Getting a list of owned ships")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Jettison Cargo
    def jettinson_cargo(self, shipId, good, quantity):
        """Jettison (delete) some cargo from a ship

        Args:
            shipId (str): The shipId of the ship you want to jettison cargo from
            good (str): The symbol of the good you want to jettison. Eg. FUEL
            quantity (int): How many units of the good you want to jettison

        Returns:
            dict: If successful a dict is returned with the remaining quantitiy of the good on the ship

        API Link: https://api.spacetraders.io/#api-ships-JettisonCargo
        """
        endpoint = f"users/{self.username}/ships/{shipId}/jettison"
        warning_log = F"Unable to jettison cargo from ship. Params - shipId: {shipId}, good: {good}, quantity: {quantity}"
        logging.info(f"Jettison the following cargo from ship: {shipId}, good: {good}, quantity: {quantity}")
        params = {"good": good, "quantity": quantity}
        res = self.generic_api_call("PUT", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Scrap Ship
    def scrap_ship(self, shipId):
        """Scraps the shipId for a small amount of credits. 
        Ships need to be scraped at a location with a Shipyard.
        Known Shipyards:
        - OE-PM-TR

        Args:
            shipId (str): ID of the ship to scrap

        Returns:
            bool: True if the ship was scrapped

        Raises:
            Exception: If something went wrong during the scrapping process
        """
        endpoint = f"users/{self.username}/ships/{shipId}/"
        warning_log = f"Failed to scrap ship ({shipId})."
        logging.info(f"Scrapping ship: {shipId}")
        res = self.generic_api_call("DELETE", endpoint, token=self.token, warning_log=warning_log)
        return res

    # Transfer Cargo
    def transfer_cargo(self, fromShipId, toShipId, good, quantity):
        """Move cargo from own ship to another that are in the same location

        Args:
            fromShipId (str): The shipId of the ship you want to transfer the cargo FROM
            toShipId (str): The shipId of the ship you want to transfer the cargo TO
            good (str): The symbol of the good you want to transfer. Eg. FUEL
            quantity (int): How many units of the good you want to transfer

        Returns:
            dict: A dict is returned with two keys "fromShip" & "toShip" each with the updated ship info for the respective ships

        API Link: https://api.spacetraders.io/#api-ships-TransferCargo
        """
        endpoint = f"users/{self.username}/ships/{fromShipId}/transfer"
        warning_log = F"Unable to transfer {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}"
        logging.info(f"Transferring {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}")
        params = {"toShipId": toShipId, "good": good, "quantity": quantity}
        res = self.generic_api_call("PUT", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Structures (Client):
    # Create a new structure
    def create_new_structure(self, location, type):
        """Create a new structure on the location provided. Note that only certain structures can be built at specific locations

        Args:
            location (str): symbol of the location to build the structure
            type (str): type of structure you want to build
        """
        endpoint = f"users/{self.username}/structures"
        params = {"location": location, "type": type}
        warning_log = F"Unable to create structure type: {type}, at location: {location}."
        logging.info(f"Creating structure of type: {type} at location: {location}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Deposit Goods
    def deposit_goods(self, structureId, shipId, good, quantity):
        """Deposit goods from a ship to a structure. The ship must be at the location the structure has been built.

        Args:
            structureId (str): ID of the structure to deposit the goods into
            shipId (str): ID of the ship to take the goods from
            good (str): symbol of the good to deposite. Eg: FUEL
            quantity (str): How many units of the good to deposit
        
        Returns:
            dict : dict containing the updated info of the ship and structure
        """
        endpoint = f"users/{self.username}/structures/{structureId}/deposit"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to deposit {quantity} units of {good} from ship: {shipId} into structure: {structureId}"
        logging.info(f"Depositing {quantity} units of {good} from ship: {shipId} into structure: {structureId}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get your structure info
    def get_structure(self, structureId):
        """Get the info about a structure

        Args:
            structureId (str): ID of the structure to deposit the goods into

        Returns:
            dict : dict containing the info of the strucutre
        """
        endpoint = f"users/{self.username}/structures/{structureId}"
        warning_log = F"Unable to get the info for structure: {structureId}"
        logging.info(f"Getting info about structure: {structureId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Get your strucutres
    def get_users_structures(self):
        """Get the info about a structure

        Returns:
            dict : dict containings a JSON list of the structures the user owns
        """
        endpoint = f"users/{self.username}/structures"
        warning_log = F"Unable to get the info about your structures"
        logging.info(f"Getting info about the user's structures")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False

    # Transfer goods
    def transfer_goods(self, structureId, shipId, good, quantity):
        """Transfer goods from a structure to a ship. The ship must be docked at the location the structure has been built.

        Args:
            structureId (str): ID of the structure to deposit the goods into
            shipId (str): ID of the ship to take the goods from
            good (str): symbol of the good to deposite. Eg: FUEL
            quantity (str): How many units of the good to deposit
        
        Returns:
            dict : dict containing the updated info of the ship and structure
        """
        endpoint = f"users/{self.username}/structures/{structureId}/transfer"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to transfer {quantity} units of {good} from structure: {structureId} into ship: {shipId}"
        logging.info(f"Transferring {quantity} units of {good} from structure: {structureId} into ship: {shipId}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res.json() if res else False

class Systems (Client):
    # Get system info
    def get_systems(self):
        """Get info about the systems and their locations.

        Returns:
            dict: dict containing a JSON list of the different systems
        """
        # Get user
        endpoint = f"game/systems"
        warning_log = F"Unable to get systems"
        logging.info(f"Getting systems")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False    

class Users (Client):

    def get_your_info(self):
        """Get your user info

        Returns:
            dict: dict containing your user data
        """
        # Get user
        endpoint = f"users/{self.username}"
        warning_log = F"Unable to get {self.username} user info"
        logging.info(f"Getting user info for {self.username}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res.json() if res else False    

class Api ():
    def __init__(self, username, token=None):
        self.username = username
        self.token = token if token is not None else get_user_token(username)
        self.flightplans = FlightPlans(username, token)
        self.game = Game(username, token)
        self.loans = Loans(username, token)
        self.locations = Locations(username, token)
        self.marketplace = Marketplace(username, token)
        self.purchaseOrders = PurchaseOrders(username, token)
        self.sellOrders = SellOrders(username, token)
        self.ships = Ships(username, token)
        self.structures = Structures(username, token)
        self.systems = Systems(username, token)
        self.users = Users(username, token)


if __name__ == "__main__":
    pass
    # username = "JimHawkins"
    # token = "0930cc36-7dc7-4cb1-8823-d8e72594d91e"

    # api = Api(username, token)

    # print(api.loans.get_loans_available())
