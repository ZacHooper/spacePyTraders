"""This module is all about getting the optimum trading routes.
Using the Bellman-Ford algorithm and Cost/Time/Volume value an optimum route can be determined for a given ship. 

Please note that this my calculation to find the "best" trading route. 
It may not actually be the most optimal route however, it is as close as I have
got it so far. 
"""

from decimal import Decimal
from SpacePyTraders import client
import pandas as pd
import datetime
import time
import math

def get_best_route(market_db, ship):
    # Get the current best trades across system
    current_market = get_current_market(market_db)
    bt = best_trades(all_trades(current_market, ship))
    # Prepare data for alogrithm
    graph = prepare_data_for_algorithm(bt)
    locs = current_market.location.unique()
    # Get the potential routes
    possible_routes = potential_routes(locs, graph)
    best_route = possible_routes.sort_values('weight').head(1)
    # Create a route guide for the best route
    route_guide = create_route_guide(bt, best_route.route.values[0])
    return route_guide

def get_location_data_from_market(current_market):
    locs = current_market.groupby('location').max()
    return locs[['x', 'y']].reset_index()

def all_trades_for_loc(current_market, symbol, ship):
    """Get the possible trades for a location. This includes adding a distance, time_to_fly and ctv column to the data to help analyse whether the trade is good or not. Returns a DataFrame with all the possible trades you could make from the destination provided

    Args:
        current_market (DataFrame): The snapshot of the market currently
        symbol (str): the symbol for the location you want the trades for
        ship (Ship): the ship object currently making this call. Required to calculate the time the ship would take to fly somewhere

    Returns:
        DataFrame: All the possible trades for the location specified
    """
    loc_market = current_market.loc[current_market.location == symbol]
    market_compare = loc_market.join(current_market.set_index('symbol'), on='symbol', how='inner', rsuffix="_to").reset_index()
    # Only select important features
    mc_clean = market_compare[['symbol', 'volumePerUnit', 'location', 'x', 'y', 'purchasePricePerUnit', 'location_to', 'x_to', 'y_to', 'sellPricePerUnit_to']].copy()
    mc_clean.rename(columns={"location":"from_loc", "x":"from_x", "y":"from_y", 
                             "location_to":"to_loc", "x_to": "to_x", "y_to":"to_y",
                             "sellPricePerUnit_to": "sellPricePerUnit"}, inplace=True)
    # Function for distance formula
    calc_distance = lambda from_x, to_x, from_y, to_y: round(
        math.sqrt(math.pow((to_x - from_x),2) + math.pow((to_y - from_y),2))
    )

    # Process Data
    apply_distance_calc = lambda row: calc_distance(row.from_x, row.to_x, row.from_y, row.to_y)
    mc_clean['profit'] = mc_clean.sellPricePerUnit - mc_clean.purchasePricePerUnit
    mc_clean['distance'] = mc_clean.apply(apply_distance_calc, axis=1)
    mc_clean['time_to_fly'] = round(mc_clean.distance * (2/ship.speed) + 59)
    mc_clean['ctv'] = mc_clean.profit / mc_clean.time_to_fly / mc_clean.volumePerUnit
    
    return mc_clean


def all_trades(current_market, ship):
    """Creates a large DataFrame with all the possible trades and their values that can be made in the entire system

    Args:
        current_market (DataFrame): snapshot of the most recent market data
        ship (Ship): the ship currently investigating the market. Need the ship's speed for time calculation

    Returns:
        DataFrame: A DataFrame containing all the possible trads in the system
    """
    trades = [all_trades_for_loc(current_market, symbol, ship) for symbol in current_market.location.unique()]
    return pd.concat(trades).reset_index().drop('index', axis=1)

def best_trades_per_loc(all_trades, symbol):
    idxs = all_trades.loc[all_trades.from_loc == symbol].groupby('to_loc').ctv.idxmax()
    return all_trades.loc[idxs]

