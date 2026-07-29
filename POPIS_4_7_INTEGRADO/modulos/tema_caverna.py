from __future__ import annotations

import html
from typing import Any

import streamlit as st


# Identidad visual inspirada en CAVERNA, adaptada a POPIS/EDA.
NAVY = "#081F3D"
NAVY_2 = "#0D2B50"
CORAL = "#D92D55"
CORAL_DARK = "#B91F45"
PEACH = "#FFF0EF"
BLUE = "#3478D4"
GREEN = "#21A67A"
PURPLE = "#8857D9"
PINK = "#EF5A86"
INK = "#102A4C"
MUTED = "#66758A"
BG = "#F5F7FB"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"


def aplicar_tema_caverna() -> None:
    """Inyecta el tema CAVERNA en la página Streamlit actual.

    No modifica datos ni lógica epidemiológica. Está diseñada para poder llamarse
    en cada página de una app multipágina.
    """
    st.markdown(
        f"""
        <style>
        :root {{
          --popis-navy: {NAVY};
          --popis-navy-2: {NAVY_2};
          --popis-coral: {CORAL};
          --popis-coral-dark: {CORAL_DARK};
          --popis-peach: {PEACH};
          --popis-blue: {BLUE};
          --popis-green: {GREEN};
          --popis-purple: {PURPLE};
          --popis-pink: {PINK};
          --popis-ink: {INK};
          --popis-muted: {MUTED};
          --popis-bg: {BG};
          --popis-card: {CARD};
          --popis-border: {BORDER};
        }}

        html, body, [class*="css"] {{
          font-family: Inter, "Segoe UI", Arial, sans-serif;
        }}

        .stApp {{
          background: var(--popis-bg);
          color: var(--popis-ink);
        }}

        header[data-testid="stHeader"] {{
          background: rgba(245, 247, 251, 0.82);
          backdrop-filter: blur(8px);
        }}

        [data-testid="stAppViewContainer"] > .main {{
          background: var(--popis-bg);
        }}

        .block-container {{
          padding-top: 1.15rem;
          padding-bottom: 2.5rem;
          max-width: 1680px;
        }}

        /* Sidebar CAVERNA */
        section[data-testid="stSidebar"] {{
          background: linear-gradient(180deg, #071B36 0%, #0A2447 55%, #06182F 100%);
          border-right: 1px solid rgba(255,255,255,.08);
        }}
        section[data-testid="stSidebar"] * {{ color: #F7FAFF; }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label {{ color: #F7FAFF !important; }}
        section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.13); }}

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
          border-radius: 9px;
          margin: 2px 7px;
          padding-top: .46rem;
          padding-bottom: .46rem;
          transition: background .15s ease, transform .15s ease;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
          background: rgba(255,255,255,.09);
          transform: translateX(2px);
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
          background: linear-gradient(90deg, {CORAL_DARK}, {CORAL});
          box-shadow: 0 8px 20px rgba(217,45,85,.22);
        }}

        /* Encabezado tipo CAVERNA */
        .popis-hero {{
          position: relative;
          overflow: hidden;
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 18px;
          align-items: center;
          padding: 16px 20px;
          margin: 0 0 16px 0;
          border: 1px solid #F4DCDD;
          border-radius: 16px;
          background:
            radial-gradient(circle at 92% 110%, rgba(235,91,116,.16) 0 72px, transparent 73px),
            radial-gradient(circle at 86% 108%, rgba(235,91,116,.10) 0 112px, transparent 113px),
            linear-gradient(100deg, #FFF7F5 0%, #FFF0EF 58%, #FFE6E7 100%);
          box-shadow: 0 8px 24px rgba(12, 35, 65, .06);
        }}
        .popis-hero-icon {{
          width: 74px;
          height: 74px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 18px;
          font-size: 42px;
          background: linear-gradient(145deg, #FFB8C5, #F45A78);
          box-shadow: inset 0 0 0 1px rgba(255,255,255,.7), 0 9px 20px rgba(210,43,81,.16);
        }}
        .popis-brand-row {{ display:flex; align-items:center; gap:13px; flex-wrap:wrap; }}
        .popis-brand {{
          margin: 0;
          font-size: clamp(2rem, 4.2vw, 4.35rem);
          line-height: .9;
          letter-spacing: .025em;
          font-weight: 900;
          color: var(--popis-navy);
        }}
        .popis-divider {{ width: 4px; height: 48px; border-radius: 6px; background: var(--popis-coral); }}
        .popis-subtitle {{
          max-width: 620px;
          font-size: clamp(.92rem, 1.45vw, 1.22rem);
          line-height: 1.2;
          font-weight: 700;
          color: var(--popis-navy);
        }}
        .popis-badges {{ display:flex; gap:8px; margin-top:9px; flex-wrap:wrap; }}
        .popis-badge {{
          display:inline-flex; align-items:center; min-height:26px;
          padding: 4px 12px; border-radius:999px; font-size:.72rem; font-weight:800;
          letter-spacing:.02em;
        }}
        .popis-badge-coral {{ color:white; background:var(--popis-coral); }}
        .popis-badge-navy {{ color:white; background:var(--popis-navy); }}
        .popis-cut {{
          min-width: 190px;
          padding: 11px 14px;
          border-radius: 13px;
          border: 1px solid rgba(10,40,75,.10);
          background: rgba(255,255,255,.82);
          box-shadow: 0 4px 16px rgba(18,46,79,.06);
        }}
        .popis-cut-label {{ color:var(--popis-muted); font-size:.73rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
        .popis-cut-value {{ color:var(--popis-coral); font-size:1.05rem; font-weight:900; margin-top:3px; }}
        .popis-cut-source {{ color:var(--popis-muted); font-size:.68rem; line-height:1.25; margin-top:5px; }}

        /* Títulos y separadores */
        h1, h2, h3 {{ color: var(--popis-ink); letter-spacing: -.012em; }}
        h3, h4 {{ color: var(--popis-coral-dark) !important; font-weight: 850 !important; }}
        .popis-section-title {{
          color:var(--popis-coral-dark); font-size:1.02rem; font-weight:900;
          letter-spacing:.015em; text-transform:uppercase; margin: .2rem 0 .75rem 0;
        }}

        /* Tarjetas, métricas y contenedores */
        div[data-testid="stMetric"] {{
          background: var(--popis-card);
          border: 1px solid var(--popis-border);
          border-radius: 14px;
          padding: 13px 15px;
          min-height: 112px;
          box-shadow: 0 5px 14px rgba(12,37,69,.045);
        }}
        div[data-testid="stMetric"] label {{
          color: var(--popis-ink) !important;
          font-weight: 800 !important;
          font-size: .74rem !important;
          text-transform: uppercase;
          letter-spacing: .025em;
        }}
        div[data-testid="stMetricValue"] {{ color: var(--popis-navy); font-weight: 900; }}
        div[data-testid="stMetricDelta"] {{ font-weight: 700; }}

        div[data-testid="stExpander"] {{
          background: white;
          border: 1px solid var(--popis-border);
          border-radius: 13px;
          box-shadow: 0 4px 13px rgba(12,37,69,.035);
        }}

        [data-testid="stDataFrame"], [data-testid="stTable"] {{
          border: 1px solid var(--popis-border);
          border-radius: 13px;
          overflow: hidden;
          background: white;
        }}

        /* Inputs */
        [data-baseweb="select"] > div,
        [data-testid="stFileUploader"] section,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {{
          border-radius: 10px !important;
          border-color: #CDD7E5 !important;
          background: white !important;
        }}

        /* Botones */
        .stButton > button[kind="primary"], .stDownloadButton > button {{
          border-radius: 10px;
          font-weight: 800;
          border: 1px solid {CORAL};
        }}
        .stButton > button[kind="primary"] {{
          background: linear-gradient(90deg, {CORAL_DARK}, {CORAL});
          color: white;
        }}
        .stButton > button:not([kind="primary"]) {{
          border-radius: 10px;
          font-weight: 750;
          border-color: #C7D2E2;
        }}

        /* Alertas */
        div[data-testid="stAlert"] {{ border-radius: 12px; }}

        /* Gráficas */
        [data-testid="stPlotlyChart"], [data-testid="stPyplotGlobalUse"] {{
          background: white;
          border: 1px solid var(--popis-border);
          border-radius: 14px;
          padding: 7px;
          box-shadow: 0 4px 13px rgba(12,37,69,.035);
        }}

        .popis-note {{
          margin-top:14px; padding:11px 14px; border:1px solid #D8E2EF; border-radius:11px;
          background:#F9FBFE; color:var(--popis-muted); font-size:.78rem;
        }}

        @media (max-width: 900px) {{
          .popis-hero {{ grid-template-columns: auto 1fr; }}
          .popis-cut {{ grid-column: 1 / -1; min-width: 0; }}
          .popis-divider {{ display:none; }}
          .popis-brand {{ font-size:2.4rem; }}
          .popis-hero-icon {{ width:58px; height:58px; font-size:34px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def cabecera_popis(
    *,
    corte: str | None = None,
    fuente: str | None = None,
    version: str = "v4.8",
    etiqueta: str = "VIGILANCIA EDA · TABLERO AVANZADO",
) -> None:
    corte = html.escape(corte or "Corte automático")
    fuente = html.escape(fuente or "SINAVE EDA + SUIVE/SUAVE + población")
    version = html.escape(version)
    etiqueta = html.escape(etiqueta)
    st.markdown(
        f"""
        <div class="popis-hero">
          <div class="popis-hero-icon" aria-hidden="true">🧫</div>
          <div>
            <div class="popis-brand-row">
              <div class="popis-brand">POPIS</div>
              <div class="popis-divider"></div>
              <div class="popis-subtitle">Procesador Operativo de Patógenos e Indicadores Sanitarios</div>
            </div>
            <div class="popis-badges">
              <span class="popis-badge popis-badge-coral">{version}</span>
              <span class="popis-badge popis-badge-navy">{etiqueta}</span>
            </div>
          </div>
          <div class="popis-cut">
            <div class="popis-cut-label">Corte de información</div>
            <div class="popis-cut-value">{corte}</div>
            <div class="popis-cut-source">Fuente: {fuente}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def titulo_seccion(texto: str) -> None:
    st.markdown(f'<div class="popis-section-title">{html.escape(texto)}</div>', unsafe_allow_html=True)


def nota_metodologica(texto: str) -> None:
    st.markdown(f'<div class="popis-note">ℹ️ {html.escape(texto)}</div>', unsafe_allow_html=True)
