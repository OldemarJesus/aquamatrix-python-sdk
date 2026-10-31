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

        reading = await client.get_last_reading()
        print("Last reading:", reading.reading_date, reading.value)

        billed_values = await client.get_billed_values_graph()
        for entry in billed_values:
            print(entry.label, entry.value)


asyncio.run(main())
```

The SDK currently exposes the confirmed GET-based billing summary, reading dates, water-shortage flag, and billing graph data. Invoice history and pending-invoice methods are temporarily disabled because they require a POST request that currently returns HTTP 417.

The client owns its HTTP session and cookie jar. Use `async with` or call `await client.aclose()` when finished. A session-expired response raises `SessionExpiredError`; call `login()` again when appropriate.