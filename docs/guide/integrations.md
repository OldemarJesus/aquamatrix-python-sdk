# Integration Patterns

The SDK is framework-independent. An integration should own one client for the lifetime of its account entry, refresh it asynchronously, and close it during unload or shutdown.

## Home Assistant

Use the config entry's stored credentials to construct the client and a coordinator to refresh data. Perform login and reads through Home Assistant's async setup/update lifecycle; do not block the event loop. Call `aclose()` when unloading the config entry. Keep the NIF and password in the integration's secret storage, not in entity attributes or logs.

```python
client = SimarClient(nif, password)
await client.login()
invoices = await client.get_pending_invoices()
```

## MCP server

Create the client within the server's account/session lifecycle. Return only the fields a tool needs, such as amount and payment deadline; avoid exposing address, client code, or invoice identifiers unless the tool's use case requires them. Close the client when the session ends.

## Error handling

Catch `AuthenticationError` for rejected credentials and `SessionExpiredError` for a stale session. Treat `ProtocolError` as an upstream compatibility problem rather than returning partial or fabricated billing data. Retry or reauthenticate only according to the host application's policy.