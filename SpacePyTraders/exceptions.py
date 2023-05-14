from dataclasses import dataclass


@dataclass
class ThrottleException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@dataclass
class ServerException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@dataclass
class TooManyTriesException(Exception):
    message: str = "Has failed too many times to make API call. "


class RegisterAgentExistsError(Exception):
    """Is raised when the API returns the error code 4109"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ShipDeliverInvalidLocationError(Exception):
    """Is raised when the API returns the error code 4510"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ShipDeliverTermsError(Exception):
    """Is raised when the API returns the error code 4508"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    """Is raised when the API returns the error code 404"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AcceptContractNotAuthorizedError(Exception):
    """Is raised when the API returns the error code 4500"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AcceptContractConflictError(Exception):
    """Is raised when the API returns the error code 4501"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FulfillContractDeliveryError(Exception):
    """Is raised when the API returns the error code 4502"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ContractDeadlineError(Exception):
    """Is raised when the API returns the error code 4503"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ContractFulfilledError(Exception):
    """Is raised when the API returns the error code 4504"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MarketNotFoundError(Exception):
    """Is raised when the API returns the error code 4603"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def which_exception(error: dict) -> Exception:
    """Checks the error returned by the Space Traders API and returns the appropriate exception

    Args:
        error (dict): The error returned by the Space Traders API

    Returns:
        Exception: The appropriate exception
    """
    match error["code"]:
        case 4109:
            return RegisterAgentExistsError(error)
        case 429:
            return ThrottleException(error)
        case 404:
            return ResourceNotFoundError(error)
        case 4500:
            return AcceptContractNotAuthorizedError(error)
        case 4501:
            return AcceptContractConflictError(error)
        case 4502:
            return FulfillContractDeliveryError(error)
        case 4503:
            return ContractDeadlineError(error)
        case 4504:
            return ContractFulfilledError(error)
        case 4508:
            return ShipDeliverTermsError(error)
        case 4510:
            return ShipDeliverInvalidLocationError(error)
        case 4603:
            return MarketNotFoundError(error)
        case 5000:
            return ServerException(error)
        case _:
            return Exception(error)
