# spaceTraders
 Playing Space Traders

  ## Todo
  ### Core
  - Better Exception handling
  - Create a constant filter method
    - Can handle equals, not equals, etc - likely add a third element to the tuple. 
  
  ### General
  - Track Total Credits - or at least equity so value of goods also containined on ships - and out of curiosity assests
  - Track Ship Count
  - Build out testing suite

  ### Traders
  - Handle multiple ship trading
  - Consider travel time when choosing location to fly
  - Handle when a good has no available units
  - Improve handle when user doesn't have enough credits

  ### Flight Paths
  - Update Flight Path DB to hold type of flight: ie Trading, or Travel, Scouting, etc
  - Update Flight Path DB to hold type of ship not manufacturer

  ### Tracker
  - Work out way to run constantly
  
  ### Analyis
  - Build an analysis pipeline

  ### Logs
  - Create database to track logs

## Changelog
- Created DB Handler Module
- Created Buy & Sell Order tables in DB
- Created Flight path table in DB
- Handle Grav III buying more than 300 units
- Handledish when not enough credits available for trade 


2021-04-22 16:27:12,337 - WARNING - Error: {'error': {'message': 'Ships can only place a sell order while docked.', 'code': 400}}
2021-04-22 16:27:12,338 - ERROR - Something broke the script. Code: 400 Error Message: Ships can only place a sell order while docked. 

2021-04-22 20:27:56,265 - WARNING - Something went wrong when hitting: POST https://api.spacetraders.io/users/JimHawkins/purchase-orders?shipId=cknr0wynw51684015s6wvq7q1th&good=FUEL&quantity=39 with parameters: {'shipId': 'cknr0wynw51684015s6wvq7q1th', 'good': 'FUEL', 'quantity': 39}
2021-04-22 20:27:56,265 - WARNING - Error: {'error': {'message': 'Failed to process request due to a conflict. You may be sending the same request multiple times. Please try again if necessary.', 'code': 409}}
2021-04-22 20:27:56,267 - ERROR - Something broke the script. Code: 409 Error Message: Failed to process request due to a conflict. You may be sending the same request multiple times. Please try again if necessary. 


### When trying to scrap a ship
Error 422: 
{
    "error": {
        "message": "You can not sell your ship here. You need to sell somewhere that has a shipyard.",
        "code": 42201
    }
}

### When claiming a user
{'error': {'message': 'Username has already been claimed.', 'code': 40901}} 409 error