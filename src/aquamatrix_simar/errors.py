"""Exceptions exposed by the SIMAR client."""


class SimarError(Exception):
    """Base exception for SIMAR client errors."""


class AuthenticationError(SimarError):
    """Credentials were rejected or the login flow could not be completed."""


class SessionExpiredError(AuthenticationError):
    """The authenticated web session is no longer valid."""


class ProtocolError(SimarError):
    """Aquamatrix returned an unexpected response or changed its web protocol."""