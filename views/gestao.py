"""Painel de consulta, pesquisa e gestão das encomendas."""
from __future__ import annotations

import html
from datetime import date, timedelta

import streamlit as st

import db
import ui
from utils import (
    formatar_data,
    formatar_hora,
    formatar_numero,
    proximo_24_dezembro,
)

TAMANHO_PAGINA = 20


def _filtrar(
    encomendas: list[dict],
    pesquisa: str,
) -> list[dict]:
    termo = pesquisa.strip().lower().lstrip("#")
    resultado: list[dict] = []

    for encomenda in encomendas:
        if termo:
            nome = (encomenda.get("nome_cliente") or "").lower()
            numero = str(encomenda.get("numero_encomenda") or "")
            if termo not in nome and termo not in numero:
                continue
        resultado.append(encomenda)

    return resultado


def _chave_ordem(encomenda: dict) -> tuple[str, str, int]:
    return (
        str(encomenda.get("data_levantamento") or ""),
        str(encomenda.get("hora_levantamento") or "99:99:99"),
        int(encomenda.get("numero_encomenda") or 0),
    )


def _mudar_pagamento(
    encomenda_id: int,
    numero: object,
    pago_atual: bool,
    chave: str,
) -> None:
    novo = bool(st.session_state.get(chave))
    if novo == pago_atual:
        return
    try:
        db.atualizar_estado_pagamento(encomenda_id, novo)
        ui.flash(
            "sucesso",
            f"Encomenda {formatar_numero(numero)} marcada como "
            f"{'paga' if novo else 'por pagar'}.",
        )
    except db.ErroBaseDados as exc:
        st.session_state[chave] = pago_atual
        ui.flash(
            "erro",
            f"Não foi possível atualizar o pagamento de {formatar_numero(numero)}. {exc}",
        )


def _cartao(encomenda: dict) -> None:
    ident = int(encomenda.get("id"))
    numero = formatar_numero(encomenda.get("numero_encomenda"))
    pago = (encomenda.get("estado_pagamento") or "Por Pagar") == "Pago"

    with st.container(border=True):
        topo_esquerda, topo_direita = st.columns([3, 1.3])
        with topo_esquerda:
            st.markdown(
                f"<div class='ordem-titulo'>{html.escape(numero)} · "
                f"{html.escape(encomenda.get('nome_cliente') or '—')}</div>",
                unsafe_allow_html=True,
            )
            detalhes = [f"📅 {formatar_data(encomenda.get('data_levantamento'))}"]
            hora = formatar_hora(encomenda.get("hora_levantamento"))
            if hora:
                detalhes.append(f"🕒 {hora}")
            if encomenda.get("telefone"):
                detalhes.append(f"📞 {encomenda['telefone']}")
            if encomenda.get("funcionario"):
                detalhes.append(f"👤 {encomenda['funcionario']}")
            st.caption(" · ".join(detalhes))
        with topo_direita:
            st.markdown(
                ui.badge_pagamento(encomenda.get("estado_pagamento")),
                unsafe_allow_html=True,
            )

        produtos = (encomenda.get("produtos") or "").strip()
        if produtos:
            st.markdown(
                "<div class='ordem-produtos'>"
                + html.escape(produtos).replace("\n", "<br>")
                + "</div>",
                unsafe_allow_html=True,
            )

        observacoes = (encomenda.get("observacoes") or "").strip()
        if observacoes:
            st.markdown(
                f"<div class='ordem-obs'>📝 {html.escape(observacoes)}</div>",
                unsafe_allow_html=True,
            )

        st.toggle(
            "Pagamento recebido",
            value=pago,
            key=f"pago_{ident}_{int(pago)}",
            on_change=_mudar_pagamento,
            args=(ident, encomenda.get("numero_encomenda"), pago, f"pago_{ident}_{int(pago)}"),
        )


def render() -> None:
    hoje = date.today()
    filtro_data, filtro_pesquisa = st.columns([1, 1.4])

    dia: date | None = None
    with filtro_data:
        modo = st.selectbox(
            "Data de levantamento",
            ("Hoje", "Amanhã", "Escolher dia", "Todas"),
            key="gestao_modo_data",
        )
        if modo == "Escolher dia":
            dia = st.date_input(
                "Dia",
                value=proximo_24_dezembro(hoje),
                format="DD/MM/YYYY",
                key="gestao_dia",
            )

    with filtro_pesquisa:
        pesquisa = st.text_input(
            "Pesquisar por nº ou nome",
            key="gestao_pesquisa",
            placeholder="Ex.: 42 ou Maria",
        )

    inicio: date | None
    fim: date | None
    if modo == "Hoje":
        inicio = fim = hoje
    elif modo == "Amanhã":
        inicio = fim = hoje + timedelta(days=1)
    elif modo == "Escolher dia" and dia is not None:
        inicio = fim = dia
    else:
        inicio = fim = None

    try:
        encomendas = db.listar_encomendas(inicio, fim)
    except db.ErroBaseDados as exc:
        st.error(f"Não foi possível carregar as encomendas. {exc}")
        return

    filtradas = sorted(_filtrar(encomendas, pesquisa), key=_chave_ordem)

    assinatura = (modo, str(dia), pesquisa)
    if st.session_state.get("gestao_assinatura") != assinatura:
        st.session_state["gestao_assinatura"] = assinatura
        st.session_state["gestao_limite"] = TAMANHO_PAGINA

    if not filtradas:
        st.info("Não há encomendas para estes filtros.")
        return

    por_pagar = sum(
        1 for encomenda in filtradas if encomenda.get("estado_pagamento") != "Pago"
    )
    st.caption(f"**{len(filtradas)}** encomenda(s) · **{por_pagar}** por pagar")

    limite = st.session_state.get("gestao_limite", TAMANHO_PAGINA)
    for encomenda in filtradas[:limite]:
        _cartao(encomenda)

    if len(filtradas) > limite:
        restantes = len(filtradas) - limite
        if st.button(f"Mostrar mais ({restantes} restantes)", key="gestao_mostrar_mais"):
            st.session_state["gestao_limite"] = limite + TAMANHO_PAGINA
            st.rerun()
