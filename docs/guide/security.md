# Security and Limitations

This is an unofficial client for a private web interface, not a documented Aquamatrix or SIMAR API. Endpoint paths and response formats may change without notice. Compatibility is best-effort and no availability or correctness guarantee is implied.

- Use only accounts you are authorized to access and follow the portal's applicable terms.
- Credentials and session cookies are held in memory for the client lifetime; this library does not persist them.
- Do not log credentials, cookies, NIFs, raw request or response bodies, addresses, or invoice identifiers.
- Keep credentials in a host application's secret store.
- The client verifies TLS and performs read-only operations. It does not submit payments or mutate account state.
- Authentication challenges such as MFA or CAPTCHA are not bypassed. If the portal requires a new flow, access may fail until the client is updated appropriately.

If the portal changes, report a sanitized description of the response shape; never attach unredacted browser captures or account data to an issue.