"""Resumo de produção agregado por dia (a "bake list" da cozinha)."""
from __future__ import annotations

import html
from datetime import date, timedelta

import streamlit as st

import db
import ui
from utils import (
    agregar_produtos,
    formatar_data_extenso,
    formatar_hora,
    formatar_numero,
    formatar_quantidade,
    proximo_24_dezembro,
)


def _definir_dia(dia: date) -> None:
    st.session_state["producao_dia"] = dia


def render() -> None:
    st.subheader("🥖 Resumo de produção")
    st.caption(
        "Lista agregada dos produtos a preparar no dia escolhido, "
        "pensada para ficar aberta no ecrã da cozinha."
    )

    hoje = date.today()
    if "producao_dia" not in st.session_state:
        st.session_state["producao_dia"] = proximo_24_dezembro(hoje)

    atalho_hoje, atalho_amanha, atalho_natal = st.columns(3)
    atalho_hoje.button(
        "Hoje", on_click=_definir_dia, args=(hoje,), key="producao_atalho_hoje"
    )
    atalho_amanha.button(
        "Amanhã",
        on_click=_definir_dia,
        args=(hoje + timedelta(days=1),),
        key="producao_atalho_amanha",
    )
    atalho_natal.button(
        "24 de dezembro",
        on_click=_definir_dia,
        args=(proximo_24_dezembro(hoje),),
        key="producao_atalho_natal",
    )

    dia = st.date_input(
        "Dia de produção",
        key="producao_dia",
        format="DD/MM/YYYY",
    )
    incluir_entregues = st.toggle(
        "Incluir encomendas já entregues",
        value=False,
        key="producao_incluir_entregues",
    )

    try:
        encomendas = db.listar_encomendas(dia, dia)
    except db.ErroBaseDados as exc:
        st.error(f"Não foi possível carregar as encomendas do dia. {exc}")
        return

    if incluir_entregues:
        ativas = encomendas
    else:
        ativas = [
            encomenda
            for encomenda in encomendas
            if encomenda.get("estado_encomenda") != "Entregue"
        ]

    st.markdown(f"### {formatar_data_extenso(dia)}")

    if not ativas:
        mensagem = "Não há encomendas a produzir para este dia."
        if not incluir_entregues:
            mensagem += " Ative a opção acima para incluir encomendas já entregues."
        st.info(mensagem)
        return

    agregados = agregar_produtos(
        encomenda.get("produtos") for encomenda in ativas
    )
    por_pagar = sum(
        1 for encomenda in ativas if encomenda.get("estado_pagamento") != "Pago"
    )

    metrica_1, metrica_2, metrica_3 = st.columns(3)
    metrica_1.metric("Encomendas", len(ativas))
    metrica_2.metric("Produtos distintos", len(agregados))
    metrica_3.metric("Por pagar", por_pagar)

    st.markdown("#### Lista de produção")
    linhas = "".join(
        f"<tr><td class='qtd'>{html.escape(formatar_quantidade(item['quantidade']))}×</td>"
        f"<td>{html.escape(item['produto'])}</td></tr>"
        for item in agregados
    )
    st.markdown(
        f"<table class='bake-table'><tbody>{linhas}</tbody></table>",
        unsafe_allow_html=True,
    )
    if any(item["estimada"] for item in agregados):
        st.caption("As linhas sem quantidade explícita contam como 1 unidade.")

    with st.expander(f"Detalhe por encomenda ({len(ativas)})"):
        ordenadas = sorted(
            ativas,
            key=lambda encomenda: (
                str(encomenda.get("hora_levantamento") or "99:99:99"),
                int(encomenda.get("numero_encomenda") or 0),
            ),
        )
        for encomenda in ordenadas:
            hora = formatar_hora(encomenda.get("hora_levantamento")) or "sem hora"
            produtos = (encomenda.get("produtos") or "").replace("\n", "<br>")
            st.markdown(
                "<div class='detalhe-ordem'>"
                "<div class='linha-topo'>"
                f"<strong>{formatar_numero(encomenda.get('numero_encomenda'))} · "
                f"{html.escape(encomenda.get('nome_cliente') or '—')}</strong>"
                f"<span class='hora'>🕒 {html.escape(hora)}</span>"
                "</div>"
                f"<div>{html.escape(produtos)}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
