# Aquamatrix SIMAR Python SDK

An async Python client for reading customer billing data from the SIMAR portal hosted by Aquamatrix. It manages the web session and anti-forgery tokens so integrations can work with typed Python objects instead of portal-specific HTML and form fields.

**Documentation:** [User guide and API reference](https://oldemarjesus.github.io/aquamatrix-python-sdk/)

This is an **unofficial** integration. It is not affiliated with or endorsed by SIMAR or Aquamatrix, and the website does not present a stable public API. Portal changes, additional authentication requirements, or access policies may affect compatibility.

## Requirements

- Python 3.14 or newer. Python does not designate a long-term-support release; this project targets the latest stable CPython release available at initial development.
- A SIMAR portal account.

## Install

```shell
python -m pip install aquamatrix-simar
```

Until the first PyPI release, install from the repository:

```shell
python -m pip install "git+https://github.com/OldemarJesus/aquamatrix-python-sdk.git"
```

## Usage

```python
import asyncio
import os

from aquamatrix_simar import SimarClient


async def main() -> None:
    async with SimarClient(os.environ["SIMAR_NIF"], os.environ["SIMAR_PASSWORD"]) as simar:
        await simar.login()
        summary = await simar.get_billing_summary()
        print(f"Portal says {summary['invoices_to_pay']} invoice(s) need payment")

        reading = await simar.get_last_reading()
        print("Last reading:", reading.reading_date, reading.value)

        for entry in await simar.get_billed_values_graph():
            print(entry.label, entry.value)


asyncio.run(main())
```

The SDK currently supports the observed GET-based billing summary, reading, shortage, and graph endpoints. Invoice history and pending-invoice methods are temporarily disabled because the portal's history endpoint requires POST and currently returns HTTP 417. This SDK does not initiate payments.

For Home Assistant, create and retain a client in the integration's coordinator lifecycle, refresh it asynchronously, and close it during unload. Do not log credentials, cookies, request bodies, or personal invoice data.

## Development

```shell
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src
```

See [PRD.md](PRD.md), [ARCH.md](ARCH.md), and [AGENTS.md](AGENTS.md) for product scope, design boundaries, and contributor guidance.

## Author and license

Copyright (c) 2026 Oldemar Jesus <oldemego@gmail.com>. Released under the MIT License; see [LICENSE](LICENSE).