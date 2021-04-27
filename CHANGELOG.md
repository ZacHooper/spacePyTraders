# 0.0.3 (27-Apr-21)

## Models
- Added the Ship, User, Location & Loan models. 

## Bug Fixes
- Fixed when an Api is created without a token the auto-generated token doesn't get applied to all the other properties. This now happens
- Add the optional argument `type` to the locations.get_system_locations() method. You can new filter the returned locations by their type. 
