# Aquamatrix SIMAR Python SDK

An async Python client for reading billing information from the SIMAR customer portal hosted by Aquamatrix.

Use the SDK to establish a portal session and retrieve typed billing, reading, and graph data without putting Aquamatrix's HTML or portal paths into each integration.

## Capabilities

- Authenticate with a SIMAR NIF and password.
- Retrieve billing summary counts and billed-value graph data.
- Read the latest and upcoming meter-reading dates and water-shortage status.
- Use an async context manager and typed response models.

Invoice history and pending-invoice methods are temporarily disabled because the portal endpoint requires POST and currently returns HTTP 417.

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