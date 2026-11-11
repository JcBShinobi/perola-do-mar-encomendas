"""Componentes visuais partilhados: CSS, cabeçalho, badges e mensagens."""
from __future__ import annotations

import streamlit as st

CHAVE_ASSINATURA = "_assinatura_encomendas"

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
    .b-nao-separado { background: #f1e7dc; color: #6b4a3b; }
    .b-a-separar   { background: #fff1c9; color: #7a5a00; }
    .b-separado    { background: #d7f2e0; color: #155c36; }

    /* Contador de cada fila de separação */
    .fila-contador {
        display: flex;
        align-items: center;
        gap: .65rem;
        margin: .2rem 0 .9rem;
        padding: .55rem .8rem;
        background: #fff8ef;
        border: 1px solid #efdfd0;
        border-radius: 12px;
    }
    .fila-contador .fila-numero {
        font-size: 1.55rem;
        font-weight: 800;
        line-height: 1;
        color: var(--vinho);
        font-variant-numeric: tabular-nums;
    }
    .fila-contador .fila-texto {
        font-size: .82rem;
        line-height: 1.35;
        color: #6b4a3b;
    }

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

    /* Botões */
    .stButton > button,
    .stDownloadButton > button {
        min-height: 2.45rem;
        padding: .48rem 1rem;
        border: 1px solid rgba(140, 29, 47, .20);
        border-radius: 12px;
        background: linear-gradient(180deg, #fffdfa 0%, #fbf0e2 100%);
        color: #6b2a33;
        font-size: .92rem;
        font-weight: 650;
        letter-spacing: .005em;
        line-height: 1.2;
        box-shadow: 0 2px 6px rgba(43, 27, 20, .05);
        -webkit-tap-highlight-color: transparent;
        transition: transform .16s ease, box-shadow .16s ease,
                    background .16s ease, border-color .16s ease, color .16s ease;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(201, 162, 39, .70);
        background: #fff8ef;
        color: var(--vinho);
        box-shadow: 0 6px 14px rgba(85, 11, 25, .10);
        transform: translateY(-1px);
    }
    .stButton > button:active,
    .stDownloadButton > button:active { transform: translateY(0); }
    .stButton > button p,
    .stDownloadButton > button p { margin: 0; color: inherit; }

    /* Ação principal: vinho profundo com filete dourado */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        border-color: rgba(232, 197, 106, .60);
        background: linear-gradient(135deg, #a8243a 0%, #8c1d2f 55%, #6f1020 100%);
        color: var(--creme) !important;
        box-shadow: 0 5px 14px rgba(85, 11, 25, .20),
                    inset 0 1px 0 rgba(255, 255, 255, .16);
    }
    .stButton > button[kind="primary"] p,
    .stDownloadButton > button[kind="primary"] p { color: inherit !important; }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        border-color: rgba(245, 214, 132, .90);
        background: linear-gradient(135deg, #b32a43 0%, #972037 55%, #7a1327 100%);
        color: #fffdf7 !important;
        box-shadow: 0 8px 20px rgba(85, 11, 25, .27),
                    inset 0 1px 0 rgba(255, 255, 255, .18);
    }

    /* Ações terciárias/discretas */
    .stButton > button[kind="tertiary"] {
        min-height: 2rem;
        padding: .3rem .6rem;
        border-color: transparent;
        background: transparent;
        color: #7a5a49;
        box-shadow: none;
    }
    .stButton > button[kind="tertiary"]:hover {
        border-color: rgba(201, 162, 39, .35);
        background: #fff8ef;
        color: var(--vinho);
        box-shadow: 0 3px 8px rgba(43, 27, 20, .06);
        transform: none;
    }

    /* Botão de link (SMS) */
    .stLinkButton > a,
    .stLinkButton a,
    div[data-testid="stLinkButton"] a,
    a[data-testid^="stBaseLinkButton"] {
        display: flex !important;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-height: 2.45rem;
        padding: .48rem 1rem;
        border: 1px solid rgba(31, 92, 67, .42);
        border-radius: 12px;
        background: linear-gradient(135deg, #2b7255 0%, #1f5c43 60%, #174a35 100%);
        color: var(--creme) !important;
        font-size: .92rem;
        font-weight: 700;
        line-height: 1.2;
        text-decoration: none !important;
        box-shadow: 0 5px 14px rgba(20, 65, 47, .18),
                    inset 0 1px 0 rgba(255, 255, 255, .14);
        -webkit-tap-highlight-color: transparent;
        transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
    }
    .stLinkButton a p { margin: 0; color: inherit !important; }
    .stLinkButton a:hover,
    div[data-testid="stLinkButton"] a:hover,
    a[data-testid^="stBaseLinkButton"]:hover {
        background: linear-gradient(135deg, #358664 0%, #276b4f 60%, #1c563e 100%);
        box-shadow: 0 8px 18px rgba(20, 65, 47, .25),
                    inset 0 1px 0 rgba(255, 255, 255, .18);
        transform: translateY(-1px);
    }

    /* Submissão de formulários */
    .stFormSubmitButton > button,
    button[kind="primaryFormSubmit"] {
        width: 100%;
        min-height: 2.8rem;
        padding: .65rem 1.2rem;
        border: 1px solid rgba(232, 197, 106, .60);
        border-radius: 12px;
        background: linear-gradient(135deg, #a8243a 0%, #8c1d2f 55%, #6f1020 100%);
        color: var(--creme) !important;
        font-size: .96rem;
        font-weight: 700;
        letter-spacing: .01em;
        line-height: 1.2;
        box-shadow: 0 5px 14px rgba(85, 11, 25, .20),
                    inset 0 1px 0 rgba(255, 255, 255, .16);
        transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
    }
    .stFormSubmitButton > button p,
    button[kind="primaryFormSubmit"] p { margin: 0; color: inherit !important; }
    .stFormSubmitButton > button:hover,
    button[kind="primaryFormSubmit"]:hover {
        border-color: rgba(245, 214, 132, .90);
        background: linear-gradient(135deg, #b32a43 0%, #972037 55%, #7a1327 100%);
        box-shadow: 0 8px 20px rgba(85, 11, 25, .27),
                    inset 0 1px 0 rgba(255, 255, 255, .18);
        transform: translateY(-1px);
    }
    .stFormSubmitButton > button:active,
    button[kind="primaryFormSubmit"]:active { transform: translateY(0); }

    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled,
    .stLinkButton a[aria-disabled="true"] {
        opacity: .52;
        box-shadow: none;
        transform: none;
        cursor: not-allowed;
    }
    .stButton > button:focus-visible,
    .stDownloadButton > button:focus-visible,
    .stFormSubmitButton > button:focus-visible,
    .stLinkButton a:focus-visible {
        outline: 3px solid rgba(201, 162, 39, .55);
        outline-offset: 2px;
    }

    .stTabs [data-baseweb="tab-list"] { gap: .2rem; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { padding: .45rem .8rem; }

    /* Ações compactas dos cartões: pequenas “chips” com contorno suave */
    [class*="st-key-editar_"] button,
    [class*="st-key-apagar_"] button {
        width: auto !important;
        min-height: 1.9rem !important;
        padding: .12rem .62rem !important;
        border: 1px solid rgba(140, 29, 47, .14) !important;
        border-radius: 999px !important;
        background: #fffdfa !important;
        color: #6b4a3b !important;
        font-size: .74rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        white-space: nowrap;
        box-shadow: 0 1px 4px rgba(43, 27, 20, .04) !important;
        transition: transform .16s ease, background .16s ease,
                    border-color .16s ease, color .16s ease !important;
    }
    [class*="st-key-editar_"] button p,
    [class*="st-key-apagar_"] button p { margin: 0; }
    [class*="st-key-editar_"] button:hover,
    [class*="st-key-apagar_"] button:hover {
        border-color: rgba(201, 162, 39, .65) !important;
        background: #fff8ef !important;
        color: var(--vinho) !important;
        transform: translateY(-1px);
    }
    [class*="st-key-apagar_"] button:hover {
        border-color: rgba(168, 36, 58, .35) !important;
        background: #fdf1f1 !important;
        color: #a8243a !important;
    }

    @media (prefers-reduced-motion: reduce) {
        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton a,
        .stFormSubmitButton > button,
        [class*="st-key-editar_"] button,
        [class*="st-key-apagar_"] button {
            transition: none !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton a:hover,
        .stFormSubmitButton > button:hover,
        [class*="st-key-editar_"] button:hover,
        [class*="st-key-apagar_"] button:hover { transform: none; }
    }

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

        /* Alvos de toque confortáveis no telemóvel */
        .stButton,
        .stDownloadButton,
        .stLinkButton,
        .stFormSubmitButton { width: 100%; }
        [class*="st-key-testar_ligacao"] { width: auto !important; }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-height: 3rem;
            padding: .7rem 1rem;
            font-size: .95rem;
            touch-action: manipulation;
        }
        .stLinkButton > a,
        .stLinkButton a,
        div[data-testid="stLinkButton"] a,
        a[data-testid^="stBaseLinkButton"] {
            min-height: 3rem;
            padding: .7rem 1rem;
            font-size: .95rem;
            touch-action: manipulation;
        }
        .stFormSubmitButton > button,
        button[kind="primaryFormSubmit"] {
            min-height: 3.1rem;
            padding: .75rem 1.2rem;
            font-size: 1rem;
            touch-action: manipulation;
        }

        /* Editar/Apagar continuam discretos, mas com alvo de toque maior */
        [class*="st-key-editar_"] button,
        [class*="st-key-apagar_"] button {
            width: 100% !important;
            min-height: 2.8rem !important;
            padding: .5rem .9rem !important;
            font-size: .8rem !important;
        }
        [class*="st-key-testar_ligacao"] button {
            width: auto !important;
            min-height: 2.6rem !important;
        }

        .stButton > button:hover,
        .stLinkButton a:hover,
        .stFormSubmitButton > button:hover,
        [class*="st-key-editar_"] button:hover,
        [class*="st-key-apagar_"] button:hover { transform: none; }

        .stButton > button:active,
        .stLinkButton a:active,
        .stFormSubmitButton > button:active,
        [class*="st-key-editar_"] button:active,
        [class*="st-key-apagar_"] button:active { transform: scale(.985); }

        .stTabs [data-baseweb="tab"] {
            min-height: 2.8rem;
            padding: .55rem .7rem;
        }

        /* Empilha as colunas para leitura confortável no telemóvel */
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .55rem; }
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


def badge_separacao(estado: str | None) -> str:
    """Selo compacto com a fase de separação da encomenda."""
    rotulo = estado or "Não separado"
    classes = {
        "Não separado": "b-nao-separado",
        "A separar": "b-a-separar",
        "Separado": "b-separado",
    }
    classe = classes.get(rotulo, "b-nao-separado")
    return f"<span class='badge {classe}'>🧺 {rotulo}</span>"


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


def marcar_dados_alterados() -> None:
    """Invalida a assinatura local após uma escrita feita nesta sessão.

    O próximo rerun volta a ler a assinatura, mas não dispara um segundo
    rerun automático pelo simples facto de os dados terem mudado.
    """
    st.session_state.pop(CHAVE_ASSINATURA, None)
