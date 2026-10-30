# Agent Guide

## Project intent

This repository is an unofficial async Python SDK for reading SIMAR customer data from the Aquamatrix portal. Its primary consumers are independent integrations such as Home Assistant and MCP servers. Keep the public interface stable, typed, read-only, and independent from those consumer frameworks.

## Required practices

- Read `PRD.md` and `ARCH.md` before changing scope or architecture.
- Keep portal-specific HTTP paths, HTML token parsing, form fields, and response mapping inside `src/aquamatrix_simar/client.py`.
- Add or update deterministic `httpx.MockTransport` tests for protocol behavior. Unit tests must not contact real accounts or the live portal.
- Use `Decimal` for money and `date` for calendar dates. Do not expose portal JSON dictionaries as the primary public API.
- Preserve async operation and explicit client lifecycle. Do not add blocking network calls.
- Never log or commit credentials, cookies, NIFs, invoice identifiers, addresses, raw request/response bodies, or unsanitized browser captures. Keep local captures under ignored `/temp/`; sanitize any fixture committed to tests.
- Do not add payment submission, account mutation, CAPTCHA/MFA bypass, or browser automation without explicit product and security review.
- Do not disable TLS verification or persist credentials in this library.
- Keep errors actionable and avoid leaking secrets or personal data in exception messages.
- Preserve the MIT license and attribution to Oldemar Jesus (`oldemego@gmail.com`).

## Validation

Run the focused test file first, then the complete checks before finalizing:

```shell
pytest
ruff check .
mypy src
```

Use the project's declared minimum Python version for syntax and typing decisions. Python has no official LTS release; the current package metadata targets Python 3.14+.

## Upstream uncertainty

Aquamatrix's portal endpoints are not documented as a stable public API. Treat captured behavior as evidence, not a contract. When a protocol change is needed, document the observed behavior, add sanitized tests, and fail clearly on unknown response shapes rather than silently returning misleading data.