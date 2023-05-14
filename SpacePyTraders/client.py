from asyncio.format_helpers import extract_stack
import requests
import logging
import time
from dataclasses import dataclass, field
import warnings
from ratelimit import limits, sleep_and_retry
import json
from SpacePyTraders.exceptions import *
from typing import Union

URL = "https://api.spacetraders.io/"
V2_URL = "https://api.spacetraders.io/v2/"
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(thread)d - %(message)s", level=logging.INFO
)


# @limits(calls=2, period=1, )
@sleep_and_retry
def make_request(
    method: str, url: str, headers: dict, params: Union[dict, None] = None
) -> requests.Response:
    """Checks which method to use and then makes the actual request to Space Traders API

    Args:
        method (str): The HTTP method to use
        url (str): The URL of the request
        headers (dict): the request headers holding the Auth
        params (dict, optional): Any params required for the request. Defaults to None.

    Returns:
        Request: Returns the request

    Exceptions:
        Exception: Invalid method - must be GET, POST, PUT or DELETE
    """
    # Convert params into proper JSON data
    params_json = None if params is None else json.dumps(params)
    # Define the different HTTP methods
    if method == "GET":
        r = requests.get(url, headers=headers, params=params_json)
    elif method == "POST":
        r = requests.post(url, headers=headers, data=params_json)
    elif method == "PUT":
        r = requests.put(url, headers=headers, data=params_json)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers, data=params_json)
    else:
        raise Exception(f"Invalid method provided: {method}")

    if r is None:
        raise Exception("No response returned")

    return r


@dataclass
class Client:
    def __init__(self, token: Union[str, None] = None):
        """The Client class handles all user interaction with the Space Traders API.
        The class is initiated with the username and token of the user.
        If the user does not provide a token the 'create_user' method will attempt to fire and create a user with the username provided.
        If a user with the name already exists an exception will fire.

        Args:
            username (str): Username of the user
            token (str): The personal auth token for the user. If None will invoke the 'create_user' method
            v2 (bool): Determine if you want to use the new V2 API or V1
        """
        self.token: str = token if token else ""
        self.url: str = V2_URL

    def generic_api_call(
        self,
        method: str,
        endpoint: str,
        params: Union[dict, None] = None,
        token: str = "",
        warning_log: str = "",
        throttle_time: int = 10,
    ) -> dict:
        """Function to make consolidate parameters to make an API call to the Space Traders API.
        Handles any throttling or error returned by the Space Traders API.

        Args:
            method (str): The HTTP method to use. GET, POST, PUT or DELETE
            endpoint (str): The API endpoint
            params (dict, optional): Any params required for the endpoint. Defaults to None.
            token (str, optional): The token of the user. Defaults to None.
            throttle_time (int, default = 10): Sets how long the wait time before attempting call again. Default is 10 seconds

        Returns:
            Any: depends on the return from the API but likely JSON
        """
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        # Make the request to the Space Traders API
        for i in range(10):
            try:
                r = make_request(method, self.url + endpoint, headers, params)
                # If an error returned from api
                if "error" in r.json():
                    error = r.json()
                    code = error["error"]["code"]
                    message = error["error"]["message"]
                    logging.warning(
                        f"An error has occurred when hitting: {r.request.method} {r.url} with parameters: {params}. Error: "
                        + str(error)
                    )

                    raise which_exception(error["error"])

                # If successful return r
                return r.json()

            except ThrottleException as te:
                logging.info(te.message)
                time.sleep(throttle_time)
                continue

            except ServerException as se:
                logging.info(se.message)
                time.sleep(throttle_time)
                continue

        # If failed to make call after 10 tries fail it
        raise (TooManyTriesException)


class Ships(Client):
    def buy_ship(self, waypoint_symbol, ship_type, throttle_time=10):
        """Buys a ship of the type provided and at the location provided.
        Certain ships can only be bought from specific locations. Use get_available_ships to see full list.

        Args:
            - waypoint_symbol (str): symbol of the waypoint the ship to buy is
            - ship_type (str): type of ship you want to buy e.g. SHIP_MINING_DRONE
        """
        endpoint = f"my/ships"
        params = {"waypointSymbol": waypoint_symbol, "shipType": ship_type}
        warning_log = (
            f"Unable to buy ship type: {ship_type}, at location: {waypoint_symbol}."
        )
        logging.debug(
            f"Buying ship of type: {ship_type} at location: {waypoint_symbol}"
        )
        res = self.generic_api_call(
            "POST", endpoint, params=params, token=self.token, warning_log=warning_log
        )
        return res

    # Get Ship
    def get_ship(self, ship_id: str, throttle_time: int = 10) -> dict:
        """Get info on the ship

        Args:
            ship_id (str): The shipId of the ship you want to get info on

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
        endpoint = f"my/ships/{ship_id}"
        warning_log = f"Unable to get info fo ship: {ship_id}"
        logging.info(f"Getting info on ship: {ship_id}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    # Get Users ships
    def get_user_ships(self, throttle_time=10):
        """Get a list of all the ships you own

        Returns:
            dict: A JSON list of the ships you own. Each item is a return from the get_ship_info endpoint.

        API Link: https://api.spacetraders.io/#api-ships-GetShips
        V2 API: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MzI-list-ships
        """
        endpoint = f"my/ships"
        warning_log = f"Unable to get list of owned ships."
        logging.info(f"Getting a list of owned ships")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    # Jettison Cargo
    def jettinson_cargo(self, ship_symbol, symbol, units, throttle_time=10):
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
        endpoint = f"my/ships/{ship_symbol}/jettison"
        warning_log = f"Unable to jettison cargo from ship. Params - shipId: {ship_symbol}, good: {symbol}, quantity: {units}"
        logging.info(
            f"Jettison the following cargo from ship: {ship_symbol}, good: {symbol}, quantity: {units}"
        )
        params = {"symbol": symbol, "units": units}
        res = self.generic_api_call(
            "POST", endpoint, params=params, token=self.token, warning_log=warning_log
        )
        return res

    # Scrap Ship
    def scrap_ship(self, shipId, throttle_time=10):
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
        res = self.generic_api_call(
            "DELETE", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    # Transfer Cargo
    def transfer_cargo(self, fromShipId, toShipId, good, quantity, throttle_time=10):
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
        warning_log = f"Unable to transfer {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}"
        logging.info(
            f"Transferring {quantity} units of {good} from ship: {fromShipId} to ship: {toShipId}"
        )
        params = {"toShipId": toShipId, "good": good, "quantity": quantity}
        res = self.generic_api_call(
            "POST", endpoint, params=params, token=self.token, warning_log=warning_log
        )
        return res

    def scan(self, shipSymbol, mode, throttle_time=10):
        """Execute a ship scan to view approach / departing ships, system information or details about a waypoint.
           Send a scan mode to select the type of scan performed by your ship.

        Args:
            shipSymbol (str): The ship's symbol (id)
            mode (str): What type of scan do you want to undertake. APPROACHING_SHIPS, DEPARTING_SHIPS, SYSTEM, WAYPOINT

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: Return JSON repsonse

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjk-scan
        """
        endpoint = f"my/ships/{shipSymbol}/scan"
        params = {"mode": mode}
        warning_log = f"Unable to perform scan of mode: {mode}"
        logging.info(f"Unable to perform scan of mode: {mode}")
        res = self.generic_api_call(
            "POST", endpoint, params=params, token=self.token, warning_log=warning_log
        )
        return res

    def scan_cooldown(self, shipSymbol, throttle_time=10):
        """See how long your ship must wait before it can scan again.

        Args:
            shipSymbol (str): The ship's symbol (id)

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: Return JSON repsonse

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyMzgxMTc-scan-cooldown
        """
        endpoint = f"my/ships/{shipSymbol}/scan"
        warning_log = f"Unable to obtain scan cooldown for ship: {shipSymbol}"
        logging.info(f"Unable to obtain scan cooldown for ship: {shipSymbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def dock_ship(self, ship_symbol, throttle_time=10):
        """Transition your ship from orbit to docked. Consecutive calls to this endpoint will succeed.

        {
            "data": {
                "status": "DOCKED"
            }
        }

        Args:
            ship_symbol (str): Symbol of the ship to dock

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjI-dock-ship
        """
        endpoint = f"my/ships/{ship_symbol}/dock"
        warning_log = f"Unable to dock ship: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def orbit_ship(self, ship_symbol, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjI-dock-ship
        """
        endpoint = f"my/ships/{ship_symbol}/orbit"
        warning_log = f"Unable to orbit ship: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def jump_ship(self, ship_symbol, destination, throttle_time=10):
        """Navigate a ship between systems

        Args:
            ship_symbol (str): Symbol of ship to make a jump
            destination (str): System to jump to

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjY-jump-ship
        """
        endpoint = f"my/ships/{ship_symbol}/jump"
        params = {"destination": destination}
        warning_log = f"Unable to jump ship: {ship_symbol} to System: {destination}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def jump_cooldown(self, ship_symbol, throttle_time=10):
        """See how long your ship has on cooldown

        Args:
            ship_symbol (str): Symbol of the ship to check it's cooldown for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyMzY2MDg-jump-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/jump"
        warning_log = f"Unable to jump ship: {ship_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def refuel_ship(self, ship_symbol, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjg-refuel-ship
        """
        endpoint = f"my/ships/{ship_symbol}/refuel"
        warning_log = f"Unable to refuel ship: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def navigate_ship(
        self,
        ship_symbol: str,
        waypoint_symbol: str,
        raw_res: bool = False,
        throttle_time: int = 10,
    ) -> dict:
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
            waypoint_symbol (str): Symbol of destination to fly to

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzQ3MzU-navigate-ship
        """
        endpoint = f"my/ships/{ship_symbol}/navigate"
        params = {"waypointSymbol": waypoint_symbol}
        warning_log = (
            f"Unable to navigate ship: {ship_symbol} to destination: {waypoint_symbol}"
        )
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def navigation_status(self, ship_symbol, throttle_time=10):
        """Checks to see the status of a ships navigation path

        Args:
            ship_symbol (str): Symbol of ship to check navigation status for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzQ3MzY-navigation-status
        """
        endpoint = f"my/ships/{ship_symbol}/navigate"
        warning_log = f"Unable to get navigation status for ship: {ship_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res


class Systems(Client):
    def chart_waypoint(self, ship_symbol, throttle_time=10):
        """Chart a new system or waypoint.
        Returns an array of the symbols that have been charted,
        including the system and the waypoint if both were uncharted, or just the waypoint.

        Args:
            ship_symbol (str): symbol of ship that will perform the charting

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjA-chart-waypoint
        """
        endpoint = f"my/ships/{ship_symbol}/chart"
        warning_log = f"Unable to chart the waypoint: {ship_symbol}"
        logging.info(f"Unable to chart the waypoint: {ship_symbol}")
        res = self.generic_api_call(
            "POST", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def list_systems(self, throttle_time=10):
        """Return a list of all systems.

        Args:

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5Mjk2Mzc-list-systems
        """
        endpoint = f"systems"
        warning_log = f"Unable to view systems"
        logging.info(f"Unable to view systems")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def get_system(self, symbol, throttle_time=10):
        """Get info on the definined system

        Args:
            symbol (str): The symbol for the system eg: OE

        Returns:
            dict: A dict with info about the system
        """
        endpoint = f"systems/{symbol}"
        warning_log = f"Unable to get the  system: {symbol}"
        logging.info(f"Getting the system: {symbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def list_waypoints(self, system_symbol: str, throttle_time=10):
        """Fetch all of the waypoints for a given system.
        System must be charted or a ship must be present to return waypoint details.

        Args:
            system_symbol (str): symbol of system to get list of waypoints

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY2NzYwMTY-list-waypoints
        """
        endpoint = f"systems/{system_symbol}/waypoints"
        warning_log = f"Unable to get list of waypoints in system: {system_symbol}"
        logging.info(f"Getting list of waypoints in sytem: {system_symbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def get_waypoint(
        self, system_symbol: str, waypoint_symbol: str, throttle_time: int = 10
    ) -> dict:
        """View the details of a waypoint.

        Args:
            system_symbol (str): Symbol of system waypoint is located in
            waypoint_symbol (str): Symbol of waypoint to get details for
            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}"
        warning_log = f"Unable to get details of waypoint: {waypoint_symbol}"
        logging.info(f"Viewing waypoint: {waypoint_symbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def get_market(self, system_symbol, waypoint_symbol, throttle_time=10):
        """Retrieve imports, exports and exchange data from a marketplace.
           Imports can be sold, exports can be purchased, and exchange trades can be purchased or sold.

           Market data is only available if you have a ship at the location, or the location is charted and has a communications relay deployed.

           See /my/ships/{shipSymbol}/deploy for deploying relays at a location.

        Args:
            system_symbol (str): Symbol for the system the market is located in
            waypoint_symbol (str): Symbol for the waypoint the market is located in

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY2OTM4NjY-view-market
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}/market"
        warning_log = f"Unable to get markets in system: {system_symbol} & waypoint: {waypoint_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def get_shipyard(self, system_symbol: str, waypoint_symbol: str, throttle_time=10):
        """Get the ships listed for sale in the system defined

        Args:
            system_symbol (str): The symbol for the system eg: OE
            waypoint_symbol (str): The symbol for the waypoint eg: OE-PM-TR

        Returns:
            dict: A dict containing a list of the available ships for sale
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}/shipyard"
        warning_log = f"Unable to get the listed ships at waypoint: {waypoint_symbol}"
        logging.info(f"Getting the ships available for sale in: {waypoint_symbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res

    def get_jump_gate(self, system_symbol: str, waypoint_symbol: str, throttle_time=10):
        """Gets the jump gate info for the system and waypoint defined

        Args:
            system_symbol (str): The symbol for the system eg: OE
            waypoint_symbol (str): The symbol for the waypoint eg: OE-PM-TR

        Returns:
            dict: A dict containing a list of the available ships for sale
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}/jump-gate"
        warning_log = f"Unable to get the jump gate at waypoint: {waypoint_symbol}"
        logging.info(f"Getting the jump gate at: {waypoint_symbol}")
        res = self.generic_api_call(
            "GET", endpoint, token=self.token, warning_log=warning_log
        )
        return res


class Api:
    def __init__(self, token=None):
        self.token = token
        self.agent = Agent(token=token)
        self.contracts = Contracts(token=token)
        self.extract = Extract(token=token)
        self.markets = Markets(token=token)
        self.ships = Ships(token=token)
        self.shipyard = Shipyard(token=token)
        self.systems = Systems(token=token)
        self.trade = Trade(token=token)

    def register_new_agent(self, symbol, faction, *args, **kwargs):
        """Registers a new agent in the Space Traders world

        Args:
            symbol (str): The symbol for your agent's ships
            faction (str): The faction you wish to join

        Returns:
            dict: JSON response

        Usage:
            >>> from spacetraders.api import Api
            >>> api = Api()
            >>> res = api.register_new_agent("HMS", "QUANTUM")
        """
        endpoint = f"register"
        warning_log = f"Unable to register new agent"
        params = {"symbol": symbol, "faction": faction}
        res = make_request("POST", V2_URL + endpoint, headers={}, params=params)
        print(res.text)
        if res.ok:
            data = res.json().get("data")
            self.token = data.get("token")
            self.ships.token = self.token
            self.systems.token = self.token
            self.agent.token = self.token
            self.markets.token = self.token
            self.trade.token = self.token
            self.contracts.token = self.token
            self.extract.token = self.token
            self.shipyard.token = self.token
        else:
            logging.warning(warning_log)
            logging.warning(res.text)
        return res


#
#
# V2 Related Classes
#
#


class Agent(Client):
    """
    Get or create your agent details
    """

    def get_my_agent(self, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/agent"
        warning_log = f"Unable to retrieve agent details"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def register_new_agent(self, symbol, faction, throttle_time=10):
        """Registers a new agent in the Space Traders world

        Args:
            symbol (str): The symbol for your agent's ships
            faction (str): The faction you wish to join

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        Usage:
            >>> from spacetraders.api import Api
            >>> api = Api()
            >>> res = api.agent.register_new_agent("HMS", "QUANTUM")
        """
        endpoint = f"register"
        warning_log = f"Unable to register new agent"
        params = {"symbol": symbol, "faction": faction}
        res = self.generic_api_call(
            "POST",
            endpoint,
            token="",
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )

        return res


class Markets(Client):
    """Endpoints related to interacting with markets in the system

    Args:
        Client (Client): Details to login to your agent
    """

    def deploy_asset(self, ship_symbol, trade_symbol, throttle_time=10):
        """Use this endpoint to deploy a Communications Relay to a waypoint.
            A waypoint with a communications relay will allow agents to retrieve price information from the market.
            Without a relay, agents must send a ship to a market to retrieve price information.
            Communication relays can be purchased from a market that exports COMM_RELAY_I.

        Args:
            shipSymbol (str): The symbol for your agent's ships
            tradeSymbol (str): Symbol for communicatino relay that you want to deploy to the waypoint.

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0ODE2NDA-deploy-asset
        """
        endpoint = f"my/ships/{ship_symbol}/deploy"
        params = {"tradeSymbol": trade_symbol}
        warning_log = f"Unable to deploy communicatino relay. Ship: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def trade_imports(self, trade_symbol, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNTg-trade-imports
        """
        endpoint = f"trade/{trade_symbol}/imports"
        warning_log = f"Unable to view trade import for trade: {trade_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def trade_exports(self, trade_symbol, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNTk-trade-exports
        """
        endpoint = f"trade/{trade_symbol}/exports"
        warning_log = f"Unable to view trade export for trade: {trade_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def trade_exchanges(self, trade_symbol, throttle_time=10):
        """TODO: Explain what this endpoint does

        Args:
            trade_symbol (str): symbol of the trade good you want to import

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0MDgxNjA-trade-exchanges
        """
        endpoint = f"trade/{trade_symbol}/exchange"
        warning_log = f"Unable to view trade exchange for trade good: {trade_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def list_markets(self, system_symbol, throttle_time=10):
        """Retrieve a list of all charted markets in the given system.
           Markets are only available if the waypoint is charted and contains a communications relay.

           To install a communications relay at a market, look at the my/ships/{shipSymbol}/deploy endpoint.

        Args:
            system_symbol (sre): symbol of the system you want to list markets for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

        API URL: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY0ODYwNjQ-list-markets
        """
        endpoint = f"systems/{system_symbol}/markets"
        warning_log = f"Unable to get list of markets in system: {system_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def view_market(self, system_symbol, waypoint_symbol, throttle_time=10):
        """Retrieve imports, exports and exchange data from a marketplace.
           Imports can be sold, exports can be purchased, and exchange trades can be purchased or sold.

           Market data is only available if you have a ship at the location, or the location is charted and has a communications relay deployed.

           See /my/ships/{shipSymbol}/deploy for deploying relays at a location.

        Args:
            system_symbol (str): Symbol for the system the market is located in
            waypoint_symbol (str): Symbol for the waypoint the market is located in

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDY2OTM4NjY-view-market
        """
        endpoint = f"systems/{system_symbol}/waypoints/{waypoint_symbol}/market"
        warning_log = f"Unable to get markets in system: {system_symbol} & waypoint: {waypoint_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res


class Trade(Client):
    "Buy and Sell cargo"

    def purchase_cargo(self, ship_symbol, trade_symbol, units, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0Mjc-purchase-cargo
        """
        endpoint = f"my/ships/{ship_symbol}/purchase"
        params = {"symbol": trade_symbol, "units": units}
        warning_log = f"Unable to get purchase {units} units of good: {trade_symbol} onto ship: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def sell_cargo(self, ship_symbol, trade_symbol, units, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MzA-sell-cargo
        """
        endpoint = f"my/ships/{ship_symbol}/sell"
        params = {"symbol": trade_symbol, "units": units}
        warning_log = f"Unable to get sell {units} units of good: {trade_symbol} from ship: {ship_symbol}"
        logging.info(
            f"Selling {units} units of {trade_symbol} from ship: {ship_symbol}"
        )
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res


class Contracts(Client):
    """Endpoints to handle contracts"""

    def deliver_contract(
        self,
        contract_id,
        ship_symbol,
        trade_symbol,
        units,
        raw_res=False,
        throttle_time=10,
    ):
        """Deliver cargo on a given contract.

        Args:
            ship_symbol (str): The symbol of the ship
            contract_id (str): Id of contract to deliver goods for
            trade_symbol (sre): Trade goods to deliver
            units (int): how many units to deliver

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ2NjQ0MjE-deliver-on-contract
        """
        endpoint = f"my/contracts/{contract_id}/deliver"
        params = {
            "shipSymbol": ship_symbol,
            "tradeSymbol": trade_symbol,
            "units": units,
        }
        warning_log = f"Unable to deliver trade goods for contract: {contract_id}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def list_contracts(self, throttle_time=10):
        """List all of your contracts.

        Args:

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5NDc4NTg-list-contracts
        """
        endpoint = f"my/contracts"
        warning_log = f"Unable to get a list of your contracts"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def get_contract(self, contract_id, throttle_time=10):
        """Get the details of a contract by ID.

        Args:
            contract_id (str): Id of contract to get the details for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/contracts/{contract_id}"
        warning_log = f"Unable to get details of contract: {contract_id}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def accept_contract(self, contract_id, throttle_time=10):
        """Accept a contract.

        Args:
            contract_id (str): ID of contract to accept

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5NTI5NjQ-accept-contract
        """
        endpoint = f"my/contracts/{contract_id}/accept"
        warning_log = f"Unable to accept contract: {contract_id}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def fulfill_contract(self, contract_id, throttle_time=10):
        """Fulfill a contract.

        Args:
            contract_id (str): ID of contract to fulfill

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/d4ff41c101af0-fulfill-contract
        """
        endpoint = f"my/contracts/{contract_id}/fulfill"
        warning_log = f"Unable to fulfill contract: {contract_id}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res


class Extract(Client):
    """Functions related to extracting resources from a waypoint"""

    def extract_resource(self, ship_symbol, survey={}, throttle_time=10):
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

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"my/ships/{ship_symbol}/extract"
        warning_log = f"Unable to extract resources: {ship_symbol}"
        if survey != {}:
            params = {"survey": survey}
        else:
            params = {}

        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def extraction_cooldown(self, ship_symbol, throttle_time=10):
        """Get the status of your last extraction.

        Args:
            ship_symbol (str): Symbol of ship to get status for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NDQ-extraction-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/extract"
        warning_log = f"Get the status of your last extraction: {ship_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def survey_waypoint(self, ship_symbol, throttle_time=10):
        """If you want to target specific yields for an extraction, you can survey a waypoint,
        such as an asteroid field, and send the survey in the body of the extract request.
        Each survey may have multiple deposits, and if a symbol shows up more than once,
        that indicates a higher chance of extracting that resource.

        Your ship will enter a cooldown between consecutive survey requests.
        Surveys will eventually expire after a period of time.
        Multiple ships can use the same survey for extraction.

        Args:
            ship_symbol (str): Symbol of ship to perform the survey

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NTI-survey-waypoint
        """
        endpoint = f"my/ships/{ship_symbol}/survey"
        warning_log = f"Unable to perform a survey of a waypoint: {ship_symbol}"
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def survey_cooldown(self, ship_symbol, throttle_time=10):
        """Executing a survey will initiate a cooldown for a number of seconds before you can call it again.
        This endpoint returns the details of your cooldown, or a 404 if there is no cooldown for the survey action.

        Args:
            ship_symbol (str): symbol of ship to check status of cooldown

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDQ5MzU0NTM-survey-cooldown
        """
        endpoint = f"my/ships/{ship_symbol}/survey"
        warning_log = f"Unable to check on status of cooldown for ship: {ship_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res


class Shipyard(Client):
    """Function specific to handling shipyard"""

    def purchase_ship(self, listing_id, throttle_time=10):
        """Purchase a ship

        Args:
            listing_id (str): The id of the shipyard listing you want to purchase.

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDc-purchase-ship
        """
        endpoint = f"my/ships"
        warning_log = f"Unable to purchase ship with listing id: {listing_id}"
        params = {"id": listing_id}
        res = self.generic_api_call(
            "POST",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
            params=params,
        )
        return res

    def list_shipyards(self, system_symbol, throttle_time=10):
        """Returns a list of all shipyards in a system.

        Args:
            system_symbol (str): symbol of system to get list of shipyards for

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDY-list-shipyards
        """
        endpoint = f"systems/{system_symbol}/shipyards"
        warning_log = f"Unable to view shipyards in system: {system_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def shipyard_details(self, system_symbol, waypoint_symbol, throttle_time=10):
        """Get details about a shipyard

        Args:
            system_symbol (str): Symbol of system shipyard is located in
            waypoint_symbol (str): Symbol of waypoint shipyeard is located in

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response

            API Link: https://spacetraders.stoplight.io/docs/spacetraders/b3A6NDUyNDAzMDQ-shipyard-details
        """
        endpoint = f"systems/{system_symbol}/shipyards/{waypoint_symbol}"
        warning_log = f"Unable to view shipyard in system: {system_symbol}, waypoint: {waypoint_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res

    def shipyard_listings(self, system_symbol, waypoint_symbol, throttle_time=10):
        """View ships available for purchase in shipyard

        Args:
            system_symbol (str): system shipyard is located in
            waypoint_symbol (str): waypoint shipyard is located in

            throttle_time (int, optional): How long to wait before attempting call again. Defaults to 10.

        Returns:
            dict: JSON response
        """
        endpoint = f"systems/{system_symbol}/shipyards/{waypoint_symbol}/ships"
        warning_log = f"Unable to view ships in shipyard in system: {system_symbol}, waypoint: {waypoint_symbol}"
        res = self.generic_api_call(
            "GET",
            endpoint,
            token=self.token,
            warning_log=warning_log,
            throttle_time=throttle_time,
        )
        return res


if __name__ == "__main__":
    pass
