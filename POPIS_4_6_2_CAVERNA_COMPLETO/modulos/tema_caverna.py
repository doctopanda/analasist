from __future__ import annotations

import html
from typing import Iterable

import streamlit as st

NAVY = "#14213D"
CORAL = "#E76F76"
CORAL_DARK = "#C94F5C"
BLUSH = "#FCECEE"
BG = "#F4F6F9"
CARD = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#6B7280"
BLUE = "#3A86FF"
GREEN = "#2A9D8F"
PURPLE = "#7B61FF"
AMBER = "#F4A261"
RED = "#D1495B"

PLOTLY_COLORS = [NAVY, CORAL, GREEN, BLUE, PURPLE, AMBER, RED]


def apply_theme() -> None:
    """Aplica el lenguaje visual CAVERNA a toda la página Streamlit."""
    st.markdown(
        f"""
        <style>
        :root {{
            --popis-navy: {NAVY};
            --popis-coral: {CORAL};
            --popis-coral-dark: {CORAL_DARK};
            --popis-bg: {BG};
            --popis-card: {CARD};
            --popis-text: {TEXT};
            --popis-muted: {MUTED};
        }}
        .stApp {{ background: {BG}; color: {TEXT}; }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #101C35 0%, {NAVY} 55%, #172845 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }}
        [data-testid="stSidebar"] * {{ color: #F8FAFC; }}
        [data-testid="stSidebar"] a {{ color: #F8FAFC !important; }}
        [data-testid="stSidebarNav"] li {{ border-radius: 12px; margin: 3px 8px; }}
        [data-testid="stSidebarNav"] li:hover {{ background: rgba(231,111,118,.16); }}
        [data-testid="stSidebarNav"] li:has(a[aria-current="page"]) {{
            background: linear-gradient(90deg, rgba(231,111,118,.94), rgba(201,79,92,.88));
            box-shadow: 0 8px 24px rgba(0,0,0,.15);
        }}
        .block-container {{ max-width: 1500px; padding-top: 1.25rem; padding-bottom: 3rem; }}
        h1, h2, h3 {{ color: {NAVY}; letter-spacing: -0.02em; }}
        h2, h3 {{ font-weight: 800 !important; }}
        hr {{ border-color: #E7EAF0; }}
        div[data-testid="stMetric"] {{
            background: {CARD};
            border: 1px solid #E8EAF0;
            border-top: 4px solid {CORAL};
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 10px 26px rgba(20,33,61,.07);
            min-height: 112px;
        }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED}; font-weight: 700; }}
        div[data-testid="stMetricValue"] {{ color: {NAVY}; font-weight: 900; }}
        div[data-testid="stDataFrame"], div[data-testid="stTable"],
        [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {{
            background: {CARD}; border: 1px solid #E7EAF0; border-radius: 18px;
            padding: 8px; box-shadow: 0 9px 28px rgba(20,33,61,.055);
        }}
        div[data-testid="stExpander"] {{
            background: {CARD}; border: 1px solid #E7EAF0; border-radius: 16px;
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: 12px; border: 0; font-weight: 800;
            background: {NAVY}; color: white; min-height: 42px;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background: {CORAL}; color: white; border: 0;
        }}
        div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
            border-radius: 12px !important; border-color: #DDE2EA !important;
        }}
        [data-testid="stAlert"] {{ border-radius: 14px; }}
        .popis-hero {{
            background: linear-gradient(105deg, #FFF6F7 0%, #FCECEE 48%, #F7E7EB 100%);
            border: 1px solid #F4D8DD; border-radius: 24px; padding: 22px 26px;
            margin-bottom: 18px; box-shadow: 0 12px 34px rgba(87,34,50,.08);
            display: flex; align-items: center; justify-content: space-between; gap: 22px;
        }}
        .popis-brand {{ display:flex; align-items:center; gap:18px; }}
        .popis-symbol {{
            width: 62px; height: 62px; border-radius: 19px;
            background: {NAVY}; color:white; display:flex; align-items:center; justify-content:center;
            font-size:31px; box-shadow: 0 10px 24px rgba(20,33,61,.18);
        }}
        .popis-title {{ font-size: 34px; line-height: 1; font-weight: 950; color:{NAVY}; }}
        .popis-subtitle {{ color:{MUTED}; font-size: 14px; font-weight:650; margin-top:7px; }}
        .popis-badges {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }}
        .popis-badge {{
            display:inline-block; border-radius:999px; padding:5px 10px; font-size:11px;
            font-weight:850; letter-spacing:.03em; background:white; color:{CORAL_DARK};
            border:1px solid #F0C9D0;
        }}
        .popis-cutoff {{
            min-width:170px; background:white; border-radius:17px; padding:13px 16px;
            border:1px solid #E9D7DB; text-align:right;
        }}
        .popis-cutoff small {{ color:{MUTED}; font-weight:700; }}
        .popis-cutoff strong {{ color:{NAVY}; font-size:20px; }}
        .popis-section-title {{
            color:{CORAL_DARK}; font-size:17px; font-weight:900; letter-spacing:.01em;
            margin: 16px 0 8px 0;
        }}
        .popis-card {{
            background:white; border:1px solid #E7EAF0; border-radius:18px; padding:16px 18px;
            box-shadow: 0 9px 26px rgba(20,33,61,.055); margin-bottom:12px;
        }}
        .popis-note {{ color:{MUTED}; font-size:12px; }}
        @media (max-width: 780px) {{
            .popis-hero {{ flex-direction:column; align-items:flex-start; }}
            .popis-cutoff {{ width:100%; text-align:left; }}
            .popis-title {{ font-size:28px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str = "POPIS", subtitle: str | None = None, cutoff: str | None = None,
         badges: Iterable[str] | None = None, symbol: str = "🧬") -> None:
    subtitle = subtitle or "Procesador Operativo de Patógenos e Indicadores Sanitarios"
    badge_html = "".join(f'<span class="popis-badge">{html.escape(str(b))}</span>' for b in (badges or []))
    cutoff_html = ""
    if cutoff:
        cutoff_html = (
            f'<div class="popis-cutoff"><small>CORTE EPIDEMIOLÓGICO</small><br>'
            f'<strong>{html.escape(str(cutoff))}</strong></div>'
        )
    st.markdown(
        f"""
        <div class="popis-hero">
          <div class="popis-brand">
            <div class="popis-symbol">{html.escape(symbol)}</div>
            <div>
              <div class="popis-title">{html.escape(title)}</div>
              <div class="popis-subtitle">{html.escape(subtitle)}</div>
              <div class="popis-badges">{badge_html}</div>
            </div>
          </div>
          {cutoff_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="popis-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def card(text: str) -> None:
    st.markdown(f'<div class="popis-card">{text}</div>', unsafe_allow_html=True)


def style_plotly(fig, title: str | None = None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=TEXT, family="Arial"),
        title=dict(text=title or fig.layout.title.text, font=dict(color=CORAL_DARK, size=18)),
        margin=dict(l=35, r=20, t=55, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E7EAF0")
    fig.update_yaxes(gridcolor="#EEF1F5", zerolinecolor="#E7EAF0")
    return fig
