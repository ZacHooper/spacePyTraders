# 0.0.5 (2-May-21)
## Features🥁
- **Automatic throttling** - Previously throttling was automatically handled by recognising the throttle response from the Space Traders API and then pausing and retrying the call again. That method was considered bad practice as it allowed a user to spam the Space Trader API with many uncessary requests. Now a rate limit is built into the SDK to limit the amount of _throttled_ requests to the Space Trader API. There should be no difference in performance from the user's perspective but there will be many less throttled requests to the Space Trader API. 
- **Added Models module** -The models module contains models for common objects in the Space Traders Universe. Create Ship and access it's information easier and cleaner using dot notation

### Class Specific Updates
#### Api
- Moved claim token function into Api class as a method

#### Structures
- Updated `Structure.get_structure()` function to allow for defining if structure is owned by the user or not
- Updated `Structure.deposit_goods()` function to allow for defining if structure is owned by the user or not

#### Systems
- Added endpoint to get available ships in a given system
- Added endpoint to get a specific system
- Added endpoint to get docked ships in a system

#### Warp Jump
- Created a warp jump class to hold the `attempt_jump()` endpoint

#### Types
- Created a Types class to hold the types related endpoints
- Added endpoint to get all available goods
- Updated available loans endpoint to use `type/` and moved from Loans class to Types class
- Added endpoint to get all available structures
- Added endpoint to get info on all available ships - Note this is different to the previous `get_available_ships` as this endpoint does not tell you where the ship types are located in the universe

#### Account
- Created the Account class to hold user account related endpoints
- Updated the `get_user_info()` method to be in the Account class rather than the User class

## Bug Fixes 🐛
- Fixed appropriate endpoints to use `my/`
- Fixed appropriate endpoints to remove `game/`
- Fixed claim token endpoint
- Fixed transfer cargo endpoint to use `POST` HTTP method instead of `PUT`
- Fixed jettison cargo endpoint to use `POST` HTTP method instead of `PUT`

# 0.0.4 (29-Apr-21)
## Models
### Ship
- Fixed bug where location, x, y, & flightplanId weren't being set when they were present.

## Client
- Fixed bug where throttling wasn't being handled correctly

# 0.0.3 (27-Apr-21)

## Models
- Added the Ship, User, Location & Loan models. 

## Bug Fixes
- Fixed when an Api is created without a token the auto-generated token doesn't get applied to all the other properties. This now happens
- Add the optional argument `type` to the locations.get_system_locations() method. You can new filter the returned locations by their type. 
