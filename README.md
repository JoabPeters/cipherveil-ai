# CipherVeil AI

**A local-first privacy gateway for AI — by Joab Peters**

This hackathon prototype demonstrates protecting selected sensitive values before an optional hosted-LLM request. Values matched locally are encrypted with AES-256-GCM and replaced with placeholders; the model receives only the sanitized prompt.

## Features
- Local pattern detection for email addresses, phone-like values, and 10–12 digit identifiers.
- AES-256-GCM encryption for recognized values.
- Ephemeral 256-bit key held in app session memory and never sent to the model.
- Dashboard for sanitized prompt, ciphertext, and audit events.
- Optional live AI request using the sanitized prompt.

## Security limitations
This is a prototype, not a production security product or formal security guarantee. Detection is incomplete. Ordinary prompt text and request metadata may reach the provider. The local runtime, dependencies, browser, and host remain trusted components. Refreshing the app loses the session key. This does not guarantee resistance to all prompt injection, side-channel attacks, logging exposure, or host compromise.

Do not enter real passwords, API secrets, financial details, or sensitive personal data.

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
Enter your API key in the app sidebar. Do not commit API keys to GitHub. API access may incur charges and depends on your provider account. Local encryption/redaction can be demonstrated without a key.

## Track
Mathematics for Systems Security — AI Pipeline Secret Sharing.
