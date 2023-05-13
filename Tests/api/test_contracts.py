import pytest
import responses
import json
from SpacePyTraders.client import Contracts, Api
from SpacePyTraders.exceptions import (
    ShipDeliverInvalidLocationError,
    ShipDeliverTermsError,
    ResourceNotFoundError,
    AcceptContractNotAuthorizedError,
    AcceptContractConflictError,
    FulfillContractDeliveryError,
    ContractDeadlineError,
    ContractFulfilledError,
)
from Tests.fixtures import api, mock_endpoints, mock_responses, BASE_URL


@pytest.mark.v2
def test_contracts_init(api):
    assert (
        Contracts(token="12345").token == "12345"
    ), "Did not set the token attribute correctly"
    assert isinstance(Contracts(token="12345"), Contracts)
    assert isinstance(api.contracts, Contracts)


### Deliver Contract Tests ###
@pytest.mark.v2
def test_contracts_deliver_contract(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Test the deliver_contract method working"""
    contract_id = "XYZ"
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/{contract_id}/deliver",
        json=mock_responses["deliver_on_contract"],
        status=200,
    )
    r = api.contracts.deliver_contract(contract_id, "HMAS-1", "IRON_ORE", 5)
    assert mock_endpoints.calls[0].request.body == json.dumps(
        {
            "shipSymbol": "HMAS-1",
            "tradeSymbol": "IRON_ORE",
            "units": 5,
        }
    )
    assert isinstance(r, dict)


@pytest.mark.v2
def test_contracts_deliver_contract_invalid_location(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Test the deliver_contract method working"""
    contract_id = "XYZ"
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/{contract_id}/deliver",
        json={
            "error": {
                "message": "Wrong location specified to deliver contract",
                "code": 4510,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(ShipDeliverInvalidLocationError):
        r = api.contracts.deliver_contract(contract_id, "HMAS-1", "IRON_ORE", 5)


@pytest.mark.v2
def test_contracts_deliver_contract_invalid_terms(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Test the deliver_contract method working"""
    contract_id = "XYZ"
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/{contract_id}/deliver",
        json={
            "error": {
                "message": "Wrong location specified to deliver contract",
                "code": 4508,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(ShipDeliverTermsError):
        r = api.contracts.deliver_contract(contract_id, "HMAS-1", "IRON_ORE", 5)


### List Contract Tests ###
@pytest.mark.v2
def test_contracts_list_contracts(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}my/contracts",
        json=mock_responses["list_contracts"],
        status=200,
    )
    r = api.contracts.list_contracts()
    assert isinstance(r, dict)
    assert mock_endpoints.calls[0].request.params == {}
    assert mock_endpoints.calls[0].request.url == f"{BASE_URL}my/contracts"


### Get Contract Tests ###
@pytest.mark.v2
def test_contracts_get_contract(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}my/contracts/XYZ",
        json=mock_responses["get_contract"],
        status=200,
    )
    r = api.contracts.get_contract("XYZ")
    assert isinstance(r, dict)
    assert mock_endpoints.calls[0].request.params == {}
    assert mock_endpoints.calls[0].request.url == f"{BASE_URL}my/contracts/XYZ"


@pytest.mark.v2
def test_contracts_get_contract_not_found(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.GET,
        f"{BASE_URL}my/contracts/XYZ",
        json={
            "error": {
                "message": "Resource with the given identifier does not exist.",
                "code": 404,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(ResourceNotFoundError):
        r = api.contracts.get_contract("XYZ")


### Accept Contract Tests ###
@pytest.mark.v2
def test_contracts_accept_contracts(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/accept",
        json=mock_responses["accept_contract"],
        status=200,
    )
    r = api.contracts.accept_contract("XYZ")
    assert isinstance(r, dict)
    assert mock_endpoints.calls[0].request.url == f"{BASE_URL}my/contracts/XYZ/accept"


@pytest.mark.v2
def test_contracts_accept_contracts_not_found(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/accept",
        json={
            "error": {
                "message": "Resource with the given identifier does not exist.",
                "code": 404,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(ResourceNotFoundError):
        r = api.contracts.accept_contract("XYZ")


@pytest.mark.v2
def test_contracts_accept_contracts_not_authorised(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/accept",
        json={
            "error": {
                "message": "Resource with the given identifier does not exist.",
                "code": 4500,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(AcceptContractNotAuthorizedError):
        r = api.contracts.accept_contract("XYZ")


@pytest.mark.v2
def test_contracts_accept_contracts_conflict(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/accept",
        json={
            "error": {
                "message": "Resource with the given identifier does not exist.",
                "code": 4501,
                "data": {},
            }
        },
        status=200,
    )
    with pytest.raises(AcceptContractConflictError):
        r = api.contracts.accept_contract("XYZ")


### Fulfull Contract Tests ###
@pytest.mark.v2
def test_contracts_fulfill_contracts(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/fulfill",
        json=mock_responses["fulfill_contract"],
        status=200,
    )
    r = api.contracts.fulfill_contract("XYZ")
    assert isinstance(r, dict)
    assert mock_endpoints.calls[0].request.url == f"{BASE_URL}my/contracts/XYZ/fulfill"


# fulfillContractDeliveryError
def test_contracts_fulfill_contracts_delivery_error(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Check that the fulfullContractDeliveryError is raised when not all of the items are delivered for the contract"""
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/fulfill",
        json={
            "error": {
                "message": "Not all items were delivered for the contract.",
                "code": 4502,
            }
        },
        status=200,
    )
    with pytest.raises(FulfillContractDeliveryError):
        r = api.contracts.fulfill_contract("XYZ")


# contractDeadlineError
def test_contracts_fulfill_contracts_deadline_error(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Check that the contractDeadlineError is raised when the contract deadline has passed"""
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/fulfill",
        json={
            "error": {
                "message": "The contract deadline has passed.",
                "code": 4503,
            }
        },
        status=200,
    )
    with pytest.raises(ContractDeadlineError):
        r = api.contracts.fulfill_contract("XYZ")


# contractFulfilledError
def test_contracts_fulfill_contracts_fulfilled_error(
    api: Api, mock_endpoints: responses.RequestsMock, mock_responses: dict
):
    """Check that the contractFulfilledError is raised when the contract has already been fulfilled"""
    mock_endpoints.add(
        responses.POST,
        f"{BASE_URL}my/contracts/XYZ/fulfill",
        json={
            "error": {
                "message": "The contract has already been fulfilled.",
                "code": 4504,
            }
        },
        status=200,
    )
    with pytest.raises(ContractFulfilledError):
        r = api.contracts.fulfill_contract("XYZ")
