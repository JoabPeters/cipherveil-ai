import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="CipherVeil AI Browser Prototype")

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)

@app.get("/api/health")
def health():
    return {"status": "ok", "provider_key_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/api/chat")
def chat(request: ChatRequest):
    # This endpoint is designed to receive the already-sanitized prompt only.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI backend is not configured yet. Set OPENAI_API_KEY on the server.")
    if OpenAI is None:
        raise HTTPException(status_code=503, detail="OpenAI SDK is not installed.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are helpful. Square-bracket tokens such as [EMAIL_1] are privacy placeholders. Do not guess their original values."},
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.2,
        )
        return {"answer": response.choices[0].message.content, "model": model}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {type(exc).__name__}") from exc

# Serve the browser application from the same origin as the API.
app.mount("/", StaticFiles(directory=ROOT, html=True), name="browser")
