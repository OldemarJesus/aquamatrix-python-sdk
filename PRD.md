# TL;DR PRD: Aquamatrix SIMAR SDK

## Product

An async, typed Python library that lets authorized SIMAR customers and downstream projects retrieve account billing data from the Aquamatrix customer portal without reimplementing login, session-cookie, anti-forgery-token, or portal-form mechanics.

## Users and problem

Primary users are Python integration maintainers, especially Home Assistant and MCP developers. They need dependable access to whether invoices are pending and to each invoice's amount, issue year/date, payment deadline, and status. Directly embedding portal scraping and session logic in each integration duplicates brittle implementation details and increases credential-handling risk.

## MVP outcomes

- Authenticate with NIF and password and retain the portal session in an owned HTTP client.
- Expose typed invoice history, pending invoices, and billing summary counts.
- Convert portal dates and amounts to standard Python types and surface stable SDK exceptions.
- Keep all portal-specific paths, CSRF handling, and DataTables forms behind a small client boundary.
- Provide deterministic offline tests and integration-oriented lifecycle/documentation guidance.

## Out of scope

- Initiating payments, modifying customer details, or any other write operation.
- Browser automation, unofficial credential storage, account discovery, or bypassing MFA/CAPTCHA/access controls.
- Guaranteeing compatibility with a website that has no documented stable API.
- Home Assistant or MCP adapters in this repository; those consume the SDK separately.

## Constraints and success criteria

- Python 3.14+ (latest stable at project inception; Python has no official LTS release designation).
- Async HTTP interface, explicit client lifecycle, no credential or personal-data logging.
- Tests cover token acquisition, login, invoice mapping, pending filtering, and expired sessions without contacting the live portal.
- Public MIT project authored by Oldemar Jesus.

## Risks

Aquamatrix may change its private portal endpoints, CSRF mechanics, response fields, authentication requirements, or terms. Such changes must fail with clear errors, be captured in sanitized fixtures, and be reviewed against applicable service terms before release.