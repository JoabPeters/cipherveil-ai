// CipherVeil browser prototype. Plaintext processing stays in this page.
const $ = (id) => document.getElementById(id);
let cryptoKey = null;
let vaultItems = [];
let safePrompt = "";

const patterns = [
  { type: "EMAIL", regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi },
  { type: "PHONE", regex: /(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)/g },
  { type: "ID_NUMBER", regex: /\b\d{10,12}\b/g }
];

async function newKey() {
  // extractable=false prevents normal JavaScript export of the raw key bytes.
  return crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

function findMatches(text) {
  const found = [];
  for (const item of patterns) {
    for (const match of text.matchAll(item.regex)) {
      const value = match[0].trim();
      if (item.type === "PHONE" && value.replace(/\D/g, "").length < 9) continue;
      const start = match.index;
      found.push({ start, end: start + match[0].length, type: item.type, value });
    }
  }
  // Prefer the longest match at a given position and avoid overlapping replacements.
  found.sort((a,b) => a.start - b.start || (b.end-b.start) - (a.end-a.start));
  const selected = [];
  for (const match of found) {
    if (!selected.length || match.start >= selected[selected.length-1].end) selected.push(match);
  }
  return selected;
}

async function protectInBrowser(text) {
  if (!cryptoKey) cryptoKey = await newKey();
  const matches = findMatches(text);
  const unique = [];
  const tokenByValue = new Map();
  for (const match of matches) {
    const identity = match.type + "::" + match.value;
    if (!tokenByValue.has(identity)) {
      const token = "[" + match.type + "_" + (unique.length + 1) + "]";
      tokenByValue.set(identity, token);
      unique.push({ ...match, token });
    }
  }
  const encrypted = [];
  for (const item of unique) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const aad = new TextEncoder().encode(item.type);
    const ciphertext = await crypto.subtle.encrypt(
      { name: "AES-GCM", iv, additionalData: aad },
      cryptoKey,
      new TextEncoder().encode(item.value)
    );
    encrypted.push({
      token: item.token,
      type: item.type,
      iv: toBase64(iv),
      ciphertext: toBase64(new Uint8Array(ciphertext))
    });
  }
  let result = "";
  let cursor = 0;
  for (const match of matches) {
    result += text.slice(cursor, match.start);
    result += tokenByValue.get(match.type + "::" + match.value);
    cursor = match.end;
  }
  result += text.slice(cursor);
  return { sanitized: result, encrypted };
}

function toBase64(bytes) {
  let binary = "";
  bytes.forEach(byte => binary += String.fromCharCode(byte));
  return btoa(binary);
}

function renderVault() {
  $("count").textContent = String(vaultItems.length);
  $("vault").replaceChildren();
  if (!vaultItems.length) {
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = "No encrypted values yet.";
    $("vault").append(p);
    return;
  }
  for (const item of vaultItems) {
    const div = document.createElement("div");
    div.className = "vault-item";
    const title = document.createElement("strong");
    title.textContent = item.token + " · " + item.type;
    const details = document.createElement("small");
    details.textContent = "AES-GCM ciphertext (base64): " + item.ciphertext.slice(0, 42) + "…";
    div.append(title, details);
    $("vault").append(div);
  }
}

$("sample").addEventListener("click", () => {
  $("prompt").value = "Please email demo@example.com and ask them to call +234 801 234 5678 about reference 123456789012.";
});
$("protect").addEventListener("click", async () => {
  const text = $("prompt").value;
  if (!text.trim()) {
    $("protect-status").textContent = "Enter a sample prompt first.";
    return;
  }
  $("protect").disabled = true;
  $("protect-status").textContent = "Detecting and encrypting in this browser…";
  try {
    const result = await protectInBrowser(text);
    safePrompt = result.sanitized;
    vaultItems = result.encrypted;
    $("sanitized").textContent = safePrompt;
    $("send").disabled = false;
    $("protect-status").textContent = "Protected " + vaultItems.length + " recognized value(s) in the browser. The original prompt has not been sent to the backend.";
    renderVault();
    $("answer").textContent = "AI response will appear here.";
  } catch (error) {
    $("protect-status").textContent = "Browser protection failed: " + error.message;
  } finally {
    $("protect").disabled = false;
  }
});
$("send").addEventListener("click", async () => {
  if (!safePrompt) return;
  $("send").disabled = true;
  $("ai-status").textContent = "Sending sanitized text to the backend…";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: safePrompt })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Backend request failed");
    $("answer").textContent = data.answer || "(The provider returned an empty response.)";
    $("ai-status").textContent = "Completed. The backend received the sanitized prompt only.";
  } catch (error) {
    $("ai-status").textContent = "Could not reach the AI backend: " + error.message + ". You can still test browser-side protection without an API connection.";
  } finally {
    $("send").disabled = false;
  }
});
$("reset").addEventListener("click", async () => {
  cryptoKey = await newKey();
  vaultItems = [];
  safePrompt = "";
  $("prompt").value = "";
  $("sanitized").textContent = "Nothing protected yet.";
  $("answer").textContent = "AI response will appear here.";
  $("protect-status").textContent = "New browser key created. Previous in-memory vault has been cleared.";
  $("ai-status").textContent = "";
  $("send").disabled = true;
  renderVault();
});
(async () => {
  if (!window.crypto || !crypto.subtle) {
    $("protect-status").textContent = "Web Crypto is unavailable. Open this app over HTTPS or localhost in a modern browser.";
    $("protect").disabled = true;
    return;
  }
  cryptoKey = await newKey();
})();