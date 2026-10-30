# Aquamatrix SIMAR Python SDK

An async Python client for reading billing information from the SIMAR customer portal hosted by Aquamatrix.

Use the SDK to establish a portal session and retrieve typed invoice data without putting Aquamatrix's HTML, CSRF tokens, or form fields into each integration.

## Capabilities

- Authenticate with a SIMAR NIF and password.
- Retrieve billing summary counts and invoice history.
- List pending invoices with amount, issue date, year, and payment deadline.
- Use an async context manager and typed `Invoice` values.

The client is read-only and unofficial. See [Security and limitations](guide/security.md) before connecting an account.

## Start here

- [Install the package](guide/installation.md)
- [Run the quick start](guide/quickstart.md)
- [Integrate with Home Assistant or an MCP server](guide/integrations.md)
- [Browse the API reference](api.md)

## Project

- [Product requirements](https://github.com/OldemarJesus/aquamatrix-python-sdk/blob/main/PRD.md)
- [Architecture](https://github.com/OldemarJesus/aquamatrix-python-sdk/blob/main/ARCH.md)
- [MIT License](https://github.com/OldemarJesus/aquamatrix-python-sdk/blob/main/LICENSE)
- [Release and publishing](guide/releasing.md)