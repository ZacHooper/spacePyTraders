from SpacePyTraders.models import *
from uuid import uuid4
import pandas as pd
from dataclasses import asdict
from datetime import datetime

def update_market(api, symbol, reason, add_to_db=None):
    """Gets the marketplace for a location and adds it to the marketplace_tracker table in the DB

    Args:
        api (Api): API object to make calls to the Space Traders API
        symbol (str): Symbol of the location to get the marketplace for. Eg: "OE-PM"
        reason (str): What triggered this market update. Eg. Trader ship or tracker
        add_to_db (func, optional): A function that takes a dataframe and adds it's data to your database

    If using a function to add to your database the following fields will be in the DataFrame provided to the function:
        - uuid (str) : a unique ID for each record in the DF
        - time (dt) : the current time of when the market data was taken
        - tracker (str) : what the ship's role is. eg: trader or scout ship
        - location (str) : the symbol for the location of the current market
        - x (int) : the x co-ordinate of the market
        - y (int) : the y co-ordinate of the market
        - symbol (str) : the symbol of the good
        - volumePerUnit (int) : the volume of the good
        - pricePerUnit (int) : the mean of the purchase & sell price of the good 
        - spread (int) : the spread of the good
        - purchasePricePerUnit (int) : the price the good can be bought at
        - sellPricePerUnit (int) : the price the good can be sold at
        - quantityAvailable (int) : how many units of the good is available

    Returns:
        DataFrame: A DataFrame with the current location's market outlook
    """
    # Make API Call for marketplace
    market = Marketplace(**api.locations.get_marketplace(symbol)['location'])
    # Convert to DF
    market_df = pd.DataFrame([asdict(good) for good in market.marketplace])
    # Add details about the location to each good record
    create_uuids = lambda x: [str(uuid4()) for i in range(x)]
    market_df['uuid'] = create_uuids(len(market_df))
    market_df['location'] = market.symbol
    market_df['x'] = market.x
    market_df['y'] = market.y
    market_df['time'] = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")
    market_df['tracker'] = reason
    # Write to DB
    if add_to_db:
        add_to_db(market_df)
    return market_df