Welcome to SpacePyTraders's documentation!
==========================================

#############
Client Module
#############

The client is what provides easy pythonic interaction with the Space Traders API. 
Interact with the API with better human readable code rather than convoluted requests.

.. automodule:: SpacePyTraders.client
   :members:

Api
########    
.. autoclass:: SpacePyTraders.client.Api
   :members:
   :special-members: __init__

Client
########    
.. autoclass:: SpacePyTraders.client.Client
    :members:

Account
#######    
.. autoclass:: SpacePyTraders.client.Account
   :members:

Flight Plans
############    
.. autoclass:: SpacePyTraders.client.FlightPlans
   :members:

Game
#### 
.. autoclass:: SpacePyTraders.client.Game
   :members:

Loans
#####
.. autoclass:: SpacePyTraders.client.Loans
   :members:

Locations
#########
.. autoclass:: SpacePyTraders.client.Locations
   :members:

Marketplace
###########
.. autoclass:: SpacePyTraders.client.Marketplace
   :members:

PurchaseOrders
##############
.. autoclass:: SpacePyTraders.client.PurchaseOrders
   :members:

SellOrders
##########
.. autoclass:: SpacePyTraders.client.SellOrders
   :members:

Ships
##########
.. autoclass:: SpacePyTraders.client.Ships
   :members:

Structures
##########
.. autoclass:: SpacePyTraders.client.Structures
   :members:

Systems
##########
.. autoclass:: SpacePyTraders.client.Systems
   :members:

Users
##########
.. autoclass:: SpacePyTraders.client.Users
   :members:

Types
##########
.. autoclass:: SpacePyTraders.client.Types
   :members:

Warp Jumps
##########
.. autoclass:: SpacePyTraders.client.WarpJump
   :members:

#############
Models Module
#############

Models provides common objects in the Space Trader Universe. Access a ships speed with dot notation rather than convoluted JSON manipulation. 

test

.. code-block:: python

   from models import Ship 
   ...
   ship = Ship(api.ships.get_ship('12345'))
   print(ship.manufacturer)
   >>> Jackshaw

.. automodule:: SpacePyTraders.models
   :members:

User
##########
.. autoclass:: SpacePyTraders.models.User
   :members:

Ship
##########
.. autoclass:: SpacePyTraders.models.Ship
   :members:

Cargo
##########
.. autoclass:: SpacePyTraders.models.Cargo
   :members:

Loan
##########
.. autoclass:: SpacePyTraders.models.Loan
   :members:

Location
##########
.. autoclass:: SpacePyTraders.models.Location
   :members:

Good
##########
.. autoclass:: SpacePyTraders.models.Good
   :members:

System
##########
.. autoclass:: SpacePyTraders.models.System
   :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
