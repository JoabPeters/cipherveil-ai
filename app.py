import os
import re
import base64
from datetime import datetime, timezone

import streamlit as st
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(page_title="CipherVeil AI", page_icon="🔐", layout="wide")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at 10% 0%, #132642 0, #0b1220 40%, #080d17 100%); color:#eef5ff;}
section[data-testid="stSidebar"] {background:#0d1728;}
div[data-testid="stMetric"] {background:#111f33; border:1px solid #243b59; padding:14px; border-radius:12px;}
.cv-card {background:#101d30; border:1px solid #243b59; border-radius:14px; padding:18px; margin:8px 0;}
</style>
""", unsafe_allow_html=True)

if "key" not in st.session_state:
    st.session_state.key = AESGCM.generate_key(bit_length=256)
if "vault" not in st.session_state:
    st.session_state.vault = []
if "audit" not in st.session_state:
    st.session_state.audit = []

def protect_secrets(text, key):
    """Encrypt recognized sensitive values locally and replace them before API transmission."""
    patterns = [
        ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
        ("PHONE", re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")),
        ("ID_NUMBER", re.compile(r"\b\d{10,12}\b")),
    ]
    matches = []
    for label, pattern in patterns:
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if label == "PHONE" and len(re.sub(r"\D", "", value)) < 9:
                continue
            matches.append((match.start(), label, value))

    unique, seen = [], set()
    for _, label, value in matches:
        if (label, value) not in seen:
            seen.add((label, value))
            unique.append((label, value))

    safe_text, vault_items = text, []
    for idx, (label, value) in enumerate(unique, start=1):
        nonce = os.urandom(12)
        ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), label.encode("utf-8"))
        token = f"[{label}_{idx}]"
        safe_text = safe_text.replace(value, token)
        vault_items.append({
            "token": token, "type": label,
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
            "aad": label,
        })
    return safe_text, vault_items

def call_model(prompt, api_key, model):
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK is missing. Run: pip install -r requirements.txt")
    if not api_key:
        raise RuntimeError("Enter an API key in the sidebar to use live AI. Local protection works without one.")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are helpful. Square-bracket tokens such as [EMAIL_1] are privacy placeholders. Do not guess their original values."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content

st.title("🔐 CipherVeil AI")
st.caption("A local-first privacy gateway for AI · Built by Joab Peters")
st.markdown("""
<div class="cv-card"><b>Privacy boundary</b><br>
Recognized sensitive values are encrypted in this app session and replaced with placeholders before an optional AI request.
The model does not receive the master key or those original protected values. Ordinary prompt text and request metadata may still reach the provider.
</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("AI connection")
    api_key = st.text_input("OpenAI API key (optional)", type="password",
                            help="Used for a live request only. Never paste a key into source code.")
    model = st.text_input("Model name", value="gpt-4o-mini")
    st.divider()
    st.subheader("Session key")
    st.success("AES-256-GCM key generated in memory")
    st.caption("The key is not shown or sent to the model. Refreshing starts a new session.")
    if st.button("Reset session and vault"):
        st.session_state.key = AESGCM.generate_key(bit_length=256)
        st.session_state.vault = []
        st.session_state.audit = []
        for name in ("safe_prompt", "original_prompt", "answer"):
            st.session_state.pop(name, None)
        st.rerun()

left, right = st.columns([1.1, 0.9], gap="large")
with left:
    st.subheader("1 · Compose a private request")
    prompt = st.text_area("Prompt", height=200,
        placeholder="Example: Draft an email to joab@example.com and ask them to call +234 801 234 5678 about account 123456789012.")
    if st.button("Protect prompt", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Enter a prompt first.")
        else:
            safe_prompt, items = protect_secrets(prompt, st.session_state.key)
            st.session_state.safe_prompt = safe_prompt
            st.session_state.vault = items
            st.session_state.audit = [{
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "event": "LOCAL_PROTECTION",
                "recognized_values": len(items),
                "api_called": False,
            }]
            st.session_state.pop("answer", None)
            st.success(f"Protected {len(items)} recognized sensitive value(s).")

    if "safe_prompt" in st.session_state:
        st.subheader("2 · Sanitized prompt")
        st.code(st.session_state.safe_prompt, language="text")
        st.caption("This sanitized text—not the original prompt—is sent by the live AI button.")
        if st.button("Send sanitized prompt to AI", use_container_width=True):
            try:
                answer = call_model(st.session_state.safe_prompt, api_key, model)
                st.session_state.answer = answer
                st.session_state.audit.append({
                    "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "event": "LIVE_MODEL_REQUEST",
                    "recognized_secrets_sent": 0,
                    "model": model,
                    "api_called": True,
                })
            except Exception as exc:
                st.error(str(exc))
        if "answer" in st.session_state:
            st.subheader("3 · AI response")
            st.write(st.session_state.answer)

with right:
    st.subheader("Privacy telemetry")
    st.metric("Encrypted values", len(st.session_state.vault))
    st.metric("Master key sent to model", "No")
    st.metric("Original detected values sent", "No*" if st.session_state.vault else "Not tested")
    st.markdown('<div class="cv-card"><b>Encrypted local vault</b><br>Ciphertext is held in session memory and is not included in the model request.</div>', unsafe_allow_html=True)
    if st.session_state.vault:
        for item in st.session_state.vault:
            with st.expander(f'{item["token"]} · {item["type"]}'):
                st.write("Nonce (base64)")
                st.code(item["nonce_b64"])
                st.write("Ciphertext (base64)")
                st.code(item["ciphertext_b64"])
                st.caption("Plaintext is intentionally not shown here.")
    else:
        st.info("Protect a prompt to populate the encrypted vault.")
    st.subheader("Audit log")
    st.json(st.session_state.audit or [{"status": "Waiting for first run"}])
    st.caption("*Only values matched by this prototype's limited patterns. Detection is not exhaustive; do not use real sensitive data.")

st.divider()
st.subheader("Security boundaries")
st.markdown("""
- **Encryption:** AES-256-GCM from the `cryptography` library; a fresh 12-byte nonce is used for each value.
- **Key handling:** a random key exists in application session memory and is never added to the prompt.
- **Privacy model:** recognized fields are encrypted locally and omitted from the external model request.
- **Limitations:** detection is incomplete; the key is ephemeral; ordinary prompt text and metadata may be transmitted; the app does not guarantee protection from host compromise, all logs, browser extensions, or side-channel attacks.
- **Safety:** never paste real passwords, API secrets, financial data, or sensitive personal information into this hackathon prototype.
""")
