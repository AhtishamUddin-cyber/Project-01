# AI Smart Trade Analyzer — Web App

Live Bitget dashboard: coins select karo (Spot ya Futures), automatic
Entry Zone / Take Profit / Stop Loss / Direction / Confidence har coin
ke liye alag milega — koi screenshot zaroori nahi. Screenshot deep-dive
aur pattern library bhi maujood hain, optional extra tabs ke tor par.

## Files
- `app.py` — Streamlit web page (UI)
- `analyzer.py` — sara analysis logic (indicators, Bitget/CoinGecko calls, docx report)
- `requirements.txt` — Python packages
- `.streamlit/secrets.toml.example` — API key template (real keys yahan **mat** dalna, ye sirf reference hai)

## Deploy karne ka tarika (Streamlit Community Cloud — free)

1. **GitHub pe upload karo**
   - GitHub pe ek naya **private** repository banao (e.g. `trade-analyzer`)
   - Is folder ki sari files (`app.py`, `analyzer.py`, `requirements.txt`, `.streamlit/`) us repo mein upload/push kar do
   - ⚠️ `secrets.toml.example` ko real keys ke saath commit mat karna — real keys sirf Streamlit Cloud ke "Secrets" section mein jayengi (step 4)

2. **Streamlit Cloud pe jao**
   - https://share.streamlit.io par jao aur apne GitHub account se login karo

3. **New app banao**
   - "Create app" → apna repo select karo → main file: `app.py`
   - Deploy dabao

4. **API keys secure add karo**
   - App ke "Settings" → "Secrets" mein jao, aur ye paste karo:
     ```toml
     GEMINI_API_KEY = "apni-real-gemini-key"
     NEWSAPI_KEY = "apni-real-newsapi-key"
     ```
   - Save karo — app khud restart ho jayega

5. **Bas — permanent link mil gaya**
   - Kuch is tarah ka URL milega: `https://your-app-name.streamlit.app`
   - Ye link Chrome mein kisi bhi normal website ki tarah khulega, bookmark kar sakte ho
   - Jab bhi code mein change chahiye ho, mujhe batao — main file update kar dunga, GitHub pe push karte hi Streamlit Cloud khud-ba-khud naya version live kar dega (dobara deploy karne ki zaroorat nahi)

## Gemini API Key kahan se milegi
https://aistudio.google.com/apikey — free tier available hai.

## NewsAPI Key (optional)
https://newsapi.org — free tier available hai (limited requests/day), isliye
Live Dashboard mein "Include news" checkbox by default off rakha hai taake
multiple coins ek saath scan karte waqt limit jaldi na khatam ho.

## Zaroori note
Ye tool sirf analysis/decision-support hai — financial advice nahi. Har
trade se pehle apna stop-loss zaroor lagao (max 2% risk per trade recommend hai).
