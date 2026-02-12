"""Utility module for exception handling."""

REPO_URL = "https://github.com/Niyada/bpmn-pnml-transformer-poc/issues"
GITHUB_MESSAGE = (
    f"Please open an issue at {REPO_URL} with your diagram "
    "if you need further assistance."
)


# Internal exceptions where details should not be exposed to users.
class PrivateInternalException(Exception):
    """Exception for internal errors that should not be exposed to users."""

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return f"We encountered an unkown issue.\n{GITHUB_MESSAGE}"


class InternalTransformationException(PrivateInternalException):
    """Exception raised for internal errors during transformation."""


# Known user facing exceptions.
class KnownException(Exception):
    """Base class for all known transformer exceptions."""

    def __init__(self, id: int, message: str) -> None:
        """Initialize a user-facing known exception with an ID and message.

        Args:
            id (int): The error ID.
            message (str): The error message.
        """
        self._message = message
        self._id = id
        super().__init__(message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        error_text = f"Error description: {self._message}\n{GITHUB_MESSAGE}"
        if self._id:
            error_text = f"[{self._id}] {error_text}"
        return error_text


class UnexpectedError(KnownException):
    """Exception raised for unexpected errors."""

    def __init__(self) -> None:
        """Initialize an unexpected error exception."""
        super().__init__(0, "Unkown error")


class NotSupportedBPMNElement(KnownException):
    """Exception raised for unsupported BPMN elements."""

    def __init__(self, element_names: str) -> None:
        """Initialize an exception for unsupported BPMN elements.

        Args:
            element_names (str): The names of unsupported BPMN elements.
        """
        super().__init__(1, f"BPMN element {element_names} not supported.")


class MissingEnvironmentVariable(KnownException):
    """Exception raised for missing environment variables."""

    def __init__(self, var_name: str) -> None:
        """Initialize an exception for a missing environment variable.

        Args:
            var_name (str): The name of the missing environment variable.
        """
        super().__init__(2, f"Env variable {var_name} not set!")


class TokenCheckUnsuccessful(KnownException):
    """Exception raised when a token check is unsuccessful."""

    def __init__(self) -> None:
        """Initialize a token check unsuccessful exception."""
        super().__init__(3, "Token check not successful")


class UnexpectedQueryParameter(KnownException):
    """Exception raised for unexpected query parameters."""

    def __init__(self, query_param: str) -> None:
        """Initialize an exception for an unexpected query parameter.

        Args:
            query_param (str): The unexpected query parameter.
        """
        super().__init__(4, f"Query parameter {query_param} wrong.")


class UnnamedLane(KnownException):
    """Exception raised for unnamed lanes."""

    def __init__(self) -> None:
        """Initialize an unnamed lane exception."""
        super().__init__(5, "Please name all of your lanes.")


class UnknownIntermediateCatchEvent(KnownException):
    """Exception raised for unknown intermediate catch events."""

    def __init__(self) -> None:
        """Initialize an unknown intermediate catch event exception."""
        super().__init__(6, "Wrong intermediate event type used!")


class WrongSubprocessDegree(KnownException):
    """Exception raised for incorrect subprocess degrees."""

    def __init__(self) -> None:
        """Initialize a wrong subprocess degree exception."""
        super().__init__(7, "Subprocess must have exactly one in and outgoing flow!")


class ORGatewayDetectionIssue(KnownException):
    """Exception raised for OR-Gateway detection issues."""

    def __init__(self) -> None:
        """Initialize an OR-Gateway detection issue exception."""
        super().__init__(8, "Could not find matching splits and joins for OR-Gateways")


class SubprocessWrongInnerSourceSinkDegree(KnownException):
    """Exception raised for incorrect inner source/sink degrees in subprocesses."""

    def __init__(self) -> None:
        """Initialize a subprocess wrong inner source/sink degree exception."""
        super().__init__(
            9,
            "Currently, source/sink in subprocess must have no incoming/outgoing arcs"
            " to convert to BPMN Start and End events.",
        )


class UnknownResourceOrganizationMapping(KnownException):
    """Exception raised for unknown resource organization mappings."""

    def __init__(self) -> None:
        """Initialize an unknown resource organization mapping exception."""
        super().__init__(10, "Resources must belong to the same organization.")


class InvalidInputXML(KnownException):
    """Exception raised for invalid input XML content."""

    def __init__(self) -> None:
        """Initialize an invalid input XML content exception."""
        super().__init__(11, "Seems like the input XML content is unsupported.")


class NoRequestTokensAvailable(KnownException):
    """Exception raised when there are no available Tokens for transformation request."""

    def __init__(self) -> None:
        """Initialize an no request tokens available exception."""
        super().__init__(14, "No request tokens available. Please try again later.")
