"""Componentes visuais partilhados: CSS, cabeçalho, badges e mensagens."""
from __future__ import annotations

import streamlit as st

_CSS = """
<style>
    :root {
        --vinho: #8c1d2f;
        --dourado: #c9a227;
        --verde: #1f5c43;
        --creme: #fff8ef;
        --texto: #2b1b14;
    }

    div[data-testid="stMainBlockContainer"] {
        padding-top: 1.6rem;
        padding-bottom: 4rem;
        max-width: 1020px;
    }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { display: none !important; }

    /* Cabeçalho da aplicação */
    .app-header {
        position: relative;
        overflow: hidden;
        background: radial-gradient(circle at 12% 15%, #a8243a 0%, #7a1327 55%, #550b19 100%);
        color: var(--creme);
        border-radius: 18px;
        padding: 1.35rem 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, .14);
        box-shadow: 0 10px 26px rgba(85, 11, 25, .25);
    }
    .app-header .marca {
        font-size: .74rem;
        letter-spacing: .18em;
        text-transform: uppercase;
        opacity: .85;
    }
    .app-header h1 {
        font-size: 2rem;
        line-height: 1.15;
        margin: .25rem 0 .2rem;
        color: var(--creme);
        padding: 0;
    }
    .app-header .pinheiro {
        position: absolute;
        right: 1.1rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 3.4rem;
        opacity: .9;
    }

    /* Cartões das encomendas */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
        border-color: rgba(140, 29, 47, .16);
        background: #fffdfa;
        box-shadow: 0 2px 10px rgba(43, 27, 20, .05);
    }
    .ordem-titulo {
        font-size: 1.12rem;
        font-weight: 700;
        color: var(--texto);
        line-height: 1.3;
    }
    .ordem-produtos {
        font-size: .97rem;
        line-height: 1.5;
        background: #fdf4ea;
        border-left: 3px solid var(--dourado);
        border-radius: 0 10px 10px 0;
        padding: .55rem .75rem;
        margin: .3rem 0 .2rem;
        white-space: normal;
    }
    .ordem-obs {
        font-size: .86rem;
        color: #6b4a3b;
        margin-bottom: .3rem;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: .16rem .6rem;
        border-radius: 999px;
        font-size: .76rem;
        font-weight: 600;
        line-height: 1.55;
        white-space: nowrap;
        margin: 0 .2rem .25rem 0;
    }
    .b-pago     { background: #d7f2e0; color: #155c36; }
    .b-porpagar { background: #fde2e4; color: #8c1d2f; }

    /* Número da encomenda em grande destaque */
    .numero-destaque {
        background: linear-gradient(135deg, #1f5c43 0%, #14412f 100%);
        color: var(--creme);
        border-radius: 20px;
        padding: 1.35rem 1rem;
        text-align: center;
        border: 2px solid var(--dourado);
        box-shadow: 0 12px 26px rgba(20, 65, 47, .26);
        margin-bottom: .6rem;
    }
    .nd-label {
        font-size: .74rem;
        letter-spacing: .2em;
        text-transform: uppercase;
        color: #f3d98b;
    }
    .nd-valor {
        font-size: 4.2rem;
        font-weight: 800;
        letter-spacing: .04em;
        line-height: 1.05;
        margin: .15rem 0;
        font-variant-numeric: tabular-nums;
    }
    .nd-info { font-size: 1.02rem; opacity: .95; }
    .nd-hint { margin-top: .55rem; font-size: .88rem; color: #f3d98b; }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: #fffaf4;
        border: 1px solid #efdfd0;
        border-radius: 14px;
        padding: .7rem .9rem;
    }
    div[data-testid="stMetricValue"] { color: var(--vinho); }

    .stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 600; }
    .stFormSubmitButton > button { width: 100%; padding: .55rem 1rem; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: .2rem; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { padding: .45rem .8rem; }

    /* Ações discretas nos cartões, sem moldura */
    [class*="st-key-editar_"] button,
    [class*="st-key-apagar_"] button {
        border: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        color: #6b4a3b !important;
        font-size: .8rem !important;
        font-weight: 500 !important;
        min-height: 1.5rem !important;
        padding: .05rem .3rem !important;
        width: auto !important;
    }
    [class*="st-key-editar_"] button:hover,
    [class*="st-key-apagar_"] button:hover {
        background: #f7ece2 !important;
        color: var(--vinho) !important;
    }
    [class*="st-key-apagar_"] button:hover { color: #a8243a !important; }

    /* Ligação ao Supabase: ícone pequeno e discreto */
    [class*="st-key-testar_ligacao"] button {
        border: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        color: #8a6a5a !important;
        min-height: 1.6rem !important;
        padding: .1rem .35rem !important;
        opacity: .6;
    }
    [class*="st-key-testar_ligacao"] button:hover {
        opacity: 1;
        background: #f7ece2 !important;
    }

    @media (max-width: 700px) {
        div[data-testid="stMainBlockContainer"] {
            padding-top: 1rem;
            padding-left: .8rem;
            padding-right: .8rem;
        }
        .app-header { padding: 1rem 1.1rem; border-radius: 14px; }
        .app-header h1 { font-size: 1.5rem; }
        .app-header .pinheiro { font-size: 2.4rem; right: .7rem; opacity: .55; }
        .nd-valor { font-size: 3.1rem; }
        .stButton > button { width: 100%; }

        /* Empilha as colunas para leitura confortável no telemóvel */
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .35rem; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
        }
    }
</style>
"""


def inject_css() -> None:
    """Aplica o tema visual (Natal suave, legível em telemóvel e balcão)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def cabecalho() -> None:
    """Cabeçalho com a marca da padaria."""
    st.markdown(
        """
        <div class="app-header">
            <div class="marca">Pérola do Mar · Padaria &amp; Cafetaria</div>
            <h1>Encomendas de Natal 🎄</h1>
            <div class="pinheiro">🎄</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_pagamento(estado: str | None) -> str:
    if (estado or "Por Pagar") == "Pago":
        return "<span class='badge b-pago'>💶 Pago</span>"
    return "<span class='badge b-porpagar'>💶 Por pagar</span>"


def flash(tipo: str, mensagem: str) -> None:
    """Guarda uma mensagem para mostrar no início do próximo rerun."""
    st.session_state.setdefault("mensagens", []).append((tipo, mensagem))


def mostrar_flash() -> None:
    """Mostra (e limpa) as mensagens pendentes."""
    mensagens = st.session_state.pop("mensagens", [])
    for tipo, mensagem in mensagens:
        if tipo == "sucesso":
            st.success(mensagem)
        else:
            st.error(mensagem)
