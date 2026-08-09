import time
from datetime import datetime

import streamlit as st
from PIL import Image

import analyzer as az

st.set_page_config(page_title="AI Smart Trade Analyzer Made By Ahtisham Uddin", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────────────────────
#   VISUAL THEME — dark, card-style UI
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
    --bg: #0A0E17;
    --panel: #121826;
    --panel-border: #1F2937;
    --accent: #00D9B5;
    --accent-2: #F0B90B;
    --long: #16C784;
    --short: #EA3943;
    --text-dim: #8B96A8;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }

.ata-hero {
    background: linear-gradient(135deg, rgba(0,217,181,0.12), rgba(240,185,11,0.06));
    border: 1px solid var(--panel-border);
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 22px;
}
.ata-hero h1 {
    font-size: 1.9rem;
    margin: 0;
    background: linear-gradient(90deg, #00D9B5, #6DD6FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.ata-hero p { color: var(--text-dim); margin: 4px 0 0 0; font-size: 0.92rem; }

div[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 14px 16px;
}
div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; }
div[data-testid="stMetricLabel"] { color: var(--text-dim); }

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid var(--panel-border);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #00A8FF);
    border: none;
    color: #06110E;
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.08); }

.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,217,181,0.10) !important;
    border-bottom: 2px solid var(--accent) !important;
}

details {
    background: var(--panel);
    border: 1px solid var(--panel-border) !important;
    border-radius: 12px !important;
    margin-bottom: 8px;
}

