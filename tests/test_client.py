from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest

from aquamatrix_simar import AuthenticationError, Invoice, SimarClient

LOGIN_PAGE = '<form><input value="login-token" name="__RequestVerificationToken"></form>'
INVOICE_ROW = {
    "ClientCode": "12345678",
    "DocumentTypeDisplay": "Fatura",
    "DocumentNumber": "INV-2026-01",
    "Year": 2026,
    "IssueDateDisplay": "2026-10-22",
    "PaymentUntilDisplay": "2026-11-11",
    "Value": 10.39,
    "StateDisplay": "Em Cobrança",
    "PaymentDate": None,
}


@pytest.mark.asyncio
async def test_login_fetches_token_and_submits_credentials() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/Account/Login") and request.method == "GET":
            return httpx.Response(200, text=LOGIN_PAGE)
        if request.url.path.endswith("/Account/Login"):
            fields = parse_qs(request.content.decode())
            assert fields["__RequestVerificationToken"] == ["login-token"]
            assert fields["UserCode"] == ["123456789"]
            assert fields["Password"] == ["secret"]
            return httpx.Response(302, headers={"Location": "/SIMARnet/"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with SimarClient(
        "123456789",
        "secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        await client.login()
        assert client.is_authenticated
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_get_pending_invoices_maps_portal_values() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("GetInvoicesHistory"):
            fields = parse_qs(request.content.decode())
            assert "__RequestVerificationToken" not in fields
            assert fields["columns[5][data]"] == ["PaymentUntilDisplay"]
            assert fields["columns[7][orderable]"] == ["false"]
            assert fields["columns[8][orderable]"] == ["true"]
            assert fields["columns[9][orderable]"] == ["true"]
            assert fields["columns[10][orderable]"] == ["false"]
            assert fields["length"] == ["100"]
            assert fields["order[0][column]"] == ["0"]
            return httpx.Response(200, json={"data": [INVOICE_ROW]})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with SimarClient(
        "123456789",
        "secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        client._authenticated = True
        invoices = await client.get_pending_invoices()

    assert invoices == [
        Invoice(
            client_code="12345678",
            document_number="INV-2026-01",
            document_type="Fatura",
            year=2026,
            issue_date=date(2026, 10, 22),
            payment_until=date(2026, 11, 11),
            amount=Decimal("10.39"),
            state="Em Cobrança",
            payment_date=None,
        )
    ]


@pytest.mark.asyncio
async def test_pending_invoice_filter_excludes_paid_and_unknown_states() -> None:
    rows = [
        INVOICE_ROW,
        {
            **INVOICE_ROW,
            "DocumentNumber": "paid",
            "StateDisplay": "Paga",
            "PaymentDate": "/Date(1794355200000)/",
        },
        {**INVOICE_ROW, "DocumentNumber": "unknown", "StateDisplay": "Anulada"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("GetInvoicesHistory"):
            return httpx.Response(200, json={"data": rows})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with SimarClient("123456789", "secret", transport=httpx.MockTransport(handler)) as client:
        client._authenticated = True
        invoices = await client.get_pending_invoices()

    assert [invoice.document_number for invoice in invoices] == ["INV-2026-01"]


@pytest.mark.asyncio
async def test_invoice_methods_require_login() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(500))
    async with SimarClient("123456789", "secret", transport=transport) as client:
        with pytest.raises(AuthenticationError):
            await client.get_invoices()


@pytest.mark.asyncio
async def test_invoice_history_does_not_require_billing_page_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("GetInvoicesHistory"):
            return httpx.Response(200, json={"data": []})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with SimarClient("123456789", "secret", transport=httpx.MockTransport(handler)) as client:
        client._authenticated = True
        invoices = await client.get_invoices()

    assert invoices == []
    assert len(requests) == 1
    assert requests[0].url.path.endswith("GetInvoicesHistory")