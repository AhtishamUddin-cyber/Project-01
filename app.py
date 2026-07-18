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
    st.caption("Data source: Bitget (live) · CoinGecko · Alternative.me")


tab_live, tab_shot, tab_lib, tab_track = st.tabs(
    ["🔴 Live Dashboard", "📸 Screenshot Deep-Dive", "📚 Pattern Library", "📒 Trade Tracker"]
)


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
            index=3, key="live_tf",
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
            errors = []
            progress = st.progress(0.0, text="Starting...")
            for i, lbl in enumerate(selected_labels):
                s = label_to_symbol[lbl]
                progress.progress((i) / len(selected_labels), text=f"Analyzing {s['base']}...")
                res = az.run_live_analysis(
                    coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
                    timeframe=timeframe, newsapi_key=newsapi_key, use_news=include_news,
                )
                if res and "error" not in res:
                    results.append((s, res))
                else:
                    err_msg = res.get("error", "Unknown error") if res else "No response"
                    errors.append(f"{s['base']}: {err_msg}")
                time.sleep(0.3)
            progress.progress(1.0, text="Done!")
            time.sleep(0.3)
            progress.empty()
            st.session_state["live_results"] = results
            st.session_state["live_errors"] = errors

        errors = st.session_state.get("live_errors", [])
        if errors:
            with st.expander(f"⚠️ {len(errors)} coin(s) could not be analyzed — click for details"):
                for e in errors:
                    st.write(f"- {e}")

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

                    if v["agreement"] != "CONFLICT" and v["entry_low"]:
                        st.divider()
                        entry_ref = round((v["entry_low"] + v["entry_high"]) / 2, 8)
                        tcol1, tcol2 = st.columns([3, 1])
                        with tcol1:
                            st.caption(
                                f"📒 Log this as a real trade — Entry ~{entry_ref:,.6f}, "
                                f"TP1 {v['tp1']:,.6f}, TP2 {v['tp2']:,.6f}, SL {v['sl']:,.6f}"
                            )
                        with tcol2:
                            if st.button("➕ Add to Tracker", key=f"track_{s['base']}_{s['symbol']}"):
                                az.add_trade(
                                    coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
                                    direction=v["final_direction"], entry=entry_ref,
                                    tp1=v["tp1"], tp2=v["tp2"], sl=v["sl"], timeframe=timeframe,
                                )
                                st.success(f"{s['base']} trade added to tracker! Check the 📒 Trade Tracker tab.")

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


# ─────────────────────────────────────────────────────────────
#   TAB 4 — TRADE TRACKER
# ─────────────────────────────────────────────────────────────
with tab_track:
    st.subheader("Trade Tracker")
    st.caption(
        "Jo trades tumne Live Dashboard se 'Add to Tracker' kiye hain, wo yahan track hote hain. "
        "Refresh dabate hi live price check hoga aur agar TP ya SL hit ho gaya ho to status khud update ho jayega."
    )

    tcol1, tcol2 = st.columns([1, 4])
    with tcol1:
        if st.button("🔄 Refresh & Check Status", type="primary"):
            with st.spinner("Checking live prices against TP/SL..."):
                az.refresh_all_trades()
            st.rerun()

    trades = az.load_trades()

    if not trades:
        st.info("Abhi koi trade track nahi ho raha. Live Dashboard mein kisi coin ki analysis kholo aur '➕ Add to Tracker' dabao.")
    else:
        stats = az.trade_stats(trades)
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Open Trades", stats["open"])
        s2.metric("Closed Trades", stats["closed"])
        s3.metric("Win Rate", f"{stats['win_rate']:.0f}%" if stats["closed"] else "N/A")
        s4.metric("Avg Win", f"{stats['avg_win_pnl']:+.2f}%" if stats["wins"] else "N/A")
        s5.metric("Avg Loss", f"{stats['avg_loss_pnl']:+.2f}%" if stats["losses"] else "N/A")

        st.divider()
        open_trades = [t for t in trades if t["status"] == "OPEN"]
        closed_trades = [t for t in trades if t["status"] != "OPEN"]

        st.markdown("### 🟡 Open Trades")
        if not open_trades:
            st.caption("Koi open trade nahi hai.")
        else:
            for t in open_trades:
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                cur = t.get("current_price")
                pnl = t.get("pnl_pct")
                pnl_txt = f"{pnl:+.2f}%" if pnl is not None else "—"
                with st.container(border=True):
                    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1])
                    h1.markdown(f"**{dir_emoji} {t['coin']}** ({t['market_type']}, {t['timeframe']}) — opened {t['opened_at']}")
                    h2.metric("Entry", f"{t['entry']:,.6f}")
                    h3.metric("Current", f"{cur:,.6f}" if cur else "—")
                    h4.metric("Unrealized P&L", pnl_txt)
                    with h5:
                        if st.button("✋ Close now", key=f"close_{t['id']}"):
                            az.close_trade_manually(t["id"], exit_price=cur, note="Manually closed")
                            st.rerun()
                    st.caption(f"TP1 {t['tp1']:,.6f}  |  TP2 {t.get('tp2', 0):,.6f}  |  SL {t['sl']:,.6f}")

        st.divider()
        st.markdown("### ✅ Closed Trades")
        if not closed_trades:
            st.caption("Abhi tak koi trade close nahi hua.")
        else:
            status_map = {
                "TP1_HIT": "✅ Take Profit 1 Hit",
                "TP2_HIT": "🎯 Take Profit 2 Hit",
                "SL_HIT": "❌ Stop Loss Hit",
                "CLOSED_MANUAL": "✋ Closed Manually",
            }
            rows = []
            for t in sorted(closed_trades, key=lambda x: x.get("closed_at") or "", reverse=True):
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                rows.append({
                    "Coin": f"{dir_emoji} {t['coin']}",
                    "Direction": t["direction"],
                    "Entry": f"{t['entry']:,.6f}",
                    "Exit": f"{t['exit_price']:,.6f}" if t.get("exit_price") else "N/A",
                    "Result": status_map.get(t["status"], t["status"]),
                    "P&L": f"{t['pnl_pct']:+.2f}%" if t.get("pnl_pct") is not None else "—",
                    "Opened": t["opened_at"],
                    "Closed": t.get("closed_at") or "—",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            del_id = st.selectbox(
                "Delete a closed trade record",
                ["-- select --"] + [f"{t['coin']} @ {t['opened_at']} ({t['id']})" for t in closed_trades],
            )
            if del_id != "-- select --" and st.button("🗑️ Delete This Record"):
                trade_id = del_id.split("(")[-1].rstrip(")")
                az.delete_trade(trade_id)
                st.rerun()

        st.divider()
        st.caption(
            "⚠️ Status sirf jab tum 'Refresh' dabate ho tab ke live price se check hota hai — "
            "agar price beech mein SL aur TP dono cross kar chuki ho refresh se pehle, to sirf latest "
            "price ke hisaab se result dikhega. Bitget app/exchange par apna actual order hamesha confirm karo."
        )