div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px !important; }
span[data-baseweb="tag"] { border-radius: 8px !important; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ata-hero">
  <h1>📊 AI Smart Trade Analyzer Made By Ahtisham Uddin</h1>
  <p>Live Bitget multi-coin analysis — AI + real indicators, no screenshot required</p>
</div>
""", unsafe_allow_html=True)

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
    github_token = st.text_input(
        "GitHub Token (recommended)", value=get_key("GITHUB_TOKEN"), type="password",
        help="Without this, Pattern Library and Trade Tracker data get wiped whenever "
             "Streamlit Cloud restarts the app (it happens automatically). With a token, "
             "data is also saved into your GitHub repo so it survives restarts. "
             "Create one free at github.com → Settings → Developer settings → "
             "Personal access tokens → Fine-grained → grant 'Contents: Read and write' "
             "on this repo only.",
    )
    if github_token:
        if st.button("🔌 Test GitHub Connection"):
            with st.spinner("Checking token..."):
                ok, msg = az.test_github_connection(github_token)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ Connection failed: {msg}")
        if not get_key("GITHUB_TOKEN"):
            st.warning(
                "⚠️ Yeh token abhi sirf is box mein typed hai, Streamlit Secrets mein saved "
                "nahi — refresh/app-restart hote hi gayab ho jayega aur data phir se sirf local "
                "(temporary) storage mein save hoga. Secrets mein `GITHUB_TOKEN = \"...\"` add karo."
            )

    st.subheader("💰 Position Sizing")
    st.caption("Har analysis ke sath position size bhi suggest hogi — SL hit hone par exactly itna hi % loss ho.")
    account_balance = st.number_input("Account Balance (USDT)", min_value=0.0, value=100.0, step=10.0)
    risk_pct = st.slider("Risk per trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    leverage = st.number_input("Leverage (futures only)", min_value=1, max_value=125, value=1, step=1)
    st.caption(
        "⚠️ Zyada leverage se liquidation price entry ke kareeb aa jati hai — agar woh tumhare "
        "SL se pehle aa gayi, to trade SL par nahi, liquidation par band hogi (poora margin loss). "
        "Har trade ke sath 'Safe Leverage' suggestion dekho jo us trade ke SL distance ke hisaab se hai."
    )

    st.divider()
    st.caption("Data source: Bitget (live) · CoinGecko · Alternative.me")


@st.cache_data(ttl=20, show_spinner=False)
def _cached_trades(token):
    return az.load_trades(github_token=token)


tab_live, tab_scan, tab_shot, tab_lib, tab_track, tab_backtest = st.tabs(
    ["🔴 Live Dashboard", "🔍 Opportunity Scanner", "📸 Screenshot Deep-Dive",
     "📚 Pattern Library", "📒 Trade Tracker", "🔁 Backtest"]
)


# ─────────────────────────────────────────────────────────────
#   TAB 1 — LIVE DASHBOARD (main feature, no screenshots)
# ─────────────────────────────────────────────────────────────
ALL_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]


def render_coin_tf_detail(s, res, market_type, timeframe, github_token, account_balance,
                           risk_pct, leverage, key_prefix):
    """Renders the full detail block (metrics, factors, tracker button, download)
    for one coin on one timeframe. key_prefix must be unique per coin+timeframe
    combination so widget keys never collide when multiple timeframes for the
    same coin are shown together (All-timeframes mode)."""
    chart = res["chart"]
    v = res["verdict"]
    indicators = res["indicators"]
    funding = res["funding"]
    orderbook = res["orderbook"]
    fg = res["fg"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"${chart['price']:,.6f}" if chart["price"] else "N/A")
    m2.metric("Trend", chart["trend"])
    m3.metric("RSI (14)", f"{indicators.get('rsi', 0):.1f}")
    atr = indicators.get("atr")
    atr_pct = (atr / chart["price"] * 100) if (atr and chart["price"]) else 0
    m4.metric("Volatility (ATR)", f"{atr_pct:.2f}%" if atr else "N/A")

    if v["agreement"] == "CONFLICT":
        st.error("🚫 Data aur trend direction alag hain — is coin/timeframe ko abhi skip karo.")
    else:
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Entry Zone", f"{v['entry_low']:,.6f} - {v['entry_high']:,.6f}" if v["entry_low"] else "N/A")
        e2.metric("Take Profit 1", f"{v['tp1']:,.6f}" if v["tp1"] else "N/A")
        e3.metric("Take Profit 2", f"{v['tp2']:,.6f}" if v["tp2"] else "N/A")
        e4.metric("Stop Loss", f"{v['sl']:,.6f}" if v["sl"] else "N/A")
        st.caption(f"Risk:Reward = 1:{v['rr']}  |  {v['entry_note']}")

        htf_trend = v.get("htf_trend")
        htf_tf = v.get("htf_timeframe", "-")
        if htf_trend and htf_trend != v["final_direction"] and htf_trend != "NEUTRAL":
            st.warning(f"⚠️ Counter-trend: {htf_tf} higher-timeframe trend is {htf_trend}, this trade is {v['final_direction']}. Higher risk — size down or skip.")
        elif htf_trend == v["final_direction"]:
            st.caption(f"✅ Higher timeframe ({htf_tf}) trend agrees: {htf_trend}")

    st.markdown("**Signal breakdown:**")
    for level, text in v["factors"]:
        icon = "✅" if level == "good" else ("⚠️" if level == "warn" else "❌")
        st.markdown(f"- {icon} {text}")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Order Book", f"Buy {orderbook.get('buy_pct',50):.0f}% / Sell {orderbook.get('sell_pct',50):.0f}%")
    d2.metric("Fear & Greed", f"{fg.get('value',50)} — {fg.get('label','')}")
    d3.metric("Funding Rate", f"{funding.get('rate',0):+.4f}% ({funding.get('signal','NEUTRAL')})")
    whale = res.get("whale", {})
    d4.metric("RSI Divergence", indicators.get("rsi_divergence", "NONE").title())
    if whale.get("available") or whale.get("wall_side"):
        st.caption(f"🐋 Whale activity: {whale.get('note', 'N/A')}")

    hist = az.coin_trade_history(_cached_trades(github_token), s["base"])
    if hist["count"] > 0:
        st.caption(
            f"📜 **{s['base']} ki pichli trades:** {hist['count']} closed — "
            f"{hist['wins']} profit, {hist['losses']} loss ({hist['win_rate']:.0f}% win rate), "
            f"avg P&L {hist['avg_pnl']:+.2f}%, total ${hist['total_dollar_pnl']:+,.2f}"
        )

    # ── Signal Shadow-Log ───────────────────────────────────────────────
    # Auto-log this signal (whether or not it's ever taken as a real trade)
    # so the confidence score's real predictive power can be measured on an
    # unbiased sample, not just the trades Ahtisham chose to log manually.
    if v["agreement"] != "CONFLICT" and v.get("entry_low"):
        az.log_signal_shadow(
            coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
            direction=v["final_direction"], tp1=v["tp1"], tp2=v["tp2"], sl=v["sl"],
            timeframe=timeframe, confidence=v["accuracy"], vote_margin=v.get("vote_margin"),
            entry_low=v["entry_low"], entry_high=v["entry_high"],
            invalidate_price=v.get("invalidate_price"), github_token=github_token,
        )

    # ── Past SL-hit lessons for this exact coin+direction ──────────────
    # Surfaces prior setups on this coin that looked good (high confidence)
    # but still stopped out, along with WHY, so a repeat pattern gets extra
    # scrutiny before taking it again — not just a blind confidence number.
    if v["agreement"] != "CONFLICT":
        past_sl = az.sl_hit_lessons_for_coin(
            _cached_trades(github_token), s["base"], direction=v["final_direction"], min_confidence=60
        )
        if past_sl:
            with st.expander(f"⚠️ {s['base']} {v['final_direction']} setups jo pehle SL hit hue ({len(past_sl)}) — dekho pehle", expanded=False):
                for pt in past_sl[:5]:
                    st.markdown(
                        f"- **{pt.get('closed_at', '—')}** — confidence {pt.get('confidence', 0):.0f}%: "
                        f"{az.sl_hit_conclusion_text(pt)}"
                    )

    if v["agreement"] != "CONFLICT" and v["entry_low"]:
        st.divider()
        entry_ref = round((v["entry_low"] + v["entry_high"]) / 2, 8)

        pos = az.position_size(account_balance, risk_pct, entry_ref, v["sl"],
                                leverage if market_type == "futures" else 1)
        if pos:
            p1, p2, p3 = st.columns(3)
            p1.metric("Position Size", f"{pos['units']:,.4f} {s['base']}")
            p2.metric("Position Value", f"${pos['position_value']:,.2f}")
            p3.metric("Risking", f"${pos['risk_amount']:,.2f}")
            if market_type == "futures" and leverage > 1:
                st.caption(f"Margin required at {leverage}x leverage: ${pos['margin_required']:,.2f}")

        if market_type == "futures":
            safe_lev = az.suggest_max_safe_leverage(entry_ref, v["sl"])
            if safe_lev:
                l1, l2 = st.columns(2)
                l1.metric("🛡️ Safe Leverage (this trade)", f"{safe_lev['safe_leverage']}x")
                l2.metric("SL distance", f"{safe_lev['sl_distance_pct']:.2f}%")
                if leverage > safe_lev["safe_leverage"]:
                    st.warning(
                        f"⚠️ Sidebar mein {leverage}x set hai, lekin is trade ke SL distance "
                        f"({safe_lev['sl_distance_pct']:.2f}%) ke hisaab se ~{safe_lev['safe_leverage']}x "
                        f"se zyada leverage par liquidation SL se pehle aa sakti hai — trade SL "
                        f"par nahi, liquidation par (poora margin loss) band ho sakti hai."
                    )

        tcol1, tcol2, tcol3 = st.columns([2, 1.2, 1])
        with tcol1:
            st.caption(
                f"📒 Log this as a real trade — Entry ~{entry_ref:,.6f}, "
                f"TP1 {v['tp1']:,.6f}, TP2 {v['tp2']:,.6f}, SL {v['sl']:,.6f}"
            )
        with tcol2:
            stake_amt = st.number_input(
                "Amount ($)", min_value=0.0, value=10.0, step=5.0,
                key=f"stake_{key_prefix}",
                help="Demo balance mein se itna $ is trade mein daala jayega. 0 rakho agar sirf track karna hai, balance na chhuye.",
            )
        with tcol3:
            st.write("")
            if st.button("➕ Add to Tracker", key=f"track_{key_prefix}"):
                new_trade = az.add_trade(
                    coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
                    direction=v["final_direction"], entry=entry_ref,
                    tp1=v["tp1"], tp2=v["tp2"], sl=v["sl"], timeframe=timeframe,
                    github_token=github_token,
                    confidence=v["accuracy"], vote_margin=v.get("vote_margin"),
                    entry_low=v["entry_low"], entry_high=v["entry_high"],
                    invalidate_price=v.get("invalidate_price"),
                    stake=stake_amt if stake_amt > 0 else None,
                    leverage=leverage, atr_at_entry=indicators.get("atr"),
                )
                if github_token and not new_trade.get("_github_synced"):
                    st.error(
                        f"⚠️ Saved locally but GitHub sync FAILED — this trade will be "
                        f"lost on the next app restart unless this is fixed: "
                        f"{new_trade.get('_github_error') or 'unknown error'}. "
                        f"Use 'Test GitHub Connection' in the sidebar to diagnose."
                    )
                else:
                    st.success(
                        f"{s['base']} added as a PENDING setup — it only becomes a real "
                        f"open trade once price actually confirms at {entry_ref:,.6f}. "
                        f"Check the 📒 Trade Tracker tab."
                    )

    try:
        docx_bytes = az.generate_docx_bytes(chart, res["market"], funding, indicators, v, [], None)
        st.download_button(
            "📥 Download Word Report", data=docx_bytes,
            file_name=f"{s['base']}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl_{key_prefix}",
        )
    except Exception as e:
        st.caption(f"Report generation skipped: {e}")


with tab_live:
    st.subheader("Live multi-coin analysis")
    st.caption(
        "Bitget ke sare live coins/pairs yahan se select karo — Entry, TP, SL aur "
        "Direction automatically calculate ho jayega, har coin ke liye alag. "
        "'All' timeframe select karke ek hi coin ke liye sare timeframes (1m se 1d tak) "
        "ek sath compare bhi kar sakte ho."
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        market_type = st.radio("Market", ["spot", "futures"], horizontal=True,
                                format_func=lambda x: "Spot" if x == "spot" else "Futures")
    with c2:
        timeframe = st.selectbox(
            "Chart timeframe", ALL_TIMEFRAMES + ["All"],
            index=4, key="live_tf",
            help="'All' select karo taake har selected coin ka har timeframe (1m→1d) ek sath dikhe — "
                 "kis timeframe pe Long favor hai, kis pe Short, sab ek jagah.",
        )
    with c3:
        include_news = st.checkbox("Include news", value=False,
                                    help="Slower — one NewsAPI call per selected coin (per timeframe in 'All' mode).")

    is_all_tf = (timeframe == "All")
    if is_all_tf:
        st.info(
            "ℹ️ 'All' mode mein har coin ke liye 8 timeframes (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d) "
            "analyze honge — is liye yeh normal se kaafi slower hoga aur kam coins select karna behtar hai.",
            icon="ℹ️",
        )

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

        max_coins = 4 if is_all_tf else 12
        selected_labels = st.multiselect(
            f"Coins select karo ({len(symbols)} available on {market_type})",
            options=labels,
            max_selections=max_coins,
            help=(f"'All' timeframe mode mein max {max_coins} coins — har coin 8 timeframes analyze "
                  f"karega is liye zyada coins bohot slow ho jayenge." if is_all_tf else
                  "Ek baar mein max 12 coins — taake analysis fast aur reliable rahe."),
        )

        run_btn = st.button("🚀 Analyze Selected Coins", type="primary", disabled=not selected_labels)

        if run_btn:
            tfs_to_run = ALL_TIMEFRAMES if is_all_tf else [timeframe]
            results = []
            errors = []
            total_steps = max(len(selected_labels) * len(tfs_to_run), 1)
            step = 0
            progress = st.progress(0.0, text="Starting...")
            for lbl in selected_labels:
                s = label_to_symbol[lbl]
                tf_results = {}
                for tf in tfs_to_run:
                    step += 1
                    progress.progress(step / total_steps, text=f"Analyzing {s['base']} ({tf})...")
                    res = az.run_live_analysis(
                        coin_symbol=s["base"], pair=s["symbol"], market_type=market_type,
                        timeframe=tf, newsapi_key=newsapi_key, use_news=include_news,
                    )
                    if res and "error" not in res:
                        tf_results[tf] = res
                    else:
                        err_msg = res.get("error", "Unknown error") if res else "No response"
                        errors.append(f"{s['base']} ({tf}): {err_msg}")
                    time.sleep(0.3)
                if tf_results:
                    results.append((s, tf_results))
            progress.progress(1.0, text="Done!")
            time.sleep(0.3)
            progress.empty()
            st.session_state["live_results"] = results
            st.session_state["live_errors"] = errors
            st.session_state["live_mode_all"] = is_all_tf

        errors = st.session_state.get("live_errors", [])
        if errors:
            with st.expander(f"⚠️ {len(errors)} analysis attempt(s) failed — click for details"):
                for e in errors:
                    st.write(f"- {e}")

        results = st.session_state.get("live_results", [])
        mode_all = st.session_state.get("live_mode_all", False)

        if results and mode_all:
            st.divider()
            st.markdown("### 📋 Summary — every coin across every timeframe")
            st.caption(
                "Har row ek coin hai, har column ek timeframe — dekho kis timeframe pe woh coin "
                "abhi 🟢 LONG favor kar raha hai aur kis pe 🔴 SHORT, sath confidence % ke."
            )
            matrix_rows = []
            for s, tf_results in results:
                row = {"Coin": s["base"]}
                long_tfs, short_tfs = [], []
                for tf in ALL_TIMEFRAMES:
                    res = tf_results.get(tf)
                    if not res:
                        row[tf] = "—"
                        continue
                    v = res["verdict"]
                    dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                    row[tf] = f"{dir_emoji} {v['final_direction'][0]} {v['accuracy']:.0f}%"
                    if v["final_direction"] == "LONG":
                        long_tfs.append(tf)
                    else:
                        short_tfs.append(tf)
                row["Long on"] = ", ".join(long_tfs) if long_tfs else "—"
                row["Short on"] = ", ".join(short_tfs) if short_tfs else "—"
                matrix_rows.append(row)
            st.dataframe(matrix_rows, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### 🔍 Per-coin, per-timeframe details")
            for s, tf_results in results:
                available_tfs = [tf for tf in ALL_TIMEFRAMES if tf in tf_results]
                with st.expander(f"📌 {s['base']} — {len(available_tfs)} timeframe(s) analyzed"):
                    tf_tabs = st.tabs(available_tfs)
                    for tab, tf in zip(tf_tabs, available_tfs):
                        with tab:
                            res = tf_results[tf]
                            v = res["verdict"]
                            dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                            st.markdown(f"**{dir_emoji} {v['final_direction']} — {v['accuracy']:.0f}% confidence on {tf}**")
                            render_coin_tf_detail(
                                s, res, market_type, tf, github_token, account_balance,
                                risk_pct, leverage, key_prefix=f"{s['base']}_{s['symbol']}_{tf}",
                            )

        elif results:
            st.divider()
            st.markdown("### 📋 Summary — all selected coins")

            rows = []
            for s, tf_results in results:
                res = tf_results.get(timeframe) or next(iter(tf_results.values()))
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
            for s, tf_results in results:
                res = tf_results.get(timeframe) or next(iter(tf_results.values()))
                v = res["verdict"]
                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                with st.expander(f"{dir_emoji} {s['base']} — {v['final_direction']} ({v['accuracy']:.0f}% confidence)"):
                    render_coin_tf_detail(
                        s, res, market_type, timeframe, github_token, account_balance,
                        risk_pct, leverage, key_prefix=f"{s['base']}_{s['symbol']}",
                    )

        st.divider()
        st.caption("⚠️ Ye AI-assisted analysis hai, financial advice nahi. Hamesha apna stop-loss lagao — max 2% risk per trade.")



# ─────────────────────────────────────────────────────────────
#   TAB 1B — OPPORTUNITY SCANNER (auto-scan many coins at once)
# ─────────────────────────────────────────────────────────────
with tab_scan:
    st.subheader("Opportunity Scanner")
    st.caption(
        "Manually har coin check karne ke bajaye — yahan se ek click mein top volume "
        "coins scan ho jayenge aur sirf woh coins dikhenge jo abhi entry-worthy hain "
        "(confidence threshold ke upar, aur data/AI conflict nahi)."
    )

    sc1, sc2, sc3, sc4 = st.columns([1, 1, 1, 1])
    with sc1:
        scan_market = st.radio("Market", ["spot", "futures"], horizontal=True, key="scan_mkt",
                                format_func=lambda x: "Spot" if x == "spot" else "Futures")
    with sc2:
        scan_tf = st.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "2h", "4h", "1d"],
                                index=3, key="scan_tf")
    with sc3:
        scan_top_n = st.slider("Coins to scan", min_value=10, max_value=60, value=25, step=5,
                                help="Zyada coins = zyada accurate coverage, lekin zyada time lagega "
                                     "(Bitget API rate limits ki wajah se).")
    with sc4:
        scan_acc_range = st.slider(
            "Confidence range %", min_value=40, max_value=100, value=(65, 100), step=5,
            help="Sirf is range ke andar wale confidence score wale coins dikhenge. Upper bound ko "
                 "100 par rehne do agar 'X% aur usse zyada, sab' dekhna ho.",
        )
        scan_min_acc, scan_max_acc = scan_acc_range

    scan_news = st.checkbox("Include news sentiment in scan", value=False,
                             help="Slower — ek NewsAPI call per scanned coin.", key="scan_news")

    if st.button("🔍 Scan Now", type="primary"):
        log_box = st.empty()
        logs = []

        def scan_log(msg):
            logs.append(msg)
            log_box.info(logs[-1])

        with st.spinner(f"Scanning top {scan_top_n} {scan_market} coins..."):
            hits = az.scan_top_coins(
                scan_market, scan_tf, top_n=scan_top_n, min_accuracy=scan_min_acc,
                max_accuracy=scan_max_acc, newsapi_key=newsapi_key, use_news=scan_news, log=scan_log,
            )
        log_box.empty()
        st.session_state["scan_hits"] = hits
        st.session_state["scan_meta"] = {"market": scan_market, "tf": scan_tf,
                                          "min_acc": scan_min_acc, "max_acc": scan_max_acc}

    hits = st.session_state.get("scan_hits")
    if hits is not None:
        meta = st.session_state.get("scan_meta", {})
        range_txt = f"{meta.get('min_acc', 40)}%–{meta.get('max_acc', 100)}%"
        if not hits:
            st.info(f"{range_txt} confidence range mein abhi koi coin qualify nahi kar raha. Range badla karke dobara try karo.")
        else:
            st.success(f"{len(hits)} coin(s) mile jo {meta.get('tf','')} timeframe pe entry-worthy hain "
                       f"({meta.get('market','')} market, confidence {range_txt}):")

            rows = []
            for s, res in hits:
                v = res["verdict"]
                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                rows.append({
                    "Coin": s["base"],
                    "Direction": f"{dir_emoji} {v['final_direction']}",
                    "Confidence": f"{v['accuracy']:.0f}%",
                    "Entry Zone": f"${v['entry_low']:,.6f} - ${v['entry_high']:,.6f}" if v["entry_low"] else "N/A",
                    "TP1": f"${v['tp1']:,.6f}" if v["tp1"] else "N/A",
                    "SL": f"${v['sl']:,.6f}" if v["sl"] else "N/A",
                    "R:R": f"1:{v['rr']}" if v["rr"] != "N/A" else "N/A",
                    "RSI Divergence": v.get("rsi_divergence", "NONE").title(),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### 🔍 Details")
            for s, res in hits:
                v = res["verdict"]
                dir_emoji = "🟢" if v["final_direction"] == "LONG" else "🔴"
                if v.get("entry_low"):
                    az.log_signal_shadow(
                        coin_symbol=s["base"], pair=s["symbol"], market_type=scan_market,
                        direction=v["final_direction"], tp1=v["tp1"], tp2=v["tp2"], sl=v["sl"],
                        timeframe=scan_tf, confidence=v["accuracy"], vote_margin=v.get("vote_margin"),
                        entry_low=v["entry_low"], entry_high=v["entry_high"],
                        invalidate_price=v.get("invalidate_price"), github_token=github_token,
                    )
                with st.expander(f"{dir_emoji} {s['base']} — {v['final_direction']} ({v['accuracy']:.0f}% confidence)"):
                    e1, e2, e3, e4 = st.columns(4)
                    e1.metric("Entry Zone", f"{v['entry_low']:,.6f} - {v['entry_high']:,.6f}" if v["entry_low"] else "N/A")
                    e2.metric("Take Profit 1", f"{v['tp1']:,.6f}" if v["tp1"] else "N/A")
                    e3.metric("Take Profit 2", f"{v['tp2']:,.6f}" if v["tp2"] else "N/A")
                    e4.metric("Stop Loss", f"{v['sl']:,.6f}" if v["sl"] else "N/A")
                    st.caption(f"Risk:Reward = 1:{v['rr']}  |  {v['entry_note']}")

                    whale = res.get("whale", {})
                    if whale.get("available") or whale.get("wall_side"):
                        st.caption(f"🐋 Whale activity: {whale.get('note', 'N/A')}")

                    st.markdown("**Signal breakdown:**")
                    for level, text in v["factors"]:
                        icon = "✅" if level == "good" else ("⚠️" if level == "warn" else "❌")
                        st.markdown(f"- {icon} {text}")

                    hist = az.coin_trade_history(_cached_trades(github_token), s["base"])
                    if hist["count"] > 0:
                        st.caption(
                            f"📜 **{s['base']} ki pichli trades:** {hist['count']} closed — "
                            f"{hist['wins']} profit, {hist['losses']} loss ({hist['win_rate']:.0f}% win rate), "
                            f"avg P&L {hist['avg_pnl']:+.2f}%, total ${hist['total_dollar_pnl']:+,.2f}"
                        )

                    entry_mid = (v["entry_low"] + v["entry_high"]) / 2 if v["entry_low"] else None
                    pos = az.position_size(account_balance, risk_pct, entry_mid,
                                            v["sl"], leverage if scan_market == "futures" else 1)
                    if pos:
                        p1, p2, p3 = st.columns(3)
                        p1.metric("Position Size", f"{pos['units']:,.4f} {s['base']}")
                        p2.metric("Position Value", f"${pos['position_value']:,.2f}")
                        p3.metric("Risking", f"${pos['risk_amount']:,.2f}")

                    if scan_market == "futures" and entry_mid:
                        safe_lev = az.suggest_max_safe_leverage(entry_mid, v["sl"])
                        if safe_lev:
                            l1, l2 = st.columns(2)
                            l1.metric("🛡️ Safe Leverage (this trade)", f"{safe_lev['safe_leverage']}x")
                            l2.metric("SL distance", f"{safe_lev['sl_distance_pct']:.2f}%")
                            if leverage > safe_lev["safe_leverage"]:
                                st.warning(
                                    f"⚠️ Sidebar mein {leverage}x set hai, lekin is trade ke SL distance "
                                    f"({safe_lev['sl_distance_pct']:.2f}%) ke hisaab se ~{safe_lev['safe_leverage']}x "
                                    f"se zyada leverage par liquidation SL se pehle aa sakti hai."
                                )

            st.divider()
            st.caption("⚠️ Scanner bhi AI-assisted analysis hai, financial advice nahi. Hamesha apna stop-loss lagao.")
    else:
        st.caption("Abhi tak scan nahi chalaya — 'Scan Now' dabao.")


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

            library = az.load_library(github_token=github_token)
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

                    htf_trend = v.get("htf_trend")
                    htf_tf = v.get("htf_timeframe", "-")
                    if htf_trend and htf_trend != v["final_direction"] and htf_trend != "NEUTRAL":
                        st.warning(f"⚠️ Counter-trend: {htf_tf} higher-timeframe trend is {htf_trend}, this trade is {v['final_direction']}. Higher risk — size down or skip.")

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

    if not github_token:
        st.info("⚠️ GitHub Token nahi diya — patterns is session ke baad ya app restart hone par "
                 "delete ho sakte hain. Sidebar mein GitHub Token daalo permanent storage ke liye.")

    library = az.load_library(github_token=github_token)
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
            synced, sync_err = az.save_library(library, github_token=github_token)
            if github_token and not synced:
                st.error(f"⚠️ Deleted locally but GitHub sync FAILED: {sync_err or 'unknown error'}")
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
            library = az.load_library(github_token=github_token)
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
            synced, sync_err = az.save_library(library, github_token=github_token)
            if github_token and not synced:
                st.error(
                    f"⚠️ Patterns saved locally but GitHub sync FAILED — will be lost on next "
                    f"restart unless fixed: {sync_err or 'unknown error'}. "
                    f"Use 'Test GitHub Connection' in the sidebar to diagnose."
                )
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
    if not github_token:
        st.info("⚠️ GitHub Token nahi diya — trades is session ke baad ya app restart hone par "
                 "delete ho sakte hain. Sidebar mein GitHub Token daalo permanent storage ke liye.")

    # ── Demo / Paper Trading Balance ────────────────────────────────
    st.markdown("### 💵 Demo Balance (Paper Trading)")
    demo_bal = az.load_balance(github_token=github_token)
    if not demo_bal.get("initialized"):
        st.caption("Abhi koi demo balance set nahi hai. Ek amount daal ke shuru karo — jab bhi koi "
                   "trade close hogi (jisme tumne amount allocate kiya ho), balance khud update hoga.")
        dcol1, dcol2 = st.columns([2, 1])
        with dcol1:
            start_amt = st.number_input("Starting Demo Balance ($)", min_value=1.0, value=100.0, step=10.0)
        with dcol2:
            st.write("")
            st.write("")
            if st.button("🚀 Start Demo Balance"):
                az.set_demo_balance(start_amt, github_token=github_token)
                st.rerun()
    else:
        change = demo_bal["balance"] - demo_bal["starting_balance"]
        change_pct = (change / demo_bal["starting_balance"] * 100) if demo_bal["starting_balance"] else 0
        b1, b2, b3 = st.columns(3)
        b1.metric("Current Balance", f"${demo_bal['balance']:,.2f}", f"{change:+.2f} ({change_pct:+.1f}%)")
        b2.metric("Starting Balance", f"${demo_bal['starting_balance']:,.2f}")
        with b3:
            with st.expander("🔄 Reset"):
                reset_amt = st.number_input("New starting amount ($)", min_value=1.0, value=100.0, step=10.0, key="reset_bal")
                if st.button("Confirm Reset"):
                    az.set_demo_balance(reset_amt, github_token=github_token)
                    st.rerun()

    st.divider()

    tcol1, tcol2, tcol3 = st.columns([1, 1, 3])
    with tcol1:
        if st.button("🔄 Refresh & Check Status", type="primary"):
            with st.spinner("Checking live prices against TP/SL..."):
                az.refresh_all_trades(github_token=github_token)
                az.refresh_shadow_signals(github_token=github_token)
            st.rerun()
    with tcol2:
        if st.button("🔧 Repair Old P&L Data"):
            with st.spinner("Repairing historical P&L on already-closed trades..."):
                fixed_count = az.repair_and_save_trade_pnls(github_token=github_token)
            if fixed_count:
                st.success(f"Fixed {fixed_count} closed trade(s) whose P&L had drifted from live-price re-checks. Avg Win/Loss should now be accurate.")
            else:
                st.info("Nothing to repair — all closed trades already have correct P&L.")
            st.rerun()

    trades = az.load_trades(github_token=github_token)

    if not trades:
        st.info("Abhi koi trade track nahi ho raha. Live Dashboard mein kisi coin ki analysis kholo aur '➕ Add to Tracker' dabao.")
    else:
        stats = az.trade_stats(trades)
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("Pending", stats.get("pending", 0))
        s2.metric("Open Trades", stats["open"])
        s3.metric("Closed Trades", stats["closed"])
        s4.metric(
            "Win Rate",
            f"{stats['win_rate']:.0f}%" if stats["closed"] else "N/A",
            f"{stats['wins']}W / {stats['losses']}L" if stats["closed"] else None,
        )
        s5.metric("Avg Win", f"{stats['avg_win_pnl']:+.2f}%" if stats["wins"] else "N/A")
        s6.metric("Avg Loss", f"{stats['avg_loss_pnl']:+.2f}%" if stats["losses"] else "N/A")
        st.caption(
            f"📊 Total logged: {stats['total']} trades — {stats['pending']} pending, "
            f"{stats['open']} open, {stats['closed']} closed "
            f"({stats['wins']} win, {stats['losses']} loss, {stats['manual_closes']} manual)"
            + (f", {stats['invalidated']} invalidated" if stats.get("invalidated") else "")
        )

        perf = az.performance_by_confidence(trades)
        if any(p["trades"] > 0 for p in perf):
            st.divider()
            st.markdown("### 📈 Performance by Signal Strength")
            st.caption(
                "Tumhare apne closed trades se real feedback — jab tool ne 'High confidence' bola, "
                "kya woh waqai zyada jeete? Yeh confidence score ko blindly trust karne ke bajaye "
                "khud check karne ka tarika hai."
            )
            perf_rows = [
                {
                    "Confidence Bucket": p["bucket"],
                    "Trades": p["trades"],
                    "Win Rate": f"{p['win_rate']:.0f}%" if p["win_rate"] is not None else "—",
                    "Avg P&L": f"{p['avg_pnl']:+.2f}%" if p["avg_pnl"] is not None else "—",
                }
                for p in perf
            ]
            st.dataframe(perf_rows, use_container_width=True, hide_index=True)
            high = next((p for p in perf if p["bucket"].startswith("High") and p["trades"] >= 5), None)
            low = next((p for p in perf if p["bucket"].startswith("Low") and p["trades"] >= 5), None)
            if high and low and high["win_rate"] is not None and low["win_rate"] is not None:
                if high["win_rate"] <= low["win_rate"]:
                    st.warning(
                        "⚠️ Tumhare data mein High-confidence trades, Low-confidence trades se behtar "
                        "perform nahi kar rahe — confidence score ko zyada literally mat lo, sirf ek factor "
                        "samjho, guarantee nahi."
                    )
                else:
                    st.success("✅ High-confidence trades tumhare data mein waqai behtar perform kar rahe hain.")
            st.caption(
                "⚠️ Ye sirf un trades ka data hai jo tumne manually 'Add to Tracker' kiya — "
                "biased sample hai (jo trades achi lagi unhi ko add kiya hoga). Neeche 🕵️ Shadow-Log "
                "section unbiased comparison deta hai, jisme har generated signal count hota hai, "
                "chahe tumne trade li ho ya nahi."
            )

        # ── Signal Shadow-Log Stats ──────────────────────────────────────
        st.divider()
        st.markdown("### 🕵️ Unbiased Signal Accuracy (Shadow-Log)")
        st.caption(
            "Ye har us signal ko count karta hai jo Live Dashboard ya Opportunity Scanner mein "
            "kabhi bhi dikhaya gaya — chahe tumne 'Add to Tracker' kiya ho ya nahi. Isse pata chalta "
            "hai confidence score sach mein predictive hai ya sirf tumhari khud choose ki hui trades "
            "mein aisa lagta hai. Jitna zyada data collect hoga (100+ signals), utna reliable hoga."
        )
        shadow_signals = az.load_shadow_signals(github_token=github_token)
        if not shadow_signals:
            st.info("Abhi tak koi signal shadow-log nahi hua. Jaise hi Live Dashboard ya Scanner mein koi analysis dikhao, yahan auto-track hona shuru ho jayega.")
        else:
            shadow_stats = az.shadow_signal_stats(shadow_signals)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Total Signals Logged", shadow_stats["total_logged"])
            sc2.metric("Closed (TP/SL)", shadow_stats["total_closed"])
            sc3.metric("Still Pending/Open", shadow_stats["still_open_or_pending"])
            if shadow_stats["total_closed"] < 30:
                st.caption(f"⚠️ Sirf {shadow_stats['total_closed']} closed signals hain abhi — statistically meaningful conclusion ke liye 100+ ka wait karo.")
            shadow_rows = [
                {
                    "Confidence Bucket": b["bucket"],
                    "Signals": b["signals"],
                    "Win Rate": f"{b['win_rate']:.0f}%" if b["win_rate"] is not None else "—",
                    "Avg P&L": f"{b['avg_pnl']:+.2f}%" if b["avg_pnl"] is not None else "—",
                }
                for b in shadow_stats["by_confidence"]
            ]
            st.dataframe(shadow_rows, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("### 🔎 Coin History Search")
        st.caption("Koi bhi coin select karo — uski sab pichli closed trades (profit/loss/confidence) dikh jayengi.")
        traded_coins = sorted({t["coin"] for t in trades})
        if traded_coins:
            search_coin = st.selectbox("Coin", traded_coins, key="coin_history_search")
            hist = az.coin_trade_history(trades, search_coin)
            if hist["count"] == 0:
                st.caption(f"{search_coin} ki abhi koi closed trade nahi hai.")
            else:
                hc1, hc2, hc3, hc4 = st.columns(4)
                hc1.metric("Closed Trades", hist["count"])
                hc2.metric("Win Rate", f"{hist['win_rate']:.0f}%", f"{hist['wins']}W / {hist['losses']}L")
                hc3.metric("Avg P&L", f"{hist['avg_pnl']:+.2f}%")
                hc4.metric("Total $ P&L", f"${hist['total_dollar_pnl']:+,.2f}")
                hist_rows = [
                    {
                        "Direction": t["direction"],
                        "Confidence": f"{t['confidence']:.0f}%" if t.get("confidence") is not None else "—",
                        "Entry": f"{t['entry']:,.6f}",
                        "Exit": f"{t['exit_price']:,.6f}" if t.get("exit_price") else "N/A",
                        "Result": t["status"],
                        "P&L %": f"{t['pnl_pct']:+.2f}%" if t.get("pnl_pct") is not None else "—",
                        "P&L $": f"${t['dollar_pnl']:+,.2f}" if t.get("dollar_pnl") is not None else "—",
                        "Closed": t.get("closed_at") or "—",
                    }
                    for t in hist["trades"]
                ]
                st.dataframe(hist_rows, use_container_width=True, hide_index=True)

        st.divider()
        pending_trades = [t for t in trades if t["status"] == "PENDING"]
        open_trades = [t for t in trades if t["status"] == "OPEN"]
        closed_trades = [t for t in trades if t["status"] not in ("OPEN", "PENDING")]

        st.markdown("### 🟠 Pending Setups (waiting for breakout confirmation)")
        st.caption(
            "Ye abhi real open trades nahi hain — jab tak price actually confirmation zone "
            "(Entry Low–Entry High) tak nahi pahunchti, tab tak trade trigger nahi hota. Agar price "
            "ulta chali gayi aur invalidation level cross ho gaya, setup khud invalidate ho jayega."
        )
        if not pending_trades:
            st.caption("Koi pending setup nahi hai.")
        else:
            for t in pending_trades:
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                cur = t.get("current_price")
                with st.container(border=True):
                    h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
                    h1.markdown(f"**{dir_emoji} {t['coin']}** ({t['market_type']}, {t['timeframe']}) — added {t['opened_at']}")
                    h2.metric("Current", f"{cur:,.6f}" if cur else "—")
                    h3.metric("Confirms at", f"{t.get('entry_low') or t.get('planned_entry'):,.6f}" if t.get("entry_low") or t.get("planned_entry") else "—")
                    h4.metric("Invalidates at", f"{t.get('invalidate_price'):,.6f}" if t.get("invalidate_price") else "—")

        st.divider()
        st.markdown("### 🟡 Open Trades")
        if not open_trades:
            st.caption("Koi open trade nahi hai.")
        else:
            for t in open_trades:
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                cur = t.get("current_price")
                pnl = t.get("pnl_pct")
                pnl_txt = f"{pnl:+.2f}%" if pnl is not None else "—"
                stake = t.get("stake")
                with st.container(border=True):
                    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1])
                    stake_txt = f" — ${stake:,.2f} staked" if stake else ""
                    h1.markdown(f"**{dir_emoji} {t['coin']}** ({t['market_type']}, {t['timeframe']}) — opened {t['opened_at']}{stake_txt}")
                    h2.metric("Entry", f"{t['entry']:,.6f}")
                    h3.metric("Current", f"{cur:,.6f}" if cur else "—")
                    if stake and pnl is not None:
                        unrealized_dollar = stake * (pnl / 100) * (t.get("leverage") or 1)
                        h4.metric("Unrealized P&L", pnl_txt, f"${unrealized_dollar:+,.2f}")
                    else:
                        h4.metric("Unrealized P&L", pnl_txt)
                    with h5:
                        if st.button("✋ Close now", key=f"close_{t['id']}"):
                            az.close_trade_manually(t["id"], exit_price=cur, note="Manually closed", github_token=github_token)
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
                "INVALIDATED": "🚫 Invalidated (never triggered)",
            }
            rows = []
            for t in sorted(closed_trades, key=lambda x: x.get("closed_at") or "", reverse=True):
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                rows.append({
                    "Coin": f"{dir_emoji} {t['coin']}",
                    "Direction": t["direction"],
                    "Confidence": f"{t['confidence']:.0f}%" if t.get("confidence") is not None else "—",
                    "Entry": f"{t['entry']:,.6f}",
                    "Exit": f"{t['exit_price']:,.6f}" if t.get("exit_price") else "N/A",
                    "Result": status_map.get(t["status"], t["status"]),
                    "P&L %": f"{t['pnl_pct']:+.2f}%" if t.get("pnl_pct") is not None else "—",
                    "P&L $": f"${t['dollar_pnl']:+,.2f}" if t.get("dollar_pnl") is not None else "—",
                    "Leverage": f"{t.get('leverage', 1)}x",
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
                az.delete_trade(trade_id, github_token=github_token)
                st.rerun()

        # ── SL Hit Post-Mortems ─────────────────────────────────────────
        sl_hit_trades = [t for t in closed_trades if t.get("status") == "SL_HIT"]
        if sl_hit_trades:
            st.divider()
            st.markdown("### ❌ Stop-Loss Post-Mortems")
            st.caption(
                "Har SL_HIT trade ki wajah aur conclusion — takke agla trade lene se pehle "
                "same pattern/coin par thora zyada dhyan diya jaaye."
            )
            for t in sorted(sl_hit_trades, key=lambda x: x.get("closed_at") or "", reverse=True):
                dir_emoji = "🟢" if t["direction"] == "LONG" else "🔴"
                conf_txt = f"{t['confidence']:.0f}%" if t.get("confidence") is not None else "—"
                with st.expander(f"{dir_emoji} {t['coin']} — {t.get('closed_at', '—')} (confidence {conf_txt})"):
                    st.write(az.sl_hit_conclusion_text(t))
                    a = t.get("sl_hit_analysis")
                    if a and not a.get("whipsaw_checked"):
                        st.caption("↻ Whipsaw check abhi pending hai — SL hit hone ke ~30 min baad next refresh par pata chalega ke price wapas mudi ya nahi.")

        st.divider()
        st.caption(
            "✅ Refresh ab candle history check karta hai (last-checked se ab tak ka low/high), "
            "sirf abhi ka point price nahi — isse beech mein wick se SL/TP hit hona bhi pakda jayega. "
            "Phir bhi, bahut lambe gap ke baad refresh karo (jaise kai din) to purani candle history "
            "exchange par available na ho to woh window miss ho sakti hai — jitna jaldi refresh karoge, "
            "utna accurate. Bitget app/exchange par apna actual order hamesha confirm karo."
        )


# ─────────────────────────────────────────────────────────────
#   TAB 6 — BACKTEST (walk-forward simulation on historical candles)
# ─────────────────────────────────────────────────────────────
with tab_backtest:
    st.subheader("Backtest")
    st.caption(
        "Strategy ko past historical candles pe test karo — asli paisa risk kiye bagair "
        "yeh pata chalega ke is coin/timeframe pe technical signal (EMA + RSI) kaisa perform karta raha hai."
    )
    st.info(
        "ℹ️ Yeh backtest sirf EMA-stack + RSI signal use karta hai (order book, funding rate, "
        "news, Fear & Greed history free APIs se available nahi hai) — is liye yeh live tool ka "
        "exact replay nahi hai, balke uske technical core ka sanity-check hai.",
        icon="ℹ️",
    )

    bt1, bt2, bt3 = st.columns([1, 2, 1])
    with bt1:
        bt_market = st.radio("Market", ["spot", "futures"], horizontal=True, key="bt_mkt",
                              format_func=lambda x: "Spot" if x == "spot" else "Futures")
    with bt2:
        @st.cache_data(ttl=300, show_spinner=False)
        def _bt_symbols(mtype):
            return az.get_spot_symbols() if mtype == "spot" else az.get_futures_symbols()

        with st.spinner("Loading symbol list..."):
            bt_symbols = _bt_symbols(bt_market)
        bt_labels = [f"{s['base']}/USDT" for s in bt_symbols]
        bt_label_to_symbol = {f"{s['base']}/USDT": s for s in bt_symbols}
        bt_coin_label = st.selectbox(f"Coin ({len(bt_labels)} available)", bt_labels, key="bt_coin")
    with bt3:
        bt_tf = st.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "2h", "4h", "1d"],
                              index=3, key="bt_tf")

    bt4, bt5, bt6 = st.columns(3)
    with bt4:
        bt_candles = st.slider("Candles to test", min_value=150, max_value=1000, value=400, step=50,
                                help="Zyada candles = zyada history cover hogi, lekin utna hi purana data "
                                     "ho sakta hai jitna Bitget deta hai is timeframe ke liye.")
    with bt5:
        bt_tp_mult = st.number_input("TP distance (x risk)", min_value=1.0, max_value=6.0, value=2.0, step=0.5)
    with bt6:
        bt_sl_mult = st.number_input("SL distance (x ATR)", min_value=0.5, max_value=4.0, value=1.5, step=0.5)

    if st.button("🔁 Run Backtest", type="primary", disabled=not bt_labels):
        s = bt_label_to_symbol[bt_coin_label]
        with st.spinner(f"Backtesting {s['base']} on {bt_tf}..."):
            result = az.run_backtest(
                s["symbol"], bt_market, bt_tf, num_candles=bt_candles,
                tp_mult=bt_tp_mult, sl_mult=bt_sl_mult,
            )
        st.session_state["bt_result"] = result
        st.session_state["bt_coin_label"] = bt_coin_label

    result = st.session_state.get("bt_result")
    if result:
        if "error" in result:
            st.warning(result["error"])
        else:
            st.success(f"Backtest complete — {st.session_state.get('bt_coin_label','')} "
                       f"({result['timeframe']}, {result['total_trades']} trades)")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Total Trades", result["total_trades"])
            r2.metric("Win Rate", f"{result['win_rate']:.1f}%", f"{result['wins']}W / {result['losses']}L")
            r3.metric("Avg Win / Avg Loss", f"{result['avg_win_pnl']:+.2f}% / {result['avg_loss_pnl']:+.2f}%")
            r4.metric("Expectancy per trade", f"{result['expectancy_pct']:+.2f}%")

            st.caption(f"📊 Sum of all trade P&L% across the tested history: {result['total_pnl_pct']:+.2f}% "
                       f"(not compounded — a rough proxy for how the edge stacks up over many trades, "
                       f"not literal account growth).")

            if result["win_rate"] < 40:
                st.error("⚠️ Is coin/timeframe pe is basic EMA+RSI signal ka win rate kaafi kamzor raha hai historically.")
            elif result["expectancy_pct"] <= 0:
                st.warning("⚠️ Win rate theek hai lekin average loss, average win se bada hai — overall expectancy negative/flat hai.")
            else:
                st.success("✅ Is history mein is signal ki positive expectancy rahi hai.")

            st.divider()
            st.markdown("### 📋 Recent simulated trades (most recent first)")
            trade_rows = [
                {
                    "Direction": t["direction"],
                    "Entry": f"{t['entry']:,.6f}",
                    "Exit": f"{t['exit']:,.6f}",
                    "Outcome": t["outcome"],
                    "P&L %": f"{t['pnl_pct']:+.2f}%",
                    "Bars Held": t["bars_held"],
                }
                for t in result["trades"]
            ]
            st.dataframe(trade_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("Abhi tak backtest nahi chalaya — coin/timeframe select karke 'Run Backtest' dabao.")
