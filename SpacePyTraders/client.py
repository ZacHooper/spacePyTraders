from asyncio.format_helpers import extract_stack
import requests
import logging
import time
from dataclasses import dataclass, field
import warnings
from ratelimit import limits, sleep_and_retry



URL = "https://api.spacetraders.io/"
V2_URL = "https://v2-0-0.alpha.spacetraders.io/"
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(thread)d - %(message)s', level=logging.INFO)

# Custom Exceptions
# ------------------------------------------
@dataclass
class ThrottleException(Exception):
    data: field(default_factory=dict)
    message: str = "Throttle limit was reached. Pausing to wait for throttle"

@dataclass
class ServerException(Exception):
    data: field(default_factory=dict)
    message: str = "Server Error. Pausing before trying again"

@dataclass
class TooManyTriesException(Exception):
    message: str = "Has failed too many times to make API call. "

@sleep_and_retry
@limits(calls=2, period=1.2)
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
    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, params=params)
    elif method == "PUT": 
        return requests.put(url, headers=headers, params=params)
    elif method == "DELETE":
        return requests.delete(url, headers=headers, params=params)

    # If an Invalid method provided throw exception
    if method not in ["GET", "POST", "PUT", "DELETE"]:
        logging.exception(f'Invalid method provided: {method}')

@dataclass
class Client ():
    def __init__(self, username=None, token=None, v2=False):
        """The Client class handles all user interaction with the Space Traders API. 
        The class is initiated with the username and token of the user. 
        If the user does not provide a token the 'create_user' method will attempt to fire and create a user with the username provided. 
        If a user with the name already exists an exception will fire. 

        Args:
            username (str): Username of the user
            token (str): The personal auth token for the user. If None will invoke the 'create_user' method
            v2 (bool): Determine if you want to use the new V2 API or V1
        """
        self.username = username
        self.token = token
        self.url = V2_URL if v2 else URL

    def generic_api_call(self, method, endpoint, params=None, token=None, warning_log=None, raw_res=False, throttle_time=10):
        """Function to make consolidate parameters to make an API call to the Space Traders API. 
        Handles any throttling or error returned by the Space Traders API. 

        Args:
            method (str): The HTTP method to use. GET, POST, PUT or DELETE
            endpoint (str): The API endpoint
            params (dict, optional): Any params required for the endpoint. Defaults to None.
            token (str, optional): The token of the user. Defaults to None.
            raw_res (bool, default = False): Returns the request response's JSON by default. Can be set to True to return the request response.
            throttle_time (int, default = 10): Sets how long the wait time before attempting call again. Default is 10 seconds

        Returns:
            Any: depends on the return from the API but likely JSON
        """
        headers = {'Authorization': 'Bearer ' + token}
        # Make the request to the Space Traders API
        for i in range(10):
            try:
                r = make_request(method, self.url + endpoint, headers, params) 
                # If an error returned from api 
                if 'error' in r.json():
                    error = r.json()
                    code = error['error']['code']
                    message = error['error']['message']
                    logging.warning(f"An error has occurred when hitting: {r.request.method} {r.url} with parameters: {params}. Error: " + str(error))
                    
                    # If throttling error
                    if code == 42901:
                        raise ThrottleException(error)

                    # Retry if server error
                    if code == 500 or code == 409:
                        raise ServerException(error)
                    
                    # Unknown handling for error
                    logging.warning(warning_log)
                    logging.exception(f"Something broke the script. Code: {code} Error Message: {message} ")
                    return False
                # If successful return r
                if raw_res:
                    return r
                else:
                    return r.json()

            except ThrottleException as te:
                    logging.info(te.message)
                    time.sleep(throttle_time)
                    continue

            except ServerException as se:
                    logging.info(se.message)
                    time.sleep(throttle_time)
                    continue
            
            except Exception as e:
                return e
        
        # If failed to make call after 10 tries fail it
        raise(TooManyTriesException)

