"""Async HTTP client for the SIMARnet customer portal."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from aquamatrix_simar.errors import (
    AuthenticationError,
    ProtocolError,
)
from aquamatrix_simar.models import GraphValue, Invoice, NextReadingsInfo, ReadingInfo

_LOGIN_PATH = "/SIMARnet/Account/Login"


class SimarClient:
    """Authenticated async client for SIMAR customer billing.

    Use as an async context manager to close the underlying HTTP session:

        async with SimarClient(nif, password) as client:
            await client.login()
            invoices = await client.get_pending_invoices()
    """

    def __init__(
        self,
        nif: str,
        password: str,
        *,
        base_url: str = "https://www.aquamatrix.pt",
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not nif.strip():
            raise ValueError("NIF must not be empty")
        if not password:
            raise ValueError("Password must not be empty")
        self._nif = nif.strip()
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": "aquamatrix-simar-python/0.1.0"},
        )
        self._authenticated = False
        self._closed = False

    @property
    def is_authenticated(self) -> bool:
        """Whether this client currently has an authenticated session."""
        return self._authenticated

    async def __aenter__(self) -> SimarClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP session."""
        if not self._closed:
            await self._client.aclose()
            self._closed = True
            self._authenticated = False

    async def login(self) -> None:
        """Authenticate using the portal's current anti-forgery token."""
        self._ensure_open()
        self._authenticated = False
        try:
            page = await self._client.get(_LOGIN_PATH)
            page.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthenticationError("Could not load the SIMAR login page") from exc

        token = _extract_token(page.text)
        if token is None:
            raise ProtocolError("Login page did not contain an anti-forgery token")

        try:
            response = await self._client.post(
                _LOGIN_PATH,
                data={
                    "__RequestVerificationToken": token,
                    "UserCode": self._nif,
                    "Password": self._password,
                    "RememberMe": "false",
                },
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError("SIMAR login request failed") from exc

        if response.status_code not in {302, 303}:
            raise AuthenticationError("SIMAR rejected the supplied credentials")

        destination = urljoin(str(response.request.url), response.headers.get("location", ""))
        if "/SIMARnet/" not in destination or destination.rstrip("/").endswith(_LOGIN_PATH):
            raise AuthenticationError("SIMAR login did not redirect to the customer portal")
        self._authenticated = True

    async def get_pending_invoices(self) -> list[Invoice]:
        """Return invoice records not marked as paid by SIMAR."""
        return [invoice for invoice in await self.get_invoices() if invoice.is_pending]

    async def get_invoices(
        self,
        *,
        start: int = 0,
        limit: int = 5,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Invoice]:
        """Invoice history is temporarily disabled while portal POSTs are investigated."""
        self._require_authentication()
        if start < 0:
            raise ValueError("start must be zero or greater")
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        raise ProtocolError(
            "Invoice history is temporarily disabled while SIMAR POST behavior is investigated"
        )

    async def get_billing_summary(self) -> dict[str, int]:
        """Return portal invoice counts (invoices to pay and failed invoices)."""
        self._require_authentication()
        try:
            response = await self._client.get("/SIMARnet/Billing/GetBillingInfo")
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProtocolError("Could not fetch SIMAR billing summary") from exc
        if not isinstance(payload, dict):
            raise ProtocolError("SIMAR returned an invalid billing summary")
        try:
            return {
                "invoices_to_pay": int(payload["InvoicesToPay"]),
                "failed_invoices": int(payload["FailedInvoices"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError("Billing summary was missing expected counts") from exc

    async def get_last_reading(self) -> ReadingInfo:
        """Return the latest reading reported by the portal."""
        payload = await self._get_json(
            "/SIMARnet/ReadingsAndConsumptions/GetLastReadingInfo",
            "Could not fetch the latest SIMAR reading",
        )
        if not isinstance(payload, dict):
            raise ProtocolError("SIMAR returned an invalid latest-reading response")
        try:
            return ReadingInfo(
                reading_date=date.fromisoformat(payload["LastReadingDate"]),
                reading_type=str(payload["Type"]),
                value=str(payload["Value"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError("Latest-reading response was missing expected fields") from exc

    async def get_next_readings(self) -> NextReadingsInfo:
        """Return scheduled company and customer reading dates."""
        payload = await self._get_json(
            "/SIMARnet/ReadingsAndConsumptions/GetNextReadingsInfo",
            "Could not fetch the next SIMAR reading dates",
        )
        if not isinstance(payload, dict):
            raise ProtocolError("SIMAR returned an invalid next-readings response")
        try:
            return NextReadingsInfo(
                company_date=date.fromisoformat(payload["Company"]),
                client_date=date.fromisoformat(payload["Client"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError("Next-readings response was missing expected dates") from exc

    async def get_water_shortages(self) -> bool:
        """Return whether the portal reports a water shortage."""
        payload = await self._get_json(
            "/SIMARnet/Support/GetWaterShortagesInfo",
            "Could not fetch water-shortage information",
        )
        if not isinstance(payload, bool):
            raise ProtocolError("SIMAR returned an invalid water-shortage response")
        return payload

    async def get_last_invoice_graph(self) -> list[GraphValue]:
        """Return the component values displayed for the latest invoice graph."""
        return await self._get_graph_values("/SIMARnet/Billing/GetLastInvoiceGraph")

    async def get_billed_values_graph(self) -> list[GraphValue]:
        """Return the portal's historical billed values graph."""
        return await self._get_graph_values("/SIMARnet/Billing/GetBilledValuesGraph")

    async def _get_graph_values(self, path: str) -> list[GraphValue]:
        payload = await self._get_json(path, "Could not fetch SIMAR billing graph")
        if not isinstance(payload, list):
            raise ProtocolError("SIMAR returned an invalid billing graph response")
        if not all(isinstance(item, dict) for item in payload):
            raise ProtocolError("Billing graph contained an invalid item")
        try:
            return [
                GraphValue(
                    label=str(item["Label"]),
                    value=Decimal(str(item["Value"])),
                    value_display=(
                        str(item["ValueDisplay"]) if item.get("ValueDisplay") is not None else None
                    ),
                )
                for item in payload
            ]
        except (KeyError, TypeError, InvalidOperation) as exc:
            raise ProtocolError("Billing graph contained an invalid item") from exc

    async def _get_json(self, path: str, error_message: str) -> object:
        self._require_authentication()
        try:
            response = await self._client.get(path)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProtocolError(error_message) from exc

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Client is closed")

    def _require_authentication(self) -> None:
        self._ensure_open()
        if not self._authenticated:
            raise AuthenticationError("Call and await login() before using this operation")


class _TokenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.token: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "input":
            return
        attributes = dict(attrs)
        if attributes.get("name") == "__RequestVerificationToken":
            self.token = attributes.get("value")


def _extract_token(html: str) -> str | None:
    parser = _TokenParser()
    parser.feed(html)
    return parser.token

