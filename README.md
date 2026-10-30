# CipherVeil AI

**An experimental privacy gateway for AI — by Joab Peters**

CipherVeil AI demonstrates detecting selected sensitive values in a prompt, encrypting recognized values with AES-256-GCM, and replacing them with placeholders before an optional hosted-LLM request.

## Current prototype features

- Pattern-based detection for email addresses, phone-like values, and 10–12 digit identifiers.
- AES-256-GCM encryption for recognized values.
- An ephemeral 256-bit key held in the Streamlit application session and never sent to the AI provider.
- A dashboard for sanitized prompts, ciphertext, and basic audit events.
- Optional live AI requests using the sanitized prompt.

## Important deployment and privacy limitation

The current app is a Python Streamlit application. When deployed to Streamlit Community Cloud, its Python code runs on Streamlit's servers, not in the visitor's browser. The original prompt therefore reaches the Streamlit hosting environment before detection and encryption occur.

When a user explicitly requests a live AI response, the app sends the sanitized prompt to the configured AI provider. The encryption key and recognized original values are not included in that AI request.

**This prototype does not protect the original prompt from the application host. Do not enter real passwords, API secrets, financial information, or sensitive personal data.** See [SECURITY.md](SECURITY.md) for the current data-flow explanation and intended security improvements.

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed in the terminal, usually `http://localhost:8501`.

## Optional live AI

Enter your API key in the app sidebar. Do not commit API keys to GitHub. API access may incur charges and depends on your provider account. The local development server or hosted Streamlit server handles the key for the request.

## Hackathon direction

Mathematics for Systems Security — AI Pipeline Secret Sharing.

The current prototype demonstrates encryption and prompt sanitization; it does **not yet implement a secret-sharing protocol**. That is a separate required engineering milestone, not a feature we claim is already complete.
