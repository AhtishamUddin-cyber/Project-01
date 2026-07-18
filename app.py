import io
import os
import time
from datetime import datetime

import streamlit as st
from PIL import Image

import analyzer as az

st.set_page_config(page_title="AI Smart Trade Analyzer", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────────────────────
#   API KEYS (from Streamlit Secrets, with manual override)
# ─────────────────────────────────────────────────────────────
def get_key(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


with st.sidebar:
    st.title("📊 Trade Analyzer")
    st.caption("Live Bitget analysis — no screenshots needed")

    st.subheader("🔑 API Keys")
    gemini_key = st.text_input(
        "Gemini API Key", value=get_key("GEMINI_API_KEY"), type="password",
        help="Only needed for the optional Screenshot Deep-Dive and Pattern Library tabs.",
    )
    newsapi_key = st.text_input(
        "NewsAPI Key (optional)", value=get_key("NEWSAPI_KEY"), type="password",
        help="Adds news-sentiment scoring. Leave blank to skip.",
    )

    st.divider()
    st.subheader("⚙️ Defaults")
    default_timeframe = st.selectbox(
        "Timeframe", ["5m", "15m", "30m", "1h", "2h", "4h", "1d"], index=3,
    )
    st.caption("Data source: Bitget (live) · CoinGecko · Alternative.me")


tab_live, tab_shot, tab_lib = st.tabs(["🔴 Live Dashboard", "📸 Screenshot Deep-Dive", "📚 Pattern Library"])


# ─────────────────────────────────────────────────────────────
#   TAB 1 — LIVE DASHBOARD (main feature, no screenshots)
# ─────────────────────────────────────────────────────────────
with tab_live:
    st.subheader("Live multi-coin analysis")
    st.caption(
        "Bitget ke sare live coins/pairs yahan se select karo — Entry, TP, SL aur "
        "Direction automatically calculate ho jayega, har coin ke liye alag."
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        market_type = st.radio("Market", ["spot", "futures"], horizontal=True,
                                format_func=lambda x: "Spot" if x == "spot" else "Futures")
    with c2:
        timeframe = st.selectbox(
            "Chart timeframe", ["5m", "15m", "30m", "1h", "2h", "4h", "1d"],
            index=["5m", "15m", "30m", "1h", "2h", "4h", "1d"].index(default_timeframe),
            key="live_tf",
        )
    with c3:
        include_news = st.checkbox("Include news", value=False,
                                    help="Slower — one NewsAPI call per selected coin.")

    @st.cache_data(ttl=300, show_spinner=False)
    def _symbols(mtype):
        return az.get_spot_symbols() if mtype == "spot" else az.get_futures_symbols()

    @st.cache_data(ttl=30, show_spinner=False)
    def _tickers(mtype):
        return az.get_all_tickers(mtype)

    with st.spinner("Loading live symbol list from Bitget..."):
        symbols = _symbols(market_type)

    if not symbols:
        st.error("Bitget symbol list load nahi ho saki. Thodi der baad try karo.")
    else:
        tickers = _tickers(market_type)
        labels = []
        label_to_symbol = {}
        for s in symbols:
            sym = s["symbol"]
            t = tickers.get(sym, {})
            price = t.get("price", 0)
            chg = t.get("change_24h", 0)
            arrow = "🟢" if chg >= 0 else "🔴"
            label = f"{s['base']}/USDT  {arrow} {chg:+.2f}%  (${price:,.4f})" if price else f"{s['base']}/USDT"
            labels.append(label)
            label_to_symbol[label] = s

        selected_labels = st.multiselect(
            f"Coins select karo ({len(symbols)} available on {market_type})",
            options=labels,
            max_selections=12,
            help="Ek baar mein max 12 coins — taake analysis fast aur reliable rahe.",
        )

        run_btn = st.button("🚀 Analyze Selected Coins", type="primary", disabled=not selected_labels)

        if run_btn:
            results = []
            progress = st.progress(0.0, text="Starting...")
            for i, lbl in enumerate(selected_labels):
                s = label_to_symbol[lbl]
                progress.progress((i) / len(selected_labels), text=f"Analyzing {s['base']}...")
                res = az.run_live_analysis(
                    coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
                    timeframe=timeframe, newsapi_key=newsapi_key, use_news=include_news,
                )
                if res:
                    results.append((s, res))
                time.sleep(0.3)
            progress.progress(1.0, text="Done!")
            time.sleep(0.3)
            progress.empty()
            st.session_state["live_results"] = results

        results = st.session_state.get("live_results", [])
        if results:
            st.divider()
            st.markdown("### 📋 Summary — all selected coins")

            rows = []
            for s, res in results:
                v = res["verdict"]
                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                if v["agreement"] == "CONFLICT":
                    decision = "🚫 SKIP (conflict)"
                elif v["accuracy"] >= 75:
                    decision = "✅ ENTER"
                elif v["accuracy"] >= 55:
                    decision = "⚠️ WAIT"
                else:
                    decision = "❌ SKIP"
                rows.append({
                    "Coin": s["base"],
                    "Direction": f"{dir_emoji} {v['final_direction']}",
                    "Confidence": f"{v['accuracy']:.0f}%",
                    "Decision": decision,
                    "Entry Zone": f"${v['entry_low']:,.6f} - ${v['entry_high']:,.6f}" if v["entry_low"] else "N/A",
                    "TP1": f"${v['tp1']:,.6f}" if v["tp1"] else "N/A",
                    "TP2": f"${v['tp2']:,.6f}" if v["tp2"] else "N/A",
                    "SL": f"${v['sl']:,.6f}" if v["sl"] else "N/A",
                    "R:R": f"1:{v['rr']}" if v["rr"] != "N/A" else "N/A",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### 🔍 Per-coin details")
            for s, res in results:
                chart = res["chart"]
                v = res["verdict"]
                indicators = res["indicators"]
                funding = res["funding"]
                orderbook = res["orderbook"]
                fg = res["fg"]

                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                with st.expander(f"{dir_emoji} {s['base']} — {v['final_direction']} ({v['accuracy']:.0f}% confidence)"):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Live Price", f"${chart['price']:,.6f}" if chart["price"] else "N/A")
                    m2.metric("Trend", chart["trend"])
                    m3.metric("RSI (14)", f"{indicators.get('rsi', 0):.1f}")
                    atr = indicators.get("atr")
                    atr_pct = (atr / chart["price"] * 100) if (atr and chart["price"]) else 0
                    m4.metric("Volatility (ATR)", f"{atr_pct:.2f}%" if atr else "N/A")

                    if v["agreement"] == "CONFLICT":
                        st.error("🚫 Data aur trend direction alag hain — is coin ko abhi skip karo.")
                    else:
                        e1, e2, e3, e4 = st.columns(4)
                        e1.metric("Entry Zone", f"{v['entry_low']:,.6f} - {v['entry_high']:,.6f}" if v["entry_low"] else "N/A")
                        e2.metric("Take Profit 1", f"{v['tp1']:,.6f}" if v["tp1"] else "N/A")
                        e3.metric("Take Profit 2", f"{v['tp2']:,.6f}" if v["tp2"] else "N/A")
                        e4.metric("Stop Loss", f"{v['sl']:,.6f}" if v["sl"] else "N/A")
                        st.caption(f"Risk:Reward = 1:{v['rr']}  |  {v['entry_note']}")

                    st.markdown("**Signal breakdown:**")
                    for level, text in v["factors"]:
                        icon = "✅" if level == "good" else ("⚠️" if level == "warn" else "❌")
                        st.markdown(f"- {icon} {text}")

                    d1, d2, d3 = st.columns(3)
                    d1.metric("Order Book", f"Buy {orderbook.get('buy_pct',50):.0f}% / Sell {orderbook.get('sell_pct',50):.0f}%")
                    d2.metric("Fear & Greed", f"{fg.get('value',50)} — {fg.get('label','')}")
                    d3.metric("Funding Rate", f"{funding.get('rate',0):+.4f}% ({funding.get('signal','NEUTRAL')})")

                    try:
                        docx_bytes = az.generate_docx_bytes(chart, res["market"], funding, indicators, v, [], None)
                        st.download_button(
                            "📥 Download Word Report", data=docx_bytes,
                            file_name=f"{s['base']}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{s['base']}_{s['symbol']}",
                        )
                    except Exception as e:
                        st.caption(f"Report generation skipped: {e}")

        st.divider()
        st.caption("⚠️ Ye AI-assisted analysis hai, financial advice nahi. Hamesha apna stop-loss lagao — max 2% risk per trade.")


# ─────────────────────────────────────────────────────────────
#   TAB 2 — SCREENSHOT DEEP-DIVE (optional, uses Gemini vision)
# ─────────────────────────────────────────────────────────────
with tab_shot:
    st.subheader("Screenshot Deep-Dive (optional)")
    st.caption(
        "Agar kisi specific chart screenshot (jaise TradingView ka custom chart) ko "
        "Gemini AI se visually padhwana ho, patterns ke saath — to yahan upload karo."
    )

    if not gemini_key:
        st.warning("Ye feature use karne ke liye sidebar mein Gemini API Key daalo.")
    else:
        s1, s2 = st.columns(2)
        with s1:
            shot_market = st.radio("Market type of this chart", ["spot", "futures"], horizontal=True, key="shot_mkt")
        uploaded = st.file_uploader("Chart screenshot upload karo", type=["png", "jpg", "jpeg", "webp"])

        if uploaded and st.button("🔍 Analyze This Screenshot", type="primary"):
            image = Image.open(uploaded)
            st.image(image, caption="Uploaded chart", width=500)

            log_box = st.empty()
            logs = []

            def log(msg):
                logs.append(msg)
                log_box.info("\n".join(logs[-3:]))

            library = az.load_library()
            with st.spinner("Analyzing..."):
                res = az.run_full_analysis(image, gemini_key, newsapi_key, library, shot_market, log=log)
            log_box.empty()

            if not res:
                st.error("Chart read nahi ho saka. Dobara try karo — clearer screenshot ke saath.")
            else:
                chart = res["chart"]
                v = res["verdict"]
                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"

                if v["agreement"] == "CONFLICT":
                    st.error("🚫 MARKET NOT IN FAVOUR — Gemini aur Data alag directions mein hain. Trade skip karo.")
                else:
                    st.success(f"{dir_emoji} {v['final_direction']} — Confidence {v['accuracy']:.0f}%")
                    e1, e2, e3, e4 = st.columns(4)
                    e1.metric("Entry Zone", f"{v['entry_low']:,.6f} - {v['entry_high']:,.6f}" if v["entry_low"] else "N/A")
                    e2.metric("TP1", f"{v['tp1']:,.6f}" if v["tp1"] else "N/A")
                    e3.metric("TP2", f"{v['tp2']:,.6f}" if v["tp2"] else "N/A")
                    e4.metric("SL", f"{v['sl']:,.6f}" if v["sl"] else "N/A")

                st.markdown("**Signal breakdown:**")
                for level, text in v["factors"]:
                    icon = "✅" if level == "good" else ("⚠️" if level == "warn" else "❌")
                    st.markdown(f"- {icon} {text}")

                st.markdown("**AI chart observations:**")
                st.write(chart.get("reason", "N/A"))

                try:
                    docx_bytes = az.generate_docx_bytes(
                        chart, res["market"], res["funding"], res["indicators"], v,
                        res["matched_patterns"], image,
                    )
                    st.download_button(
                        "📥 Download Word Report", data=docx_bytes,
                        file_name=f"{chart['coin_symbol']}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                except Exception as e:
                    st.caption(f"Report generation skipped: {e}")


# ─────────────────────────────────────────────────────────────
#   TAB 3 — PATTERN LIBRARY
# ─────────────────────────────────────────────────────────────
with tab_lib:
    st.subheader("Pattern Library")
    st.caption("Apne candlestick pattern references add karo — screenshot deep-dive inhe match karega.")

    library = az.load_library()
    st.write(f"**Total patterns saved:** {len(library)}")

    if library:
        lib_rows = [
            {"Name": p["name"], "Type": p["type"], "Signal": p["signal"], "Reliability": p["reliability"]}
            for p in library.values()
        ]
        st.dataframe(lib_rows, use_container_width=True, hide_index=True)

        del_name = st.selectbox("Delete a pattern", ["-- select --"] + [p["name"] for p in library.values()])
        if del_name != "-- select --" and st.button("🗑️ Delete Selected Pattern"):
            key_to_del = next(k for k, p in library.items() if p["name"] == del_name)
            del library[key_to_del]
            az.save_library(library)
            st.success(f"Deleted: {del_name}")
            st.rerun()

    st.divider()
    st.markdown("**Add new patterns** (image or PDF)")
    if not gemini_key:
        st.warning("Pattern add karne ke liye sidebar mein Gemini API Key daalo.")
    else:
        pattern_files = st.file_uploader(
            "Pattern image(s) or PDF upload karo", type=["png", "jpg", "jpeg", "webp", "pdf"],
            accept_multiple_files=True, key="pattern_upload",
        )
        if pattern_files and st.button("➕ Add to Library"):
            library = az.load_library()
            for f in pattern_files:
                with st.spinner(f"Processing {f.name}..."):
                    if f.name.lower().endswith(".pdf"):
                        added = az.add_patterns_from_pdf(f.read(), f.name, gemini_key, library)
                    else:
                        image = Image.open(f)
                        added = az.add_pattern_from_image(image, f.name, gemini_key, library)
                if added:
                    st.success(f"{f.name}: added {', '.join(added)}")
                else:
                    st.warning(f"{f.name}: koi pattern detect nahi hua")
            az.save_library(library)
            st.rerun()
