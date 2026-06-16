import streamlit as st
import pandas as pd
import sys
import textwrap
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

SENTIMENT_LABELS = {
    "very_positive": ("Muy positivo", "sentiment-pill--very-positive"),
    "positive": ("Positivo", "sentiment-pill--positive"),
    "neutral": ("Neutral", "sentiment-pill--neutral"),
    "negative": ("Negativo", "sentiment-pill--negative"),
    "very_negative": ("Muy negativo", "sentiment-pill--very-negative"),
}

TREND_LABELS = {
    "improving": ("↑ Mejorando", "trend-pill--up"),
    "declining": ("↓ Empeorando", "trend-pill--down"),
    "stable": ("→ Estable", "trend-pill--flat"),
}


@st.cache_resource
def get_adapter():
    return GUIAdapterService()


adapter = get_adapter()


def score_badge_class(score: float) -> str:
    if score >= 60:
        return "score-badge--high"
    if score >= 35:
        return "score-badge--mid"
    return "score-badge--low"


def format_sentiment_pill_inline(label: str | None, weighted: float | None) -> str:
    """Format sentiment as inline HTML for card rendering."""
    if not label:
        return '<span style="border-radius:999px; padding:6px 12px; background:rgba(148, 163, 184, 0.14); color:#64748b; font-weight:700; font-size:0.85rem; border:1px solid rgba(148, 163, 184, 0.24)">Sin datos</span>'

    sentiment_styles = {
        "very_positive": ("Muy positivo", "rgba(22, 163, 74, 0.22)", "#15803d"),
        "positive": ("Positivo", "rgba(34, 197, 94, 0.16)", "#16a34a"),
        "neutral": ("Neutral", "rgba(148, 163, 184, 0.2)", "#475569"),
        "negative": ("Negativo", "rgba(248, 113, 113, 0.18)", "#dc2626"),
        "very_negative": ("Muy negativo", "rgba(239, 68, 68, 0.24)", "#b91c1c"),
    }
    
    text, bg, color = sentiment_styles.get(label, ("Neutral", "rgba(148, 163, 184, 0.2)", "#475569"))
    value = f" ({weighted:+.2f})" if weighted is not None else ""
    return f'<span style="border-radius:999px; padding:6px 12px; background:{bg}; color:{color}; font-weight:700; font-size:0.85rem; border:1px solid {bg}">{escape(text)}{escape(value)}</span>'


def format_trend_pill_inline(trend: str | None) -> str:
    """Format trend as inline HTML for card rendering."""
    if not trend:
        return ""
    
    trend_styles = {
        "improving": ("↑ Mejorando", "rgba(34, 197, 94, 0.12)", "#15803d"),
        "declining": ("↓ Empeorando", "rgba(239, 68, 68, 0.12)", "#b91c1c"),
        "stable": ("→ Estable", "rgba(100, 116, 139, 0.12)", "#475569"),
    }
    
    text, bg, color = trend_styles.get(trend, ("", "rgba(100, 116, 139, 0.12)", "#475569"))
    if not text:
        return ""
    return f'<span style="border-radius:999px; padding:6px 12px; background:{bg}; color:{color}; font-weight:700; font-size:0.85rem; border:1px solid {bg}">{escape(text)}</span>'


def format_sentiment_pill(label: str | None, weighted: float | None) -> str:
    if not label:
        return '<span class="sentiment-pill sentiment-pill--unknown">Sin datos</span>'

    text, css_class = SENTIMENT_LABELS.get(label, ("Neutral", "sentiment-pill--neutral"))
    value = f" ({weighted:+.2f})" if weighted is not None else ""
    return f'<span class="sentiment-pill {css_class}">{escape(text)}{escape(value)}</span>'


def format_trend_pill(trend: str | None) -> str:
    if not trend:
        return ""
    text, css_class = TREND_LABELS.get(trend, ("", "trend-pill--flat"))
    if not text:
        return ""
    return f'<span class="trend-pill {css_class}">{escape(text)}</span>'


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
                border-radius: 10px;
                padding: 0.85rem 1rem;
            }

            div[data-testid="stMetric"] label {
                white-space: nowrap;
            }

            .ticker-card {
                border: 1px solid rgba(148, 163, 184, 0.28);
                border-radius: 14px;
                padding: 1rem 1.05rem;
                margin-bottom: 1rem;
                background: rgba(255, 255, 255, 0.96);
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
                color: #0f172a;
            }

            .ticker-card__head {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.65rem;
            }

            .ticker-card__symbol {
                font-size: 1.15rem;
                font-weight: 700;
                color: inherit;
            }

            .ticker-card__score {
                min-width: 3rem;
                text-align: center;
                border-radius: 999px;
                padding: 0.25rem 0.75rem;
                color: #ffffff;
                font-weight: 700;
            }

            .score-badge--high { background: #0f766e; }
            .score-badge--mid { background: #0369a1; }
            .score-badge--low { background: #64748b; }

            .ticker-card__sentiment-row {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.45rem;
                margin: 0.55rem 0 0.35rem;
            }

            .ticker-card__meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin: 0.45rem 0;
            }

            .ticker-card__pill {
                border-radius: 999px;
                padding: 0.2rem 0.65rem;
                background: rgba(148, 163, 184, 0.18);
                color: #0f172a;
                font-size: 0.8rem;
                font-weight: 700;
                border: 1px solid rgba(148, 163, 184, 0.24);
            }

            .ticker-card__pill--pos {
                background: rgba(34, 197, 94, 0.22);
                color: #0f172a;
                border-color: rgba(34, 197, 94, 0.26);
            }

            .ticker-card__pill--neg {
                background: rgba(239, 68, 68, 0.22);
                color: #0f172a;
                border-color: rgba(239, 68, 68, 0.24);
            }

            .sentiment-pill,
            .trend-pill {
                border-radius: 999px;
                padding: 0.22rem 0.65rem;
                font-size: 0.82rem;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
            }

            .sentiment-pill--very-positive {
                background: rgba(22, 163, 74, 0.22);
                color: #15803d;
            }

            .sentiment-pill--positive {
                background: rgba(34, 197, 94, 0.16);
                color: #16a34a;
            }

            .sentiment-pill--neutral {
                background: rgba(148, 163, 184, 0.2);
                color: #475569;
            }

            .sentiment-pill--negative {
                background: rgba(248, 113, 113, 0.18);
                color: #dc2626;
            }

            .sentiment-pill--very-negative {
                background: rgba(239, 68, 68, 0.24);
                color: #b91c1c;
            }

            .sentiment-pill--unknown {
                background: rgba(148, 163, 184, 0.14);
                color: #64748b;
            }

            .trend-pill--up {
                background: rgba(34, 197, 94, 0.12);
                color: #15803d;
            }

            .trend-pill--down {
                background: rgba(239, 68, 68, 0.12);
                color: #b91c1c;
            }

            .trend-pill--flat {
                background: rgba(100, 116, 139, 0.12);
                color: #475569;
            }

            .ticker-card__reasons {
                color: inherit;
                font-size: 0.88rem;
                line-height: 1.45;
                margin-top: 0.55rem;
                opacity: 0.92;
            }

            /* Dark theme overrides to improve contrast */
            [data-theme="dark"] .ticker-card,
            .theme-dark .ticker-card,
            .streamlit-expanderHeader .ticker-card {
                background: linear-gradient(145deg, rgba(10, 14, 22, 0.98) 0%, rgba(12, 17, 26, 0.96) 100%);
                border-color: rgba(148, 163, 184, 0.28);
                color: #f8fafc;
                box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
            }

            [data-theme="dark"] .ticker-card__symbol,
            .theme-dark .ticker-card__symbol {
                color: #e2e8f0;
                text-shadow: 0 1px 0 rgba(0, 0, 0, 0.45);
            }

            [data-theme="dark"] .ticker-card__reasons,
            .theme-dark .ticker-card__reasons {
                color: #cbd5e1;
                opacity: 0.98;
            }

            [data-theme="dark"] .ticker-card__pill {
                background: rgba(14,165,233,0.32);
                color: #ffffff;
                font-weight: 700;
            }

            [data-theme="dark"] .ticker-card__pill--pos {
                background: rgba(34,197,94,0.32);
                color: #ffffff;
            }

            [data-theme="dark"] .ticker-card__pill--neg {
                background: rgba(239,68,68,0.32);
                color: #ffffff;
            }

            [data-theme="dark"] .sentiment-pill,
            .theme-dark .sentiment-pill,
            [data-theme="dark"] .trend-pill,
            .theme-dark .trend-pill {
                color: #ffffff;
                box-shadow: none;
            }

            [data-theme="dark"] .sentiment-pill--very-positive,
            [data-theme="dark"] .trend-pill--up,
            .theme-dark .sentiment-pill--very-positive,
            .theme-dark .trend-pill--up {
                background: rgba(22,163,74,0.32);
                color: #ffffff;
            }

            [data-theme="dark"] .sentiment-pill--positive,
            .theme-dark .sentiment-pill--positive {
                background: rgba(34,197,94,0.28);
                color: #ffffff;
            }

            [data-theme="dark"] .sentiment-pill--neutral,
            [data-theme="dark"] .trend-pill--flat,
            .theme-dark .sentiment-pill--neutral,
            .theme-dark .trend-pill--flat {
                background: rgba(148,163,184,0.18);
                color: #e2e8f0;
            }

            [data-theme="dark"] .sentiment-pill--negative,
            [data-theme="dark"] .sentiment-pill--very-negative,
            [data-theme="dark"] .trend-pill--down,
            .theme-dark .sentiment-pill--negative,
            .theme-dark .sentiment-pill--very-negative,
            .theme-dark .trend-pill--down {
                background: rgba(239,68,68,0.32);
                color: #ffffff;
            }

            /* Ensure score badge text stays readable */
            [data-theme="dark"] .ticker-card__score,
            .theme-dark .ticker-card__score {
                color: #ffffff;
                text-shadow: 0 1px 0 rgba(0,0,0,0.4);
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
                score = float(row.get("score", 0))
                
                # Reasons handling
                raw_reasons = row.get("score_reasons", "")
                if not raw_reasons or pd.isna(raw_reasons):
                    reasons_html = '<div style="margin-top:10px; font-size:0.92rem; line-height:1.5; color:#64748b; font-style:italic">No hay catalizadores detectados en el periodo.</div>'
                else:
                    reasons_html = f'<div style="margin-top:10px; font-size:0.92rem; line-height:1.5; color:#334155">{escape(str(raw_reasons))}</div>'
                
                earnings = str(row.get("earnings", "No")).upper()
                filing = escape(str(row.get("latest_filing", "None")))
                news_count = int(row.get("news_count", 0) or 0)
                positive_news = int(row.get("positive_news", 0) or 0)
                negative_news = int(row.get("negative_news", 0) or 0)
                confidence = row.get("sentiment_confidence")
                
                # Confidence display
                confidence_html = ""
                if pd.notna(confidence) and float(confidence) > 0:
                    conf_val = int(float(confidence) * 100)
                    confidence_html = f'<span style="border-radius:999px; padding:6px 12px; background:rgba(148, 163, 184, 0.12); color:#64748b; font-weight:700; font-size:0.85rem; border:1px solid rgba(148, 163, 184, 0.2)">Confianza {conf_val}%</span>'

                # Sentiment and Trend handling
                weighted = row.get("weighted_sentiment")
                weighted_value = None
                if weighted is not None and weighted != "":
                    try:
                        weighted_value = float(weighted)
                    except Exception:
                        weighted_value = None
                
                sentiment_label = row.get("sentiment_label") or None
                if sentiment_label == "":
                        sentiment_label = None
                trend = row.get("sentiment_trend") or None
                if trend == "":
                        trend = None

                sentiment_pill = format_sentiment_pill_inline(sentiment_label, weighted_value)
                trend_pill = format_trend_pill_inline(trend)

                # Build pills conditionally
                pills_html = ""
                if news_count > 0:
                    pills_html += f'<span style="border-radius:999px; padding:6px 12px; background:rgba(148, 163, 184, 0.18); color:#0f172a; font-weight:700; font-size:0.85rem; border:1px solid rgba(148, 163, 184, 0.24)">📰 {news_count}</span>'
                if positive_news > 0:
                    pills_html += f'<span style="border-radius:999px; padding:6px 12px; background:rgba(34,197,94,0.22); color:#15803d; font-weight:700; font-size:0.85rem; border:1px solid rgba(34,197,94,0.26)">+{positive_news}</span>'
                if negative_news > 0:
                    pills_html += f'<span style="border-radius:999px; padding:6px 12px; background:rgba(239,68,68,0.22); color:#b91c1c; font-weight:700; font-size:0.85rem; border:1px solid rgba(239,68,68,0.24)">-{negative_news}</span>'
                if earnings == "YES" or earnings == "TODAY" or earnings == "TOMORROW":
                    label_e = "Earnings" if earnings == "YES" else f"Earnings {earnings.capitalize()}"
                    pills_html += f'<span style="border-radius:999px; padding:6px 12px; background:rgba(34,197,94,0.22); color:#15803d; font-weight:700; font-size:0.85rem; border:1px solid rgba(34,197,94,0.26)">📊 {label_e}</span>'
                if filing != "None" and filing.strip():
                    pills_html += f'<span style="border-radius:999px; padding:6px 12px; background:rgba(148, 163, 184, 0.18); color:#0f172a; font-weight:700; font-size:0.85rem; border:1px solid rgba(148, 163, 184, 0.24)">📄 {filing}</span>'

                # If no pills, show a subtle news empty state
                if not pills_html:
                    pills_html = '<span style="color:#94a3b8; font-size:0.85rem; font-weight:500">Sin catalizadores recientes</span>'

                pills_section = f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:4px">{pills_html}</div>'
                
                # Determine score badge color
                if score >= 60:
                    score_bg = "#0f766e"
                elif score >= 35:
                    score_bg = "#0284c7"
                else:
                    score_bg = "#64748b"

                # Build the card HTML without leading spaces in the multi-line string to prevent Markdown code block interpretation
                card_html = f"""<div style="border: 1px solid rgba(148, 163, 184, 0.28); border-radius:14px; padding:18px; background:#ffffff; color:#0f172a; font-family: system-ui, sans-serif; margin-bottom:16px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04)">
<div style="display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px">
<div style="font-weight:800; font-size:1.2rem; color:#0f172a; letter-spacing:-0.01em">{symbol}</div>
<div style="min-width:3rem; text-align:center; border-radius:999px; padding:5px 14px; color:#ffffff; font-weight:800; background:{score_bg}; font-size:1rem">{int(score)}</div>
</div>
<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px">
{sentiment_pill}
{trend_pill}
{confidence_html}
</div>
{pills_section}
{reasons_html}
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)


def render_watchlist_editor(key_prefix: str):
    st.subheader("Watchlist")
    st.caption(f"{len(st.session_state.watchlist)} símbolos cargados")

    input_mode = st.radio(
        "Modo de entrada",
        ["Text Area", "Data Editor"],
        horizontal=True,
        key=f"{key_prefix}_input_mode",
    )

    if input_mode == "Text Area":
        watchlist_str = st.text_area(
            "Símbolos",
            value="\n".join(st.session_state.watchlist),
            height=180,
            help="Usa comas o un símbolo por línea.",
            key=f"{key_prefix}_watchlist_text",
        )
        update_clicked = st.button("Actualizar watchlist", key=f"{key_prefix}_update_text")
        if update_clicked:
            st.session_state.watchlist = adapter.normalize_symbols(watchlist_str)
            st.success("Watchlist actualizada.")
    else:
        df_watchlist = pd.DataFrame({"Symbol": st.session_state.watchlist})
        edited_df = st.data_editor(
            df_watchlist,
            num_rows="dynamic",
            width="stretch",
            height=320,
            key=f"{key_prefix}_watchlist_editor",
        )
        update_clicked = st.button("Actualizar watchlist", key=f"{key_prefix}_update_editor")
        if update_clicked:
            new_symbols = edited_df["Symbol"].dropna().tolist()
            st.session_state.watchlist = sorted(
                {s.strip().upper() for s in new_symbols if s.strip()}
            )
            st.success("Watchlist actualizada.")

    save_col, reload_col = st.columns(2)
    if save_col.button(
        "Guardar config",
        help="Guardar la lista en config/watchlist.yaml",
        key=f"{key_prefix}_save",
    ):
        adapter.save_symbols_to_config(st.session_state.watchlist)
        st.success("Guardado en disco.")

    if reload_col.button(
        "Recargar config",
        help="Recargar desde config/watchlist.yaml",
        key=f"{key_prefix}_reload",
    ):
        st.session_state.watchlist = adapter.load_symbols_from_config()
        st.rerun()


def run_scan():
    if not st.session_state.watchlist:
        st.error("La watchlist está vacía.")
        return

    with st.spinner(f"Escaneando {len(st.session_state.watchlist)} símbolos..."):
        try:
            df = adapter.run_scan_for_symbols(st.session_state.watchlist)
            st.session_state.results_df = df
            st.session_state.last_run = datetime.now()
            st.success("Escaneo completado.")
        except Exception as e:
            st.error(f"Error en el escaneo: {e}")


def _sentiment_summary(df: pd.DataFrame) -> tuple[int, int, int]:
    positive = int((df["sentiment_label"].isin(["positive", "very_positive"])).sum()) if "sentiment_label" in df else 0
    negative = int((df["sentiment_label"].isin(["negative", "very_negative"])).sum()) if "sentiment_label" in df else 0
    neutral = len(df) - positive - negative
    return positive, neutral, negative


def render_results():
    df = st.session_state.results_df
    if df is None:
        st.info("Edita tu watchlist y ejecuta un escaneo para ver resultados.")
        return

    if df.empty:
        st.warning("El escaneo terminó pero no devolvió resultados.")
        return

    sorted_df = df.sort_values(by="score", ascending=False)
    pos_count, neu_count, neg_count = _sentiment_summary(sorted_df)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Score máximo", f"{int(sorted_df['score'].max())}")
    metric_cols[1].metric("Tickers", f"{len(sorted_df)}")
    metric_cols[2].metric("Sentimiento +", pos_count)
    metric_cols[3].metric("Sentimiento −", neg_count)
    metric_cols[4].metric(
        "Último escaneo",
        st.session_state.last_run.strftime("%H:%M:%S") if st.session_state.last_run else "N/A",
    )

    if neu_count:
        st.caption(f"{neu_count} ticker(s) con sentimiento neutral o sin datos.")

    st.subheader("Top candidatos por catalizadores")
    render_ticker_cards(sorted_df, max_cards=3)

    timestamp = (
        st.session_state.last_run.strftime("%Y%m%d_%H%M")
        if st.session_state.last_run
        else "scan"
    )
    csv = sorted_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar informe CSV",
        data=csv,
        file_name=f"scan_report_{timestamp}.csv",
        mime="text/csv",
    )

    # Prefer display-friendly columns if provided by adapter
    display_cols = ["symbol", "score"]
    # label
    display_cols.append("sentiment_label_display" if "sentiment_label_display" in sorted_df.columns else "sentiment_label")
    # weighted
    display_cols.append("weighted_sentiment_display" if "weighted_sentiment_display" in sorted_df.columns else "weighted_sentiment")
    # trend
    display_cols.append("sentiment_trend_display" if "sentiment_trend_display" in sorted_df.columns else "sentiment_trend")
    display_cols += ["sentiment_confidence", "positive_news", "negative_news", "news_count", "earnings", "latest_filing", "score_reasons"]
    available_cols = [c for c in display_cols if c in sorted_df.columns]

    with st.expander("Tabla completa de resultados", expanded=True):
        st.dataframe(sorted_df[available_cols], width="stretch", hide_index=True)


if "watchlist" not in st.session_state:
    st.session_state.watchlist = adapter.load_symbols_from_config()

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if "last_run" not in st.session_state:
    st.session_state.last_run = None

inject_mobile_styles()

st.title("📈 Stock Fundamental Scanner")
st.caption("Escáner local de catalizadores: noticias, earnings y filings SEC")

dashboard_tab, watchlist_tab, table_tab = st.tabs(["Escaneo", "Watchlist", "Resultados"])

with dashboard_tab:
    if st.button("🚀 Ejecutar escaneo fundamental", type="primary"):
        run_scan()
    st.caption(f"Watchlist: {len(st.session_state.watchlist)} símbolos")

    st.divider()
    render_results()

with watchlist_tab:
    render_watchlist_editor("main")

with table_tab:
    if st.session_state.results_df is None:
        st.info("Ejecuta un escaneo primero.")
    elif st.session_state.results_df.empty:
        st.warning("No hay resultados que mostrar.")
    else:
        render_ticker_cards(st.session_state.results_df)