def best_trades(all_trades):
    """Creates a large DataFrame with all the bests trades for each origin's possible destinations

    Args:
        current_market (DataFrame): snapshot of the most recent market data

    Returns:
        DataFrame: A DataFrame containing all the best trades you can make at each origin
    """
    trades = [best_trades_per_loc(all_trades, symbol) for symbol in all_trades.from_loc.unique()]
    return pd.concat(trades).reset_index().drop('index', axis=1)

def get_current_market_for_loc(market_db, symbol):
    """Gets the most recent market value for a specific location

    Args:
        market_db (DataFrame): The full marketplace database
        symbol (str): the symbol of the location you want to retrieve the current market for

    Returns:
        DataFrame: the most recent market data for the location specified
    """
    loc_current = market_db.loc[market_db.location == symbol]
    return loc_current.loc[loc_current.groupby('symbol').time.idxmax()]

def get_current_market(market_db):
    """Gets the most recent market value for each location

    Args:
        market_db (DataFrame): A dataframe of the full market db

    Returns:
        DataFrame: A snapshot of the current market prices
    """
    market_db.time = pd.to_datetime(market_db.time)
    trades = [get_current_market_for_loc(market_db, symbol) for symbol in market_db.location.unique()]
    recent_trades = pd.concat(trades)
    return recent_trades.drop(['uuid', 'tracker'], axis=1)

def prepare_data_for_algorithm(best_trades):
    """Create a dictionary from the trades in the format that the algorithm will accept.

    Each key in the dictionary will be an origin location. 
    Each location will contain another dictonary where the keys are the various destinarions it can trade to. 
    The values of these will be the best CTV value between the two locations

    eg 
    {
        "OE-PM" : {
            "OE-PM-TR": 2.234,
            "OE-BO": 0.342
        },
        "OE-BO": {
            "OE-CR": -1.21,
            "OE-NY": 2.333
        }
        ...
    }

    Args:
        all_trades (DataFrame): the dataframe containing all the current trades

    Returns:
        dict: a dictionary of all the best trades formatted for the alogrithm to handle
    """
    # Initialise the Dictionary
    paths = {}
    # Create a list of all the symbols
    from_locs = best_trades.from_loc.unique()
    # Get a logarithmic value of the CTV. If it's negative then make it 0 as we wouldn't make a trade where we lose money 
    set_value = lambda x: -Decimal(x).ln() if x > 0 else -Decimal(0).ln()
    # Loop through each symbol and create a dictionary containing the best trades to each location
    for loc in from_locs:
        # Get index of best trades to each location from the current origin location
        paths[loc] = {row.to_loc: set_value(row.ctv) for (index, row) in best_trades.loc[best_trades.from_loc == loc].iterrows()}
    return paths

def all_vertices(graph):
    """Return a set of all vertices in a graph.
    
    graph -- a weighted, directed graph.
    """
    vertices = set()
    for v in graph.keys():
        vertices.add(v)
        for u in graph[v].keys():
            vertices.add(u)
    return vertices

def is_edge(graph, tail, head):
    """Return if the edge (tail)->(head) is present
    in a graph.
    
    graph -- a weighted, directed graph.
    tail -- a vertex.
    head -- a vertex.
    """
    return (tail in graph) and (head in graph[tail])

class NoShortestPathError(Exception):
    pass

class NegativeCycleError(NoShortestPathError):
    def __init__(self, weight, cycle):
        self.weight = weight
        self.cycle = cycle

    def __str__(self):
        return f"Weight {self.weight}: {self.cycle}"

