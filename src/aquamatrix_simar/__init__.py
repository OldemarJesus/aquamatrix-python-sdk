"""Async client for SIMAR customer accounts hosted by Aquamatrix."""

from aquamatrix_simar.client import SimarClient
from aquamatrix_simar.errors import (
    AuthenticationError,
    ProtocolError,
    SessionExpiredError,
    SimarError,
)
from aquamatrix_simar.models import Invoice

__all__ = [
    "AuthenticationError",
    "Invoice",
    "ProtocolError",
    "SessionExpiredError",
    "SimarClient",
    "SimarError",
]

__version__ = "0.1.0"