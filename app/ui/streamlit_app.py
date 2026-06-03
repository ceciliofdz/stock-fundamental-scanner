import streamlit as st
import pandas as pd
import sys
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
    layout="wide"
)

# Initialize adapter
@st.cache_resource
def get_adapter():
    return GUIAdapterService()

adapter = get_adapter()

# Initialize session state
if "watchlist" not in st.session_state:
    st.session_state.watchlist = adapter.load_symbols_from_config()

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if "last_run" not in st.session_state:
    st.session_state.last_run = None

# --- UI Header ---
st.title("📈 Stock Fundamental Scanner")
st.markdown("### Local catalyst scanner (News, Earnings, Filings)")
st.caption("Using Marketaux, Finnhub, and SEC EDGAR APIs")

# --- Watchlist Section ---
st.sidebar.header("📋 Watchlist")

# Watchlist input mode toggle
input_mode = st.sidebar.radio("Input Mode", ["Text Area", "Data Editor"])

if input_mode == "Text Area":
    watchlist_str = st.sidebar.text_area(
        "Symbols (comma or newline separated)",
        value="\n".join(st.session_state.watchlist),
        height=300
    )
    if st.sidebar.button("Update Watchlist"):
        st.session_state.watchlist = adapter.normalize_symbols(watchlist_str)
        st.success("Watchlist updated!")
else:
    # Data Editor mode
    df_watchlist = pd.DataFrame({"Symbol": st.session_state.watchlist})
    edited_df = st.sidebar.data_editor(df_watchlist, num_rows="dynamic", width="stretch")
    if st.sidebar.button("Update Watchlist"):
        new_symbols = edited_df["Symbol"].dropna().tolist()
        st.session_state.watchlist = sorted(list(set([s.strip().upper() for s in new_symbols if s.strip()])))
        st.success("Watchlist updated!")

st.sidebar.write(f"Count: **{len(st.session_state.watchlist)}**")

col_actions1, col_actions2 = st.sidebar.columns(2)

if col_actions1.button("💾 Save Config", help="Save current list to config/watchlist.yaml"):
    adapter.save_symbols_to_config(st.session_state.watchlist)
    st.sidebar.success("Saved to disk!")

if col_actions2.button("🔄 Reload Config", help="Reload list from config/watchlist.yaml"):
    st.session_state.watchlist = adapter.load_symbols_from_config()
    st.rerun()

# --- Main Scan Action ---
if st.button("🚀 Run Fundamental Scan", type="primary"):
    if not st.session_state.watchlist:
        st.error("Watchlist is empty!")
    else:
        with st.spinner(f"Scanning {len(st.session_state.watchlist)} symbols..."):
            try:
                df = adapter.run_scan_for_symbols(st.session_state.watchlist)
                st.session_state.results_df = df
                st.session_state.last_run = datetime.now()
                st.success("Scan completed!")
            except Exception as e:
                st.error(f"Scan failed: {e}")

# --- Results Display ---
if st.session_state.results_df is not None:
    st.divider()
    
    # Run Info
    col1, col2, col3 = st.columns(3)
    col1.metric("Top Score", f"{int(st.session_state.results_df['score'].max())}")
    col2.metric("Tickers Scanned", f"{len(st.session_state.results_df)}")
    col3.metric("Last Run", st.session_state.last_run.strftime("%H:%M:%S") if st.session_state.last_run else "N/A")
    
    # Download Button
    timestamp = st.session_state.last_run.strftime("%Y%m%d_%H%M")
    csv = st.session_state.results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV Report",
        data=csv,
        file_name=f"scan_report_{timestamp}.csv",
        mime='text/csv',
    )
    
    # Results Table
    st.dataframe(
        st.session_state.results_df.sort_values(by="score", ascending=False),
        width="stretch",
        hide_index=True
    )
    
    # Top 3 Highlights
    st.subheader("🔥 Top Catalyst Candidates")
    top_3 = st.session_state.results_df.nlargest(3, "score")
    cols = st.columns(len(top_3))
    for i, (_, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.info(f"**{row['symbol']}** (Score: {row['score']})\n\n{row['score_reasons']}")
else:
    st.info("👈 Edit your watchlist and click 'Run Fundamental Scan' to see results.")
