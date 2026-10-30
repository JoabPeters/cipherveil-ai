# Security and data-flow notes

## Current prototype: important deployment limitation

CipherVeil AI currently runs as a Python Streamlit application. When deployed on Streamlit Community Cloud, the Python code executes on Streamlit-hosted infrastructure, not inside the visitor's browser.

This means:

1. The user's original prompt is transmitted to the Streamlit application server so the Python code can inspect it.
2. The application detects a limited set of patterns and encrypts matched values in the server-side application session.
3. The sanitized prompt is sent to the configured AI provider only when the user explicitly requests a live model response.
4. The encryption key is not included in the AI request.

Therefore, the current deployment does **not** provide client-side or end-to-end protection from the application host. The hosting environment processes the original prompt before redaction. Do not enter real sensitive information into this prototype.

## Current limitations

- Detection is limited to patterns in the application code and can miss sensitive information or produce false positives.
- AES-256-GCM protects matched values in the app's in-memory vault; it does not make the original prompt invisible to the Streamlit host.
- The session key is ephemeral and is not a durable key-management solution.
- The current implementation does not yet implement a secret-sharing protocol.
- The current implementation has not undergone an independent security audit or penetration test.

## Intended direction

The longer-term architecture is to move detection and protection to a trusted client-side component where feasible, then send only sanitized content to a provider adapter. Any secret-sharing protocol must be separately designed, implemented, tested, and documented. Provider integrations must not receive master keys or protected plaintext values.

Until those changes are implemented and verified, describe CipherVeil as an experimental server-side privacy gateway prototype, not as a fully local-first or production-ready security product.
