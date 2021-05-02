# 0.0.5 (2-May-21)
## Models
- Refactored model classes to use DataClass module
- Added new models: Cargo, Marketplace, Good, System

## Client
- Fixed bug where throttling wasn't being handled correctly

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
