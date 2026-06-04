import streamlit as st
import pandas as pd
import sys
from html import escape
from pathlib import Path
from datetime import datetime

# Add project root to sys.path to allow imports from 'app'
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from app.services.gui_adapter_service import GUIAdapterService

# Page config
st.set_page_config(
    page_title="Stock Fundamental Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize adapter
@st.cache_resource
def get_adapter():
    return GUIAdapterService()

adapter = get_adapter()


def inject_mobile_styles():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 2rem;
                max-width: 1180px;
            }

            h1, h2, h3 {
                letter-spacing: 0;
            }

            div[data-testid="stMetric"] {
                background: rgba(148, 163, 184, 0.12);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 8px;
                padding: 0.85rem 1rem;
            }

            div[data-testid="stMetric"] label {
                white-space: nowrap;
            }

            .ticker-card {
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 8px;
                padding: 0.95rem;
                margin-bottom: 0.75rem;
                background: rgba(148, 163, 184, 0.08);
            }

            .ticker-card__head {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.45rem;
            }

            .ticker-card__symbol {
                font-size: 1.05rem;
                font-weight: 700;
                color: inherit;
            }

            .ticker-card__score {
                min-width: 3rem;
                text-align: center;
                border-radius: 999px;
                padding: 0.2rem 0.6rem;
                background: #0f766e;
                color: #ffffff;
                font-weight: 700;
            }

            .ticker-card__meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin: 0.45rem 0;
            }

            .ticker-card__pill {
                border-radius: 999px;
                padding: 0.16rem 0.5rem;
                background: rgba(14, 165, 233, 0.16);
                color: inherit;
                font-size: 0.8rem;
                font-weight: 600;
            }

            .ticker-card__reasons {
                color: inherit;
                font-size: 0.9rem;
                line-height: 1.45;
                margin-top: 0.5rem;
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-left: 0.8rem;
                    padding-right: 0.8rem;
                    padding-top: 0.75rem;
                }

                h1 {
                    font-size: 1.55rem !important;
                    line-height: 1.2 !important;
                }

                h2, h3 {
                    font-size: 1.1rem !important;
                }

                div[data-testid="stHorizontalBlock"] {
                    gap: 0.5rem;
                }

                div[data-testid="stButton"] > button,
                div[data-testid="stDownloadButton"] > button {
                    width: 100%;
                }

                div[data-testid="stMetric"] {
                    padding: 0.7rem 0.75rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_ticker_cards(df: pd.DataFrame, max_cards: int | None = None):
    if df.empty:
        return

    sorted_df = df.sort_values(by="score", ascending=False)
    if max_cards is not None:
        sorted_df = sorted_df.head(max_cards)

    for _, row in sorted_df.iterrows():
        symbol = escape(str(row.get("symbol", "")))
        score = escape(str(row.get("score", "")))
        reasons = escape(str(row.get("score_reasons", "") or "No scoring reasons available."))
        earnings = escape(str(row.get("earnings", "No")))
        filing = escape(str(row.get("latest_filing", "None")))
        news_count = escape(str(row.get("news_count", 0)))

        st.markdown(
            f"""
            <div class="ticker-card">
                <div class="ticker-card__head">
                    <div class="ticker-card__symbol">{symbol}</div>
                    <div class="ticker-card__score">{score}</div>
                </div>
                <div class="ticker-card__meta">
                    <span class="ticker-card__pill">News {news_count}</span>
                    <span class="ticker-card__pill">Earnings {earnings}</span>
                    <span class="ticker-card__pill">Filing {filing}</span>
                </div>
                <div class="ticker-card__reasons">{reasons}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_watchlist_editor(key_prefix: str):
    st.subheader("Watchlist")
    st.caption(f"{len(st.session_state.watchlist)} symbols loaded")

    input_mode = st.radio(
        "Input mode",
        ["Text Area", "Data Editor"],
        horizontal=True,
        key=f"{key_prefix}_input_mode",
    )

    if input_mode == "Text Area":
        watchlist_str = st.text_area(
            "Symbols",
            value="\n".join(st.session_state.watchlist),
            height=180,
            help="Use commas or one symbol per line.",
            key=f"{key_prefix}_watchlist_text",
        )
        update_clicked = st.button("Update Watchlist", key=f"{key_prefix}_update_text")
        if update_clicked:
            st.session_state.watchlist = adapter.normalize_symbols(watchlist_str)
            st.success("Watchlist updated.")
    else:
        df_watchlist = pd.DataFrame({"Symbol": st.session_state.watchlist})
        edited_df = st.data_editor(
            df_watchlist,
            num_rows="dynamic",
            width="stretch",
            height=320,
            key=f"{key_prefix}_watchlist_editor",
        )
        update_clicked = st.button("Update Watchlist", key=f"{key_prefix}_update_editor")
        if update_clicked:
            new_symbols = edited_df["Symbol"].dropna().tolist()
            st.session_state.watchlist = sorted(
                {s.strip().upper() for s in new_symbols if s.strip()}
            )
            st.success("Watchlist updated.")

    save_col, reload_col = st.columns(2)
    if save_col.button(
        "Save Config",
        help="Save current list to config/watchlist.yaml",
        key=f"{key_prefix}_save",
    ):
        adapter.save_symbols_to_config(st.session_state.watchlist)
        st.success("Saved to disk.")

    if reload_col.button(
        "Reload Config",
        help="Reload list from config/watchlist.yaml",
        key=f"{key_prefix}_reload",
    ):
        st.session_state.watchlist = adapter.load_symbols_from_config()
        st.rerun()


def run_scan():
    if not st.session_state.watchlist:
        st.error("Watchlist is empty.")
        return

    with st.spinner(f"Scanning {len(st.session_state.watchlist)} symbols..."):
        try:
            df = adapter.run_scan_for_symbols(st.session_state.watchlist)
            st.session_state.results_df = df
            st.session_state.last_run = datetime.now()
            st.success("Scan completed.")
        except Exception as e:
            st.error(f"Scan failed: {e}")


def render_results():
    df = st.session_state.results_df
    if df is None:
        st.info("Edit your watchlist and run a scan to see results.")
        return

    if df.empty:
        st.warning("The scan completed but returned no results.")
        return

    sorted_df = df.sort_values(by="score", ascending=False)

    metric_cols = st.columns(3)
    metric_cols[0].metric("Top Score", f"{int(sorted_df['score'].max())}")
    metric_cols[1].metric("Tickers", f"{len(sorted_df)}")
    metric_cols[2].metric(
        "Last Run",
        st.session_state.last_run.strftime("%H:%M:%S") if st.session_state.last_run else "N/A",
    )

    st.subheader("Top Catalyst Candidates")
    render_ticker_cards(sorted_df, max_cards=3)

    timestamp = (
        st.session_state.last_run.strftime("%Y%m%d_%H%M")
        if st.session_state.last_run
        else "scan"
    )
    csv = sorted_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV Report",
        data=csv,
        file_name=f"scan_report_{timestamp}.csv",
        mime="text/csv",
    )

    with st.expander("Full results table", expanded=True):
        st.dataframe(sorted_df, width="stretch", hide_index=True)

# Initialize session state
if "watchlist" not in st.session_state:
    st.session_state.watchlist = adapter.load_symbols_from_config()

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if "last_run" not in st.session_state:
    st.session_state.last_run = None

inject_mobile_styles()

st.title("📈 Stock Fundamental Scanner")
st.caption("Local catalyst scanner: news, earnings, and SEC filings")

dashboard_tab, watchlist_tab, table_tab = st.tabs(["Scan", "Watchlist", "Results"])

with dashboard_tab:
    if st.button("🚀 Run Fundamental Scan", type="primary"):
        run_scan()
    st.caption(f"Watchlist: {len(st.session_state.watchlist)} symbols")

    st.divider()
    render_results()

with watchlist_tab:
    render_watchlist_editor("main")

with table_tab:
    if st.session_state.results_df is None:
        st.info("Run a scan first.")
    elif st.session_state.results_df.empty:
        st.warning("No results to display.")
    else:
        render_ticker_cards(st.session_state.results_df)
