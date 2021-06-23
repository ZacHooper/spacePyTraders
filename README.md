# SpacePyTraders

The Python SDK to interact with the [Space Traders API](https://spacetraders.io/). 

Read the documentation here: https://spacetraders.readthedocs.io/en/latest/

Space Traders is a great way to learn a practice coding. I highly recommend having a go at using the Requests library and interacting with the API yourself as practice but you can install this library to skip the boring work of coding for each API endpoint. 

## Install

`pip install SpacePyTraders`

## Getting Started
The first installment of this library provides a nice way to use Python and interact with the API without needed to code all the request calls. 

Using the `Api` class provided you can access all the currently possible endpoints of the API. The structure of the classes are organised the same as the Space Traders API. So if you're not sure what class to look under check the docs [here](https://spacetraders.readthedocs.io/en/latest/) or the Space Trader's API [here](https://api.spacetraders.io/).

```python
from SpacePyTraders import client

USERNAME = "YOUR USERNAME"
TOKEN = "YOUR TOKEN"

api = client.Api(USERNAME,TOKEN)

print(api.account.info())

>>> 
{
    "user": {
        "username": "JimHawkins",
        "credits": 0,
        "ships": [],
        "loans": []
    }
}
```
