# CipherVeil AI — Browser-side prototype

This is a separate experimental prototype. It does not replace the existing Streamlit app.

## What is different?

- The prompt text is read and inspected by JavaScript in the browser.
- Matched values are encrypted with the browser Web Crypto API using AES-256-GCM.
- The AES key is generated as non-exportable and remains in browser memory.
- Only the sanitized prompt is sent to the FastAPI backend when the user clicks **Send sanitized prompt to AI**.
- The backend uses an environment variable for the provider API key. The key is never placed in browser JavaScript.

## Run locally

Python 3.10+ is recommended.

1. Open a terminal in the repository root.
2. Create and activate a virtual environment.
3. Install the browser prototype requirements:

   `pip install -r browser-prototype/server/requirements.txt`

4. Set your provider key in the terminal environment (do not commit it):

   PowerShell:
   `$env:OPENAI_API_KEY="your-key-here"`

   macOS/Linux:
   `export OPENAI_API_KEY="your-key-here"`

5. Start the server from the repository root:

   `uvicorn browser-prototype.server.main:app --reload`

6. Open `http://127.0.0.1:8000`.

The browser-side protection demo works without an API key. The live AI button needs a valid key and may incur provider charges.

## Security limitations

- This is a prototype, not a security-audited product.
- Pattern matching is incomplete and may miss or misclassify sensitive information.
- The non-exportable browser key and ciphertext exist only in page memory and are lost on refresh.
- The hosting server receives the sanitized prompt, request metadata, and AI response. It is designed not to receive the original prompt or the browser vault.
- The browser must trust the JavaScript served by the application host. A compromised host could serve modified code that reads prompts.
- The current version uses AES-GCM encryption but does not yet implement Shamir Secret Sharing or another secret-sharing protocol.
- No production authentication, rate limiting, abuse controls, or independent security review is included yet.