class Account (Client):
    # Used to get info about user
    def info(self, raw_res=False, throttle_time=10):
        """Get's the user's info

        Args:
            raw_res (bool, optional): Get the actual response from requests. Defaults to False.
            throttle_time (int, optional): change the throttle time to wait. Defaults to 10.

        Returns:
            dict: Returns a dictionary containing the user's details
        """
        endpoint = f"my/account"
        warning_log = F"Unable to get {self.username} user info"
        logging.info(f"Getting user info for {self.username}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

class FlightPlans(Client):
    # Get all active flights
    def get_active_flight_plans(self, symbol, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED
        This method has been moved to the systems class. Please now use `systems.get_active_flight_plans()`
        to get the active flight plans in the system given.
        
        Get all the currently active flight plans in the system given. This is for all global accounts

        Args:
            symbol (str): Symbol of the system. OE or XV

        Returns:
            dict : dict containing a list of flight plans for each system as the key
        """
        warnings.warn("get_active_flight_plans has now been moved to the Systems class. Place now use `systems.get_active_flight_plans()`. This method will remain until the next update.", DeprecationWarning)
        endpoint = f"systems/{symbol}/flight-plans"
        warning_log = F"Unable to get flight plans for system: {symbol}."
        logging.info(f"Getting the flight plans in the {symbol} system")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get Existing Flight
    def get_flight_plan(self, flightPlanId, raw_res=False, throttle_time=10):
        """Get the details of a currently active flight plan

        Args:
            flightPlanId (str): ID of the flight plan

        Returns:
            dict : dict containing the details of the flight plan
        """
        endpoint = f"my/flight-plans/{flightPlanId}"
        warning_log = F"Unable to get flight plan: {flightPlanId}."
        logging.info(f"Getting flight plan: {flightPlanId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Create Flight Plan
    def new_flight_plan(self, shipId, destination, raw_res=False, throttle_time=10):
        """Submit a new flight plan for a ship

        Args:
            shipId (str): ID of the ship to fly
            destination (str): Symbol of the locatino to fly the ship to
        """
        endpoint = f"my/flight-plans"
        params = {"shipId": shipId, "destination": destination}
        warning_log = F"Unable to create Flight Plan for ship: {shipId}."
        logging.debug(f"Creating flight plan for ship: {shipId} to destination: {destination}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

class Game (Client):
    # Get game status
    def get_game_status(self, raw_res=False, throttle_time=10):
        """Check to see if game is up
        """
        endpoint = f"game/status"
        warning_log = "Game is currently down"
        logging.info(f"Checking if game is up")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

class Leaderboard (Client):
    def get_player_net_worths(self, raw_res=False, throttle_time=10):
        """Returns a ranking list of players net-worth. It also returns the players net-worth

        Args:
            raw_res (bool, optional): Return the actual request response. Defaults to False.
            throttle_time (int, optional): Overwrite how long to wait when throttling. Defaults to 10.

        Returns:
            dict: A dictionary containing a list of the top 10 wealthiest players and the user's net-worth
        """
        endpoint = f"game/leaderboard/net-worth"
        warning_log = "Unable to retrieve the net worth leaderboard"
        logging.debug(f"Retreiving the net worth leaderboard")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

class Loans (Client):
    # Get available loans
    def get_loans_available(self, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED
        This method has now been moved to the types class. Please now use `types.get_loans_available()`.
        
        Gets the list of loans available

        Returns:
            dict: dict containing a list of loans
        """
        warnings.warn("get_loans_available has now been moved to the Types class. Place now use `types.loans()`. This method will remain until the next update.")
        endpoint = f"types/loans"
        warning_log = F"Unable to retrieve the loans available"
        logging.info(f"Retrieving the loans currently available")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get user's loans
    def get_user_loans(self, raw_res=False, throttle_time=10):
        """Gets the list of loans available

        Returns:
            dict: dict containing a list of loans
        """
        endpoint = f"my/loans"
        warning_log = F"Unable to retrieve the loans of the user"
        logging.info(f"Retrieving the loans of the user: {self.username}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Pay off loan
    def pay_off_loan(self, loanId, raw_res=False, throttle_time=10):
        """Pays of the loan with ID provided

        Args:
            loanId (str): ID of the loan to pay off

        Returns:
            dict: Success or fail message
        """
        endpoint = f"my/loans/{loanId}"
        warning_log = F"Unable to pay off loan: {loanId}"
        logging.info(f"Paying off loan")
        res = self.generic_api_call("PUT", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Request new loan
    def request_loan(self, type, raw_res=False, throttle_time=10):
        """Request a new loan

        Args:
            type (str): The type of loan - e.g. STARTUP

        Returns:
            dict: The loan taken
        """
        endpoint = f"my/loans"
        warning_log = F"Unable to take loan of type: {type}"
        logging.info(f"Requesting {type} loan")
        params = {"type": type}
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

class Locations (Client):
    # Get Location
    def get_location(self, symbol, raw_res=False, throttle_time=10):
        """Get info on a location with the provided Symbol

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing info about a location
        """
        endpoint = f"locations/{symbol}"
        warning_log = F"Unable to get info for the location: {symbol}"
        logging.info(f"Getting location info for {symbol}")
        res = self.generic_api_call("GET", endpoint,token=self.token, warning_log=warning_log)
        return res if res else False

    # Get Ships at Location
    def get_ships_at_location(self, symbol, raw_res=False, throttle_time=10):
        """Get the ships docked at a location

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing a JSON list of the ships docked at the location. 
        """
        endpoint = f"locations/{symbol}/ships"
        warning_log = F"Unable to get ships docked at the location: {symbol}"
        logging.info(f"Getting the ships docked at: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False    

    # Get System's Locations
    def get_system_locations(self, symbol, type=None, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED
        This method has now moved to the systems class. Please now use `systems.get_system_locations()`.

        Get locations in the defined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict containing a JSON list of the locations in the system
        """
        warnings.warn("get_system_locations has now moved to the Systems class. \n\nPlease now use `systems.get_system_locations()`. \n\nThis method will remain until the next update.")
        endpoint = f"systems/{symbol}/locations"
        warning_log = F"Unable to get the locations in the system: {symbol}"
        logging.info(f"Getting the locations in system: {symbol}")
        params = {"type": type} if type is not None else None
        res = self.generic_api_call("GET", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False  
    
    def get_marketplace(self, symbol, raw_res=False, throttle_time=10):
        """Get the marketplace for the location provided

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing details of the location and a JSON list of the items available in the marketplace
        """
        endpoint = f"locations/{symbol}/marketplace"
        warning_log = F"Unable to get the marketplace for the location: {symbol}"
        logging.info(f"Getting the marketplace for location: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False  

class Marketplace (Client):
    """THIS CLASS IS BEING DEPRECATED
    All containing methods have been removed or are being deprecated."""
    # Get Location's marketplace
    def get_marketplace(self, symbol, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED
        This method has moved to the Location class. Please now use `locations.get_marketplace()`.

        Get the marketplace for the location provided

        Args:
            symbol (str): The symbol for the location eg: OE-PM

        Returns:
            dict: A dict containing details of the location and a JSON list of the items available in the marketplace
        """
        warnings.warn("get_marketplace has now moved to the Locations class. \n\nPlease now use `location.get_marketplace()`. \n\nThis method will remain until the next update.")
        endpoint = f"locations/{symbol}/marketplace"
        warning_log = F"Unable to get the marketplace for the location: {symbol}"
        logging.info(f"Getting the marketplace for location: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False  

class PurchaseOrders (Client):
    def new_purchase_order(self, shipId, good, quantity, raw_res=False, throttle_time=10):
        """Makes a purchase order to the location the ship is currently located at. 

        Args:
            shipId (str): ID of the ship to load the goods onto
            good (str): Symbol of the good to purchase
            quantity (int): How many units of the good to purchase
            raw_res (bool, default = False): Returns the request response's JSON by default. Can be set to True to return the request response.
            throttle_time (int, default = 10): Sets how long the wait time before attempting call again. Default is 10 seconds
        
        Returns:
            dict: A dict containing the user's remaining credits, the ships updated cargo and the order just made.
        """
        endpoint = f"my/purchase-orders"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to make purchase order for ship: {shipId}, good: {good} & quantity: {quantity}"
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

class SellOrders (Client):
    # Sell Orders
    def new_sell_order(self, shipId, good, quantity, raw_res=False, throttle_time=10):
        """Makes a sell order to the location the ship is currently located at. 

        Args:
            shipId (str): ID of the ship to offload the goods from
            good (str): Symbol of the good to sell
            quantity (int): How many units of the good to sell
        """
        endpoint = f"my/sell-orders"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to make sell order for ship: {shipId}, good: {good} & quantity: {quantity}"
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

class Ships (Client):
    def buy_ship(self, location, type, raw_res=False, throttle_time=10):
        """Buys a ship of the type provided and at the location provided. 
        Certain ships can only be bought from specific locations. Use get_available_ships to see full list.

        Args:
            location (str): symbol of the location the ship to buy is
            type (str): type of ship you want to buy e.g. GR-MK-III
        """
        endpoint = f"my/ships"
        params = {"location": location, "type": type}
        warning_log = F"Unable to buy ship type: {type}, at location: {location}."
        logging.debug(f"Buying ship of type: {type} at location: {location}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get available ships
    def get_available_ships(self, type=None, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED
        This method has now moved to the types class. Please now use `types.ships()`.

        Get the avialable ships to purchase across all systems

        Args:
            type (str, optional): Filter the list of ships to the class level. eg 'MK-II' (Note: those are capital i's). Defaults to None.

        Returns:
            dict: A dict containing a JSON list of ships that are available. 

        API LINK: https://api.spacetraders.io/#api-ships-ships
        """
        warnings.warn("""get_available_ships is being deprecated and is moving to the Types class. \n
                        To get your info please now use Api.types.ships()\n
                        No longer returns the location of the ships - see system.get_available_ships() for ships available in the system""", DeprecationWarning)
        endpoint = f"types/ships"
        params = {"class": type}
        warning_log = F"Unable to get available ships. Class Filter: {type}"
        logging.info(f"Getting available ships to purchase. Filter: {type}")
        res = self.generic_api_call("GET", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get Ship
    def get_ship(self, shipId, raw_res=False, throttle_time=10):
        """Get info on the ship

        Args:
            shipId (str): The shipId of the ship you want to get info on

        Returns:
            dict: A dict containing the info about the ship

        Example response:
        {
            "data": {
                "symbol": "55B261-1",
                "crew": null,
                "officers": null,
                "fuel": 100,
                "frame": "FRAME_DRONE",
                "reactor": "REACTOR_SOLAR_I",
                "engine": "ENGINE_SOLAR_PROPULSION",
                "modules": [
                    "MODULE_CARGO_HOLD"
                ],
                "mounts": [
                    "MOUNT_MINING_LASER_I"
                ],
                "registration": {
                    "factionSymbol": "COMMERCE_REPUBLIC",
                    "agentSymbol": "55B261",
                    "fee": 100,
                    "role": "EXCAVATOR"
                },
                "integrity": {
                    "frame": 1,
                    "reactor": 1,
                    "engine": 1
                },
                "status": "DOCKED",
                "location": "X1-OE-PM",
                "cargo": []
            }
        }

        API LINK: https://api.spacetraders.io/#api-ships-GetShip
        V2 API: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MzE-view-ship
        """
        endpoint = f"my/ships/{shipId}"
        warning_log = F"Unable to get info fo ship: {shipId}"
        logging.info(f"Getting info on ship: {shipId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get Users ships
    def get_user_ships(self, raw_res=False, throttle_time=10):
        """Get a list of all the ships you own

        Returns:
            dict: A JSON list of the ships you own. Each item is a return from the get_ship_info endpoint.

        API Link: https://api.spacetraders.io/#api-ships-GetShips
        V2 API: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MzI-list-ships
        """
        endpoint = f"my/ships"
        warning_log = F"Unable to get list of owned ships."
        logging.info(f"Getting a list of owned ships")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Jettison Cargo
    def jettinson_cargo(self, shipId, good, quantity, raw_res=False, throttle_time=10):
        """Jettison (delete) some cargo from a ship

        Response Example:

        {
            "data": {
                "tradeSymbol": "ALUMINUM",
                "units": 95
            }
        }

        Args:
            shipId (str): The shipId of the ship you want to jettison cargo from
            good (str): The symbol of the good you want to jettison. Eg. FUEL
            quantity (int): How many units of the good you want to jettison

        Returns:
            dict: If successful a dict is returned with the remaining quantitiy of the good on the ship

        API Link: https://api.spacetraders.io/#api-ships-JettisonCargo
        V2 Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjQ-jettison-cargo
        """
        endpoint = f"my/ships/{shipId}/jettison"
        warning_log = F"Unable to jettison cargo from ship. Params - shipId: {shipId}, good: {good}, quantity: {quantity}"
        logging.info(f"Jettison the following cargo from ship: {shipId}, good: {good}, quantity: {quantity}")
        params = {"good": good, "quantity": quantity}
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    # Scrap Ship
    def scrap_ship(self, shipId, raw_res=False, throttle_time=10):
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
        endpoint = f"my/ships/{shipId}/"
        warning_log = f"Failed to scrap ship ({shipId})."
        logging.info(f"Scrapping ship: {shipId}")
        res = self.generic_api_call("DELETE", endpoint, token=self.token, warning_log=warning_log)
        return res

    # Transfer Cargo
    def transfer_cargo(self, fromShipId, toShipId, good, quantity, raw_res=False, throttle_time=10):
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
        endpoint = f"my/ships/{fromShipId}/transfer"
        warning_log = F"Unable to transfer {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}"
        logging.info(f"Transferring {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}")
        params = {"toShipId": toShipId, "good": good, "quantity": quantity}
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    def scan(self, shipSymbol, mode, raw_res=False, throttle_time=10):
        """Execute a ship scan to view approach / departing ships, system information or details about a waypoint. 
           Send a scan mode to select the type of scan performed by your ship.

        Args:
            shipSymbol (str): The ship's symbol (id)
            mode (str): What type of scan do you want to undertake. APPROACHING_SHIPS, DEPARTING_SHIPS, SYSTEM, WAYPOINT
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: Return JSON repsonse 

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjk-scan
        """
        endpoint = f"my/ships/{shipSymbol}/scan"
        params = {"mode": mode}
        warning_log = f"Unable to perform scan of mode: {mode}"
        logging.info(f"Unable to perform scan of mode: {mode}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    def scan_cooldown(self, shipSymbol, raw_res=False, throttle_time=10):
        """See how long your ship must wait before it can scan again.

        Args:
            shipSymbol (str): The ship's symbol (id)
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: Return JSON repsonse 

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyMzgxMTc-scan-cooldown
        """
        endpoint = f"my/ships/{shipSymbol}/scan"
        warning_log = f"Unable to obtain scan cooldown for ship: {shipSymbol}"
        logging.info(f"Unable to obtain scan cooldown for ship: {shipSymbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

class Structures (Client):
    # Create a new structure
    def create_new_structure(self, location, type, raw_res=False, throttle_time=10):
        """Create a new structure on the location provided. Note that only certain structures can be built at specific locations

        Args:
            location (str): symbol of the location to build the structure
            type (str): type of structure you want to build
        """
        endpoint = f"my/structures"
        params = {"location": location, "type": type}
        warning_log = F"Unable to create structure type: {type}, at location: {location}."
        logging.info(f"Creating structure of type: {type} at location: {location}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

    # Deposit Goods
    def deposit_goods(self, structureId, shipId, good, quantity, user_owned=True, raw_res=False, throttle_time=10):
        """Deposit goods from a ship to a structure. The ship must be at the location the structure has been built.

        Args:
            structureId (str): ID of the structure to deposit the goods into
            shipId (str): ID of the ship to take the goods from
            good (str): symbol of the good to deposite. Eg: FUEL
            quantity (str): How many units of the good to deposit
            user_owned (bool): Determines which endpoint to use: deposit to user structure or any structure
        
        Returns:
            dict : dict containing the updated info of the ship and structure

        Possible Endpoints:
            - https://api.spacetraders.io/#api-structures-DepositMyGoods
            - https://api.spacetraders.io/#api-structures-DepositStructure

        """
        endpoint = f"my/structures/{structureId}/deposit" if user_owned else f"structures/{structureId}/deposit"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to deposit {quantity} units of {good} from ship: {shipId} into structure: {structureId}"
        logging.info(f"Depositing {quantity} units of {good} from ship: {shipId} into structure: {structureId}")
        res = self.generic_api_call("POST", endpoint, params=params, 
                                    token=self.token, warning_log=warning_log, 
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    # Get your structure info
    def get_structure(self, structureId, user_owned=True, raw_res=False, throttle_time=10):
        """Get the info about a structure. 

        the `user_owned` argument will determine whether the `my` endpoint is used or note.
        Possible Endpoints:
            - https://api.spacetraders.io/#api-structures-GetStructure
            - https://api.spacetraders.io/#api-structures-GetMyStructure

        Args:
            structureId (str): ID of the structure to deposit the goods into
            user_owned (bool): Determines if the queried for structure is user owned or not

        Returns:
            dict : dict containing the info of the strucutre

        """
        endpoint = f"my/structures/{structureId}" if user_owned else f"structures/{structureId}"
        warning_log = F"Unable to get the info for structure: {structureId}"
        logging.info(f"Getting info about structure: {structureId}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get your strucutres
    def get_users_structures(self, raw_res=False, throttle_time=10):
        """Get the info about a structure

        Returns:
            dict : dict containings a JSON list of the structures the user owns
        """
        endpoint = f"my/structures"
        warning_log = F"Unable to get the info about your structures"
        logging.info(f"Getting info about the user's structures")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Transfer goods
    def transfer_goods(self, structureId, shipId, good, quantity, raw_res=False, throttle_time=10):
        """Transfer goods from a structure to a ship. The ship must be docked at the location the structure has been built.

        Args:
            structureId (str): ID of the structure to deposit the goods into
            shipId (str): ID of the ship to take the goods from
            good (str): symbol of the good to deposite. Eg: FUEL
            quantity (str): How many units of the good to deposit
        
        Returns:
            dict : dict containing the updated info of the ship and structure
        """
        endpoint = f"my/structures/{structureId}/transfer"
        params = {"shipId": shipId, "good": good, "quantity": quantity}
        warning_log = F"Unable to transfer {quantity} units of {good} from structure: {structureId} into ship: {shipId}"
        logging.info(f"Transferring {quantity} units of {good} from structure: {structureId} into ship: {shipId}")
        res = self.generic_api_call("POST", endpoint, params=params, token=self.token, warning_log=warning_log)
        return res if res else False

class Systems (Client):
    # Get system info
    def get_systems(self, raw_res=False, throttle_time=10):
        """[ENDPOINT CURRENTLY BROKEN - DEVS FIXING]
        
        Get info about the systems and their locations.

        Returns:
            dict: dict containing a JSON list of the different systems
        """
        # Get user
        endpoint = f"game/systems"
        warning_log = F"Unable to get systems"
        logging.info(f"Getting systems")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False    

        # Get all active flights
    def get_active_flight_plans(self, symbol, raw_res=False, throttle_time=10):
        """Get all the currently active flight plans in the system given. This is for all global accounts

        Args:
            symbol (str): Symbol of the system. OE or XV

        Returns:
            dict : dict containing a list of flight plans for each system as the key
        """
        endpoint = f"systems/{symbol}/flight-plans"
        warning_log = F"Unable to get flight plans for system: {symbol}."
        logging.info(f"Getting the flight plans in the {symbol} system")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    # Get System's Locations
    def get_system_locations(self, symbol, raw_res=False, throttle_time=10):
        """Get locations in the defined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict containing a JSON list of the locations in the system
        """
        endpoint = f"systems/{symbol}/locations"
        warning_log = F"Unable to get the locations in the system: {symbol}"
        logging.info(f"Getting the locations in system: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False  

    def get_system_docked_ships(self, symbol, raw_res=False, throttle_time=10):
        """Get docked ships in the defined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict containing a JSON list of the docked ships in the system
        """
        endpoint = f"systems/{symbol}/ships"
        warning_log = F"Unable to get the docked ships in the system: {symbol}"
        logging.info(f"Getting the docked ships in system: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False 

    def get_system(self, symbol, raw_res=False, throttle_time=10):
        """Get info on the definined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict with info about the system
        """
        endpoint = f"systems/{symbol}"
        warning_log = f"Unable to get the  system: {symbol}"
        logging.info(f"Getting the system: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False 

    def get_available_ships(self, symbol, raw_res=False, throttle_time=10):
        """Get the ships listed for sale in the system defined

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict containing a list of the available ships for sale
        """
        endpoint = f"systems/{symbol}/ship-listings"
        warning_log = F"Unable to get the listed ships in system: {symbol}"
        logging.info(f"Getting the ships available for sale: {symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False 

    def chart_waypoint(self, ship_symbol, raw_res=False, throttle_time=10):
        """Chart a new system or waypoint. 
        Returns an array of the symbols that have been charted, 
        including the system and the waypoint if both were uncharted, or just the waypoint.

        Args:
            ship_symbol (str): symbol of ship that will perform the charting
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjA-chart-waypoint
        """
        endpoint = f"my/ships/{ship_symbol}/chart"
        warning_log = f"Unable to chart the waypoint: {ship_symbol}"
        logging.info(f"Unable to chart the waypoint: {ship_symbol}")
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False 

    def list_systems(self, raw_res=False, throttle_time=10):
        """Return a list of all systems.

        Args:
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5Mjk2Mzc-list-systems
        """
        endpoint = f"systems"
        warning_log = f"Unable to view systems"
        logging.info(f"Unable to view systems")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False 
    
    def list_waypoints(self, system_symbol, raw_res=False, throttle_time=10):
        """Fetch all of the waypoints for a given system. 
        System must be charted or a ship must be present to return waypoint details.

        Args:
            system_symbol (str): symbol of system to get list of waypoints
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY2NzYwMTY-list-waypoints
        """
        endpoint = f"systems/{system_symbol}/waypoints"
        warning_log = f"Unable to get list of waypoints in system: {system_symbol}"
        logging.info(f"Unable to get list of waypoints in system: {system_symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

    def view_waypoint(self, system_symbol, waypoint_symbol, raw_res=False, throttle_time=10):
        """View the details of a waypoint.

        Args:
            system_symbol (str): Symbol of system waypoint is located in
            waypoint_symbol (str): Symbol of waypoint to get details for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}"
        warning_log = f"Unable to get details of waypoint: {waypoint_symbol}"
        logging.info(f"Unable to get details of waypoint: {waypoint_symbol}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False

class Users (Client):
    """THIS CLASS IS BEING DEPRECATED
    All methods have been removed or are being deprecated."""

    def get_your_info(self, raw_res=False, throttle_time=10):
        """THIS METHOD IS BEING DEPRECATED

        This method has now moved to the Account class. Please now use `account.info()`
        
        Get your user info

        Returns:
            dict: dict containing your user data
        """
        # Get user
        warnings.warn("Users class is being deprecated and replaced by the `Account` class. \nTo get your info please now use Api.account.info()", DeprecationWarning)
        endpoint = f"my/account"
        warning_log = F"Unable to get {self.username} user info"
        logging.info(f"Getting user info for {self.username}")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log)
        return res if res else False    

class Types (Client):
    def goods(self, raw_res=False, throttle_time=10):
        """Get's all the available goods in the game

        Args:
            raw_res (bool, optional): Returns the actual request response. Defaults to False.
            throttle_time (int, optional): Change how long to wait if throttled. Defaults to 10.

        Returns:
            dict: A dict containing a list of all the goods in the game
        """
        endpoint = f"types/goods"
        warning_log = F"Unable to get available goods"
        logging.info(f"Getting available goods")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log, 
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False 

    def loans(self, raw_res=False, throttle_time=10):
        """Get's all the available loans in the game

        Args:
            raw_res (bool, optional): Returns the actual request response. Defaults to False.
            throttle_time (int, optional): Change how long to wait if throttled. Defaults to 10.

        Returns:
            dict: A dict containing a list of all the loans in the game
        """
        endpoint = f"types/loans"
        warning_log = F"Unable to get available loans"
        logging.info(f"Getting available loans")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log, 
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False 
    
    def structures(self, raw_res=False, throttle_time=10):
        """Get's all the available structures in the game

        Args:
            raw_res (bool, optional): Returns the actual request response. Defaults to False.
            throttle_time (int, optional): Change how long to wait if throttled. Defaults to 10.

        Returns:
            dict: A dict containing a list of all the structures in the game
        """
        endpoint = f"types/structures"
        warning_log = F"Unable to get available structures"
        logging.info(f"Getting available structures")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log, 
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False 

    def ships(self, raw_res=False, throttle_time=10):
        """Get's all the available ships in the game

        Args:
            raw_res (bool, optional): Returns the actual request response. Defaults to False.
            throttle_time (int, optional): Change how long to wait if throttled. Defaults to 10.

        Returns:
            dict: A dict containing a list of all the ships in the game
        """
        endpoint = f"types/ships"
        warning_log = F"Unable to get available ships"
        logging.info(f"Getting available ships")
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log, 
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False 

class WarpJump (Client):
    def attempt_jump(self, shipId, raw_res=False, throttle_time=10):
        """Attempts sending a ship through a warp jump

        Args:
            raw_res (bool, optional): Returns the actual request response. Defaults to False.
            throttle_time (int, optional): Change how long to wait if throttled. Defaults to 10.

        Returns:
            dict: A dict containing a list of all the goods in the game
        """
        endpoint = f"my/warp-jumps"
        warning_log = F"Ship was unable to travel through warp jump"
        params = {"shipId": shipId}
        logging.info(f"Attempting travel through warp jump")
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log, params=params,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False 

class Api ():
    def __init__(self, username=None, token=None, v2=False):
        self.token = token
        self.v2 = v2
        if v2:
            self.ships = Ships(token=token, v2=True)
            self.systems = Systems(token=token, v2=True)
            self.agent = Agent(token=token, v2=True)
            self.markets = Markets(token=token, v2=True)
            self.trade = Trade(token=token, v2=True)
            self.navigation = Navigation(token=token, v2=True)
            self.contracts = Contracts(token=token, v2=True)
            self.extract = Extract(token=token, v2=True)
            self.shipyard = Shipyard(token=token, v2=True)
        else:
            self.username = username
            self.account = Account(username, token)
            self.flightplans = FlightPlans(username, token)
            self.game = Game(username, token)
            self.leaderboard = Leaderboard(username, token)
            self.loans = Loans(username, token)
            self.locations = Locations(username, token)
            self.marketplace = Marketplace(username, token)
            self.purchaseOrders = PurchaseOrders(username, token)
            self.sellOrders = SellOrders(username, token)
            self.ships = Ships(username, token)
            self.structures = Structures(username, token)
            self.systems = Systems(username, token)
            self.users = Users(username, token)
            self.types = Types(username, token)
            self.warpjump = WarpJump(username, token)

    def generate_token(self):
        """Trys to create a new user and return their token

        Args:
            username (str): Username to user

        Returns:
            str: Token if user valid else None
        """
        url = f"https://api.spacetraders.io/users/{self.username}/claim"
        try:
            res = make_request("POST", url, None, None)
            if res.ok:
                self.token = res.json()['token']
                self.game.token = self.token
                self.leaderboard.token = self.token
                self.loans.token = self.token
                self.locations.token = self.token
                self.marketplace.token = self.token
                self.purchaseOrders.token = self.token
                self.sellOrders.token = self.token
                self.ships.token = self.token
                self.structures.token = self.token
                self.systems.token = self.token
                self.users.token = self.token
                self.types.token = self.token
                self.account = self.token
                self.warpjump = self.token
            else:
                logging.exception(f"Code: {res.json()['error']['code']}, Message: {res.json()['error']['message']}")
                return None
        except Exception as e:
            return e


#
#
# V2 Related Classes
#
#


class Agent(Client):
    """
    Get or create your agent details
    """
    def get_my_agent_details(self, raw_res=False, throttle_time=10):
        """Get your agent details

        https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MTk-my-agent-details

        Example response:
        {
            "data": {
                "accountId": "cl0hok34m0003ks0jjql5q8f2",
                "symbol": "EMBER",
                "headquarters": "X1-OE-PM",
                "credits": 0
            }
        }

        Args:
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/agent"
        warning_log = f"Unable to retrieve agent details"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def register_new_agent(self, symbol, faction, raw_res=False, throttle_time=10):
        """Registers a new agent in the Space Traders world

        Args:
            symbol (str): The symbol for your agent's ships
            faction (str): The faction you wish to join
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"agents"
        warning_log = f"Unable to register new agent"
        params = {
            'symbol': symbol,
            'faction': faction
        }
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False


class Markets(Client):
    """Endpoints related to interacting with markets in the system

    Args:
        Client (Client): Details to login to your agent
    """
    def deploy_asset(self, ship_symbol, trade_symbol, raw_res=False, throttle_time=10):
        """Use this endpoint to deploy a Communications Relay to a waypoint. 
            A waypoint with a communications relay will allow agents to retrieve price information from the market. 
            Without a relay, agents must send a ship to a market to retrieve price information.
            Communication relays can be purchased from a market that exports COMM_RELAY_I.

        Args:
            shipSymbol (str): The symbol for your agent's ships
            tradeSymbol (str): Symbol for communicatino relay that you want to deploy to the waypoint.
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0ODE2NDA-deploy-asset
        """
        endpoint = f"my/ships/{ship_symbol}/deploy"
        params = {'tradeSymbol': trade_symbol}
        warning_log = f"Unable to deploy communicatino relay. Ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def trade_imports(self, trade_symbol, raw_res=False, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNTg-trade-imports
        """
        endpoint = f"trade/{trade_symbol}/imports"
        warning_log = f"Unable to view trade import for trade: {trade_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def trade_exports(self, trade_symbol, raw_res=False, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNTk-trade-exports
        """
        endpoint = f"trade/{trade_symbol}/exports"
        warning_log = f"Unable to view trade export for trade: {trade_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False
    
    def trade_exchanges(self, trade_symbol, raw_res=False, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNjA-trade-exchanges
        """
        endpoint = f"trade/{trade_symbol}/exchange"
        warning_log = f"Unable to view trade exchange for trade good: {trade_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def list_markets(self, system_symbol, raw_res=False, throttle_time=10):
        """Retrieve a list of all charted markets in the given system. 
           Markets are only available if the waypoint is charted and contains a communications relay.

           To install a communications relay at a market, look at the my/ships/{shipSymbol}/deploy endpoint.

        Args:
            system_symbol (sre): symbol of the system you want to list markets for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        
        API URL: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0ODYwNjQ-list-markets
        """
        endpoint = f"systems/{system_symbol}/markets"
        warning_log = f"Unable to get list of markets in system: {system_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def view_market(self, system_symbol, waypoint_symbol, raw_res=False, throttle_time=10):
        """Retrieve imports, exports and exchange data from a marketplace. 
           Imports can be sold, exports can be purchased, and exchange trades can be purchased or sold.

           Market data is only available if you have a ship at the location, or the location is charted and has a communications relay deployed.

           See /my/ships/{shipSymbol}/deploy for deploying relays at a location.

        Args:
            system_symbol (str): Symbol for the system the market is located in
            waypoint_symbol (str): Symbol for the waypoint the market is located in
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY2OTM4NjY-view-market
        """
        endpoint = f"systems/{system_symbol}/markets/{waypoint_symbol}"
        warning_log = f"Unable to get markets in system: {system_symbol} & waypoint: {waypoint_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False


class Trade(Client):
    "Buy and Sell cargo"
    def purchase_cargo(self, ship_symbol, trade_symbol, units, raw_res=False, throttle_time=10):
        """Purchase cargo from a waypoint's market
        
        Example Response:
        {
            "data": {
                "waypointSymbol": "X1-OE-PM",
                "tradeSymbol": "MICROPROCESSORS",
                "credits": -843,
                "units": 1
            }
        }

        Args:
            ship_symbol (str): Symbol of the ship to transfer the cargo onto
            trade_symbol (str): symbol of the trade good to purchase
            units (str): how many units of the trade good to purchase
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjc-purchase-cargo
        """
        endpoint = f"my/ships/{ship_symbol}/purchase"
        params = {
            'tradeSymbol': trade_symbol,
            'units': units
        }
        warning_log = f"Unable to get purchase {units} units of good: {trade_symbol} onto ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def sell_cargo(self, ship_symbol, trade_symbol, units, raw_res=False, throttle_time=10):
        """Sell cargo to a waypoint's market
        
        Example Response:
        {
            "data": {
                "waypointSymbol": "X1-OE-PM",
                "tradeSymbol": "SILICON",
                "credits": 144,
                "units": -1
            }
        }

        Args:
            ship_symbol (str): Symbol of the ship to transfer the cargo from
            trade_symbol (str): symbol of the trade good to sell
            units (int): how many units of the trade good to sell
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MzA-sell-cargo
        """
        endpoint = f"my/ships/{ship_symbol}/sell"
        params = {
            'tradeSymbol': trade_symbol,
            'units': units
        }
        warning_log = f"Unable to get purchase {units} units of good: {trade_symbol} onto ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False


class Navigation(Client):

    def dock_ship(self, ship_symbol, raw_res=False, throttle_time=10):
        """Transition your ship from orbit to docked. Consecutive calls to this endpoint will succeed.

        {
            "data": {
                "status": "DOCKED"
            }
        }

        Args:
            ship_symbol (str): Symbol of the ship to dock
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        
        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjI-dock-ship
        """
        endpoint = f"my/ships/{ship_symbol}/dock"
        warning_log = f"Unable to dock ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def orbit_ship(self, ship_symbol, raw_res=False, throttle_time=10):
        """Transition your ship from docked into orbit. 
        Ships are placed into orbit by default when arriving at a destination. 
        Consecutive calls to this endpoint will continue to return a 200 response status.

        {
            "data": {
                "status": "ORBIT"
            }
        }

        Args:
            ship_symbol (str): Symbol of the ship to dock
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        
        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjI-dock-ship
        """
        endpoint = f"my/ships/{ship_symbol}/orbit"
        warning_log = f"Unable to orbit ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False
    
    def jump_ship(self, ship_symbol, destination, raw_res=False, throttle_time=10):
        """Navigate a ship between systems

        Args:
            ship_symbol (str): Symbol of ship to make a jump
            destination (str): System to jump to
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjY-jump-ship
        """
        endpoint = f"my/ships/{ship_symbol}/jump"
        params = {'destination': destination}
        warning_log = f"Unable to jump ship: {ship_symbol} to System: {destination}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def jump_cooldown(self, ship_symbol, raw_res=False, throttle_time=10):
        """See how long your ship has on cooldown

        Args:
            ship_symbol (str): Symbol of the ship to check it's cooldown for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyMzY2MDg-jump-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/jump"
        warning_log = f"Unable to jump ship: {ship_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False
    
    def refuel_ship(self, ship_symbol, raw_res=False, throttle_time=10):
        """Fully refuel a ship

        Response example:
        {
            "data": {
                "credits": -1920,
                "fuel": 800
            }
        }

        Args:
            ship_symbol (str): Symbol of ship to refuel
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjg-refuel-ship
        """
        endpoint = f"my/ships/{ship_symbol}/refuel"
        warning_log = f"Unable to refuel ship: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def navigate_ship(self, ship_symbol, destination, raw_res=False, throttle_time=10):
        """Fly a ship from one place to another.

        Example response:
        {
            "data": {
                "fuelCost": 38,
                "navigation": {
                "shipSymbol": "BA03F2-1",
                "departure": "X1-OE-PM",
                "destination": "X1-OE-A005",
                "durationRemaining": 2279,
                "arrivedAt": null
                }
            }
        }

        Args:
            ship_symbol (str): Symbol of ship to fly
            destination (str): Symbol of destination to fly to
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzQ3MzU-navigate-ship
        """
        endpoint = f"my/ships/{ship_symbol}/navigate"
        params = {'destination': destination}
        warning_log = f"Unable to navigate ship: {ship_symbol} to destination: {destination}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def navigation_status(self, ship_symbol, raw_res=False, throttle_time=10):
        """Checks to see the status of a ships navigation path

        Args:
            ship_symbol (str): Symbol of ship to check navigation status for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        
            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzQ3MzY-navigation-status
        """
        endpoint = f"my/ships/{ship_symbol}/navigate"
        warning_log = f"Unable to get navigation status for ship: {ship_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False


class Contracts(Client):
    """Endpoints to handle contracts"""
    def deliver_contract(self, ship_symbol, contract_id, trade_symbol, units, raw_res=False, throttle_time=10):
        """Deliver cargo on a given contract.

        Args:
            ship_symbol (str): The symbol of the ship
            contract_id (str): Id of contract to deliver goods for
            trade_symbol (sre): Trade goods to deliver
            units (int): how many units to deliver
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjE-deliver-on-contract
        """
        endpoint = f"my/ships/{ship_symbol}/deliver"
        params={
            'contractId': contract_id,
            'tradeSymbol': trade_symbol,
            'units': units
        }
        warning_log = f"Unable to deliver trade goods for contract: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def list_contracts(self, raw_res=False, throttle_time=10):
        """List all of your contracts.

        Args:
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5NDc4NTg-list-contracts
        """
        endpoint = f"my/contracts"
        warning_log = f"Unable to get a list of your contracts"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def contract_details(self, contract_id, raw_res=False, throttle_time=10):
        """Get the details of a contract by ID.

        Args:
            contract_id (str): Id of contract to get the details for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/contracts/{contract_id}"
        warning_log = f"Unable to get details of contract: {contract_id}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def accept_contract(self, contract_id, raw_res=False, throttle_time=10):
        """Accept a contract.

        Args:
            contract_id (str): ID of contract to accept
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5NTI5NjQ-accept-contract
        """
        endpoint = f"my/contracts/{contract_id}/accept"
        warning_log = f"Unable to accept contract: {contract_id}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False


class Extract(Client):
    """Functions related to extracting resources from a waypoint"""
    def extract_resource(self, ship_symbol, survey = {}, raw_res=False, throttle_time=10):
        """Extract resources from the waypoint into your ship. 
        Send a survey as the payload to target specific yields. 
        The entire survey must be sent as it contains a signature that the backend verifies.

        Example Response:
        {
            "data": {
                "extraction": {
                    "shipSymbol": "4B902A-1",
                    "yield": {
                        "tradeSymbol": "SILICON",
                        "units": 16
                    }
                },
                "cooldown": {
                    "duration": 119,
                    "expiration": "2022-03-12T00:41:29.371Z"
                }
            }
        }

        Args:
            ship_symbol (str): Symbol of ship performing the extraction
            payload (dict): entire response from a survey of a waypoint
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/ships/{ship_symbol}/extract"
        warning_log = f"Unable to extract resources: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=survey)
        return res if res else False

    def extraction_cooldown(self, ship_symbol, raw_res=False, throttle_time=10):
        """Get the status of your last extraction.

        Args:
            ship_symbol (str): Symbol of ship to get status for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NDQ-extraction-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/extract"
        warning_log = f"Get the status of your last extraction: {ship_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def survey_waypoint(self, ship_symbol, raw_res=False, throttle_time=10):
        """If you want to target specific yields for an extraction, you can survey a waypoint, 
        such as an asteroid field, and send the survey in the body of the extract request. 
        Each survey may have multiple deposits, and if a symbol shows up more than once, 
        that indicates a higher chance of extracting that resource.

        Your ship will enter a cooldown between consecutive survey requests. 
        Surveys will eventually expire after a period of time. 
        Multiple ships can use the same survey for extraction.

        Args:
            ship_symbol (str): Symbol of ship to perform the survey
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NTI-survey-waypoint
        """
        endpoint = f"my/ships/{ship_symbol}/survey"
        warning_log = f"Unable to perform a survey of a waypoint: {ship_symbol}"
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def survey_cooldown(self, ship_symbol, raw_res=False, throttle_time=10):
        """Executing a survey will initiate a cooldown for a number of seconds before you can call it again. 
        This endpoint returns the details of your cooldown, or a 404 if there is no cooldown for the survey action.

        Args:
            ship_symbol (str): symbol of ship to check status of cooldown
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NTM-survey-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/survey"
        warning_log = f"Unable to check on status of cooldown for ship: {ship_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

class Shipyard(Client):
    """Function specific to handling shipyard"""
    def purchase_ship(self, listing_id, raw_res=False, throttle_time=10):
        """Purchase a ship

        Args:
            listing_id (str): The id of the shipyard listing you want to purchase.
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDc-purchase-ship
        """
        endpoint = f"my/ships"
        warning_log = f"Unable to purchase ship with listing id: {listing_id}"
        params = {'id': listing_id}
        res = self.generic_api_call("POST", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time, params=params)
        return res if res else False

    def list_shipyards(self, system_symbol, raw_res=False, throttle_time=10):
        """Returns a list of all shipyards in a system.

        Args:
            system_symbol (str): symbol of system to get list of shipyards for
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDY-list-shipyards
        """
        endpoint = f"systems/{system_symbol}/shipyards"
        warning_log = f"Unable to view shipyards in system: {system_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def shipyard_details(self, system_symbol, waypoint_symbol, raw_res=False, throttle_time=10):
        """Get details about a shipyard

        Args:
            system_symbol (str): Symbol of system shipyard is located in
            waypoint_symbol (str): Symbol of waypoint shipyeard is located in
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDQ-shipyard-details
        """
        endpoint = f"systems/{system_symbol}/shipyards/{waypoint_symbol}"
        warning_log = f"Unable to view shipyard in system: {system_symbol}, waypoint: {waypoint_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False

    def shipyard_listings(self, system_symbol, waypoint_symbol, raw_res=False, throttle_time=10):
        """View ships available for purchase in shipyard

        Args:
            system_symbol (str): system shipyard is located in
            waypoint_symbol (str): waypoint shipyard is located in
            raw_res (bool, optional): Return raw respose insteas of JSON. Defaults to False.
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"systems/{system_symbol}/shipyards/{waypoint_symbol}/ships"
        warning_log = f"Unable to view ships in shipyard in system: {system_symbol}, waypoint: {waypoint_symbol}"
        res = self.generic_api_call("GET", endpoint, token=self.token, warning_log=warning_log,
                                    raw_res=raw_res, throttle_time=throttle_time)
        return res if res else False


if __name__ == "__main__":
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGlmaWVyIjoiSE1BUyIsImlhdCI6MTY1Mzc4NDEzNSwic3ViIjoiYWdlbnQtdG9rZW4ifQ.ovMpoIza1Xd9f5WfvxtvQTGmHVELXfea9sdm-usgdnFxr_vLxm3YTIFMxZPeptIXd_GVc9rX4m_iEajpu_DZzeO4uDO0w66vY9GNnltdid243v1ePMVacTZg0sVsVLG24SjL5hlNrb-4TUZ8yDJkdg-C4w_1ODbB3YZ1KxrHTt4u4F-zbfuW8JNkAJBa-KBUHhpI3Abl3G699KzNYuj77m5u1XtBtDfHBXHQqTeSlz72jf5nLUSFcN4BGoADCPyZxmUPK4C9NRW_IYUiEqa4i7ETBaoUVl-Ot6bnEJ2ZTciDqj8cdgZHMsMqq68pB_fnw1-hkaECVxkwSK6uK3LmPVD0R8-BtVcxOx0NvDQxKyLoLjKHPxAbOgfk1j_51qJuscPxzosPkimK8wOZGlxuUrXCp6FAwVHzIcDhU-Y0KvLdG-OZpM6nDJZe-2WbjCeFhM8JgDG-Sne2kTY32MfhVYWMeXdNmRuTOJaCCh-dF5WVRs53bGzczsYhYz4tAbbU"
    client = Client("HMAS", token=token, v2=True)
    ship = Ships("", token, v2=True)
    extract = Shipyard("", token, v2=True)
    print(ship.get_user_ships())
    # username = "JimHawkins"
    # token = "0930cc36-7dc7-4cb1-8823-d8e72594d91e"

    # api = Api(username, token)

    # print(api.loans.get_loans_available())