def shortest_path_bellman_ford(*, graph, start, end):
    """Find the shortest path from start to end in graph,
    using the Bellman-Ford algorithm.
    
    If a negative cycle exists, raise NegativeCycleError.
    If no shortest path exists, raise NoShortestPathError.
    """
    n = len(all_vertices(graph))

    dist = {}
    pred = {}

    def is_dist_infinite(v):
        return v not in dist

    def walk_pred(start, end):
        path = [start]
        v = start
        while v != end:
            v = pred[v]
            path.append(v)
        path.reverse()
        return path

    def find_cycle(start):
        nodes = []
        node = start
        while True:
            if node in nodes:
                cycle = [
                    node,
                    *reversed(nodes[nodes.index(node) :]),
                ]
                return cycle
            nodes.append(node)
            if node not in pred:
                break
            node = pred[node]

    dist[start] = 0

    # Relax approximations (n-1) times.

    for _ in range(n - 1):
        for tail in graph.keys():
            if is_dist_infinite(tail):
                continue
            for head, weight in graph[tail].items():
                alt = dist[tail] + weight
                if is_dist_infinite(head) or (
                    alt < dist[head]
                ):
                    dist[head] = alt
                    pred[head] = tail

    # Check for negative cycles.

    for tail in graph.keys():
        for head, weight in graph[tail].items():
            if tail not in dist:
                continue
            if (dist[tail] + weight) < dist[head]:
                cycle = find_cycle(tail)
                cycle_weight = sum(
                    graph[c_tail][c_head]
                    for (c_tail, c_head) in zip(
                        cycle, cycle[1:]
                    )
                )
                raise NegativeCycleError(
                    cycle_weight, cycle
                )

    # Build shortest path.

    if is_dist_infinite(end):
        raise NoShortestPathError

    best_weight = dist[end]
    best_path = walk_pred(end, start)

    return best_weight, best_path

def potential_routes(locs, graph):
    all_routes = []
    for l in locs:
        possible_routes = []
        for loc in locs:  
            try:
                possible_routes.append(shortest_path_bellman_ford(graph=graph, start=l, end=loc))
            except NoShortestPathError:
                print("Can't trade goods with " + loc)
        
        possible_return_routes = []
        for pr in possible_routes:
            try:
                possible_return_routes.append(shortest_path_bellman_ford(graph=graph, start=pr[1][-1], end=l))
            except NoShortestPathError:
                print("Can't trade goods with " + loc)

        combined_routes = []
        for i in range(len(possible_return_routes)):
            route = possible_routes[i][1] + possible_return_routes[i][1][1:]
            weight = possible_routes[i][0] + possible_return_routes[i][0]
            combined_routes.append((weight/len(route), route))
            
            
        all_routes = all_routes + combined_routes
    all_routes_df = pd.DataFrame(all_routes).rename(columns={0:"weight",1:"route"})
    return all_routes_df.loc[all_routes_df.weight > 0].drop_duplicates('weight')

def get_trade(best_trades, from_loc, to_loc):
    """Gets a the row of the best good to trade in that leg
    
    Parameters
        df : (DataFrame) : A DataFrame of the current best trades
        from_loc : (str) : The symbol of the origin location
        to_loc : (str) : the symbol of the to location
    """
    mask = (best_trades.from_loc == from_loc) & (best_trades.to_loc == to_loc)
    return best_trades.loc[mask]

def create_route_guide(best_trades, route):
    """Create a trading guide for the route provided. Provides the good to trade, the from/to, and the ctv

    Args:
        best_trades (DataFrame): A DataFrame of the current best trades
        best_route (list): a list containing symbols of locations in the route

    Returns:
        DataFrame: A DataFrame in order of the route containing all the information about the trades
    """
    return pd.concat(get_trade(best_trades, route[i], route[i+1]) for i in range(len(route) - 1)).reset_index().drop('index', axis=1)

def am_i_on_best_route(current_route, best_route):
    """Checks to see if the ship is on the best route

    Args:
        current_route (DataFrame): The ships current route
        best_route (DataFrame): The best route

    Return:
        bool : Whether the ship is on the best route or not
    """
    # Check if list sizes are the same
    if len(current_route) != len(best_route):
        return False
    
    # Check if all the from locations match
    if all(loc not in best_route.from_loc.values for loc in current_route.from_loc):
        return False

    return True


    