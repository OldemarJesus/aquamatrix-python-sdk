# Quick Start

Keep credentials outside source control, such as in environment variables supplied by your application or secret manager.

```python
import asyncio
import os

from aquamatrix_simar import SimarClient


async def main() -> None:
    async with SimarClient(
        os.environ["SIMAR_NIF"],
        os.environ["SIMAR_PASSWORD"],
    ) as client:
        await client.login()

        summary = await client.get_billing_summary()
        print("Invoices to pay:", summary["invoices_to_pay"])

        for invoice in await client.get_pending_invoices():
            print(
                invoice.document_number,
                invoice.amount,
                invoice.issue_date,
                invoice.payment_until,
            )


asyncio.run(main())
```

`get_invoices()` returns one page and accepts `start`, `limit`, `date_from`, and `date_to`. The default date range covers the recent year. Amounts are `Decimal` and calendar fields are `datetime.date` objects.

The client owns its HTTP session and cookie jar. Use `async with` or call `await client.aclose()` when finished. A session-expired response raises `SessionExpiredError`; call `login()` again when appropriate.