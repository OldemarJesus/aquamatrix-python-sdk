# Architecture

## Boundary

`SimarClient` is the integration-facing facade. It owns one `httpx.AsyncClient`, its cookies, and the credentials for the lifetime of that client. It exposes async operations and translates HTTP/portal behavior into `Invoice` models and stable SDK exceptions. Consumers do not need to know the portal's URL paths, form encoding, token field, or DataTables parameter names.

```text
Home Assistant / MCP / Python application
                 |
            SimarClient
       /         |         \
 session     protocol     mapping
 cookies     CSRF/forms    Invoice
                 |
       Aquamatrix SIMARnet portal
```

## Modules

- `client.py`: async transport, login, token refresh, billing requests, pagination input, and wire-format mapping.
- `models.py`: immutable public domain values; currently `Invoice` with `Decimal` amount and `date` fields.
- `errors.py`: stable base, authentication, session-expiry, and protocol exceptions.
- `__init__.py`: supported public exports.

## Authentication and request flow

1. `login()` GETs `/SIMARnet/Account/Login`, allowing the HTTP cookie jar to retain portal cookies.
2. The response HTML is parsed for `__RequestVerificationToken` using the standard-library HTML parser.
3. The token, `UserCode` (NIF), password, and `RememberMe=false` are submitted as form data. A redirect into SIMARnet marks the client authenticated; credentials are not persisted.
4. Each invoice-history request fetches the authenticated billing page for its anti-forgery token, then POSTs the token, DataTables fields, and date filters to `GetInvoicesHistory` using the authenticated session cookies.
5. Portal rows are converted into immutable `Invoice` values. Pending filtering only accepts known unpaid states and excludes records with a payment date.

The portal is currently observed to return dates as ISO strings for display and ASP.NET `/Date(milliseconds)/` values for raw fields. The mapper accepts either representation. Monetary values are represented by JSON numbers and converted through their string form to `Decimal`.

## Error behavior

- `AuthenticationError`: login was not completed or a protected operation was called before login.
- `SessionExpiredError`: the authenticated page/token is no longer available or the portal rejects the session.
- `ProtocolError`: unexpected HTTP, JSON, or data shape indicates an upstream change.

No automatic retry is performed. Consumers decide whether and when to re-authenticate. The client is an async context manager and should be closed when an integration unloads.

## Security and privacy

- Credentials and session cookies remain in memory for the client lifetime.
- Do not log credentials, form bodies, cookies, NIF, invoice identifiers, addresses, or returned personal data.
- Tests must use synthetic fixtures. Browser captures, HAR/SAR files, and account exports are ignored and must never be committed.
- TLS verification remains enabled; do not add credential submission over insecure transport.
- Scope is read-only. Payment submission is deliberately excluded.

## Evolution

Treat all portal wire formats as private implementation details. Add a normalized model or public method only where downstream callers have a concrete need; keep selectors, forms, and response peculiarities private. Tests should mock HTTP and use sanitized generic fixtures so protocol regressions are observable offline.