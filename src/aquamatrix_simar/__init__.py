"""Async client for SIMAR customer accounts hosted by Aquamatrix."""

from aquamatrix_simar.client import SimarClient
from aquamatrix_simar.errors import (
    AuthenticationError,
    ProtocolError,
    SessionExpiredError,
    SimarError,
)
from aquamatrix_simar.models import GraphValue, Invoice, NextReadingsInfo, ReadingInfo

__all__ = [
    "AuthenticationError",
    "GraphValue",
    "Invoice",
    "NextReadingsInfo",
    "ProtocolError",
    "ReadingInfo",
    "SessionExpiredError",
    "SimarClient",
    "SimarError",
]

__version__ = "0.2.0"