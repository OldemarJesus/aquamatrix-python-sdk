from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest

from aquamatrix_simar import (
    AuthenticationError,
    GraphValue,
    NextReadingsInfo,
    ProtocolError,
    ReadingInfo,
    SimarClient,
)

LOGIN_PAGE = '<form><input value="login-token" name="__RequestVerificationToken"></form>'


@pytest.mark.asyncio
async def test_login_fetches_token_and_submits_credentials() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/Account/Login") and request.method == "GET":
            return httpx.Response(200, text=LOGIN_PAGE)
        if request.url.path.endswith("/Account/Login"):
            fields = parse_qs(request.content.decode(), keep_blank_values=True)
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
@pytest.mark.asyncio
async def test_invoice_methods_require_login() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(500))
    async with SimarClient("123456789", "secret", transport=transport) as client:
        with pytest.raises(AuthenticationError):
            await client.get_invoices()


@pytest.mark.asyncio
async def test_invoice_methods_are_disabled_without_sending_requests() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async with SimarClient("123456789", "secret", transport=httpx.MockTransport(handler)) as client:
        client._authenticated = True
        with pytest.raises(ProtocolError, match="temporarily disabled"):
            await client.get_invoices()
        with pytest.raises(ProtocolError, match="temporarily disabled"):
            await client.get_pending_invoices()

    assert requests == []


@pytest.mark.asyncio
async def test_get_only_portal_features_map_captured_response_shapes() -> None:
    responses = {
        "/SIMARnet/Billing/GetBillingInfo": {
            "InvoicesToPay": 1,
            "FailedInvoices": 0,
        },
        "/SIMARnet/ReadingsAndConsumptions/GetLastReadingInfo": {
            "LastReadingDate": "2026-10-15",
            "Type": "SIMAR",
            "Value": "459,000",
        },
        "/SIMARnet/ReadingsAndConsumptions/GetNextReadingsInfo": {
            "Company": "2026-11-20",
            "Client": "2026-11-20",
        },
        "/SIMARnet/Support/GetWaterShortagesInfo": False,
        "/SIMARnet/Billing/GetLastInvoiceGraph": [
            {"Label": "RECEITA SIMAR", "Value": 10.1834, "ValueDisplay": "€ 10,18"},
            {"Label": "IVA", "Value": 0.17, "ValueDisplay": "€ 0,17"},
        ],
        "/SIMARnet/Billing/GetBilledValuesGraph": [
            {"Label": "NOV-25", "Value": 54.77},
            {"Label": "DEZ-25", "Value": 47.84},
        ],
    }
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return httpx.Response(200, json=responses[request.url.path])

    async with SimarClient("123456789", "secret", transport=httpx.MockTransport(handler)) as client:
        client._authenticated = True
        assert await client.get_billing_summary() == {
            "invoices_to_pay": 1,
            "failed_invoices": 0,
        }
        assert await client.get_last_reading() == ReadingInfo(
            reading_date=date(2026, 10, 15), reading_type="SIMAR", value="459,000"
        )
        assert await client.get_next_readings() == NextReadingsInfo(
            company_date=date(2026, 11, 20), client_date=date(2026, 11, 20)
        )
        assert await client.get_water_shortages() is False
        assert await client.get_last_invoice_graph() == [
            GraphValue("RECEITA SIMAR", Decimal("10.1834"), "€ 10,18"),
            GraphValue("IVA", Decimal("0.17"), "€ 0,17"),
        ]
        assert await client.get_billed_values_graph() == [
            GraphValue("NOV-25", Decimal("54.77")),
            GraphValue("DEZ-25", Decimal("47.84")),
        ]

    assert requests == list(responses)