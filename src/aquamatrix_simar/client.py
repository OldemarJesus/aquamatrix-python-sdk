"""Async HTTP client for the SIMARnet customer portal."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

import httpx

from aquamatrix_simar.errors import (
    AuthenticationError,
    ProtocolError,
    SessionExpiredError,
)
from aquamatrix_simar.models import Invoice

_DATE_PATTERN = re.compile(r"/Date\((-?\d+)(?:[+-]\d{4})?\)/")
_LOGIN_PATH = "/SIMARnet/Account/Login"
_INVOICE_COLUMNS = (
    ("ClientCode", "ClientCode"),
    ("DocumentTypeDisplay", "DocumentTypeId"),
    ("Year", "Year"),
    ("DocumentNumber", "DocumentNumber"),
    ("IssueDateDisplay", "IssueDate"),
    ("PaymentUntilDisplay", "PaymentUntil"),
    ("ValueDisplay", "Value"),
    ("PaymentDateDisplay", "PaymentDate"),
    ("Address", "Address"),
    ("HasElectronicInvoice", "HasElectronicInvoice"),
    ("Actions", "Actions"),
)


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
        limit: int = 100,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Invoice]:
        """Fetch one page of billing history, mapped to stable invoice objects."""
        self._require_authentication()
        if start < 0:
            raise ValueError("start must be zero or greater")
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        token = await self._get_current_token()
        form: dict[str, str] = {
            "draw": "1",
            "start": str(start),
            "length": str(limit),
            "search[value]": "",
            "search[regex]": "false",
            "type": "",
            "dateFrom": (date_from or date.today() - timedelta(days=365)).isoformat(),
            "dateTo": (date_to or date.today()).isoformat(),
            "__RequestVerificationToken": token,
        }
        form.update(_datatable_column_fields())

        try:
            response = await self._client.post(
                "/SIMARnet/Billing/GetInvoicesHistory",
                data=form,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
        except httpx.HTTPError as exc:
            raise ProtocolError("Could not fetch SIMAR invoice history") from exc

        if response.status_code in {401, 403} or _LOGIN_PATH in str(response.url):
            self._authenticated = False
            raise SessionExpiredError("SIMAR session expired; call login() again")
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProtocolError("SIMAR returned an invalid invoice-history response") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ProtocolError("Invoice-history response did not contain a data list")
        try:
            return [_parse_invoice(row) for row in payload["data"]]
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise ProtocolError("SIMAR returned an invoice with an invalid shape") from exc

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

    async def _get_current_token(self) -> str:
        try:
            response = await self._client.get("/SIMARnet/Billing")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SessionExpiredError("Could not load authenticated billing page") from exc
        token = _extract_token(response.text)
        if token is None:
            self._authenticated = False
            raise SessionExpiredError("Billing page no longer contains a session token")
        return token

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Client is closed")

    def _require_authentication(self) -> None:
        self._ensure_open()
        if not self._authenticated:
            raise AuthenticationError("Call and await login() before using this operation")


def _datatable_column_fields() -> dict[str, str]:
    fields: dict[str, str] = {}
    for index, (data_name, sort_name) in enumerate(_INVOICE_COLUMNS):
        prefix = f"columns[{index}]"
        fields[f"{prefix}[data]"] = data_name
        fields[f"{prefix}[name]"] = sort_name
        fields[f"{prefix}[searchable]"] = "true"
        fields[f"{prefix}[orderable]"] = "false"
        fields[f"{prefix}[search][value]"] = ""
        fields[f"{prefix}[search][regex]"] = "false"
    fields["order[0][column]"] = "4"
    fields["order[0][dir]"] = "desc"
    return fields


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


def _parse_invoice(row: Any) -> Invoice:
    if not isinstance(row, dict):
        raise TypeError("Invoice row must be an object")
    return Invoice(
        client_code=_optional_string(row.get("ClientCode")),
        document_number=str(row["DocumentNumber"]),
        document_type=str(row["DocumentTypeDisplay"]),
        year=int(row["Year"]),
        issue_date=_parse_date(row.get("IssueDateDisplay") or row.get("IssueDate")),
        payment_until=_parse_date(row.get("PaymentUntilDisplay") or row.get("PaymentUntil")),
        amount=Decimal(str(row["Value"])),
        state=str(row.get("StateDisplay", "")),
        payment_date=(
            _parse_date(row.get("PaymentDateDisplay") or row["PaymentDate"])
            if row.get("PaymentDateDisplay") or row.get("PaymentDate")
            else None
        ),
    )


def _parse_date(value: Any) -> date:
    if not isinstance(value, str):
        raise ValueError("Date field must be a string")
    match = _DATE_PATTERN.fullmatch(value)
    if match:
        return datetime.fromtimestamp(int(match.group(1)) / 1000, tz=UTC).date()
    return date.fromisoformat(value)


def _optional_string(value: Any) -> str | None:
    return str(value) if value is not None else None