"""Organização das encomendas por fase de separação."""
from __future__ import annotations

import html

import streamlit as st

import db
import ui
from utils import formatar_data, formatar_hora, formatar_numero

VISOES = ("todas", "a_separar", "separado")


def carregar() -> tuple[list[dict] | None, str | None]:
    """Carrega uma vez as encomendas usadas pelas três abas."""
    try:
        return db.listar_encomendas(), None
    except db.ErroBaseDados as exc:
        return None, str(exc)


def _estado(encomenda: dict) -> str:
    estado = (encomenda.get("estado_separacao") or "").strip()
    if estado in db.ESTADOS_SEPARACAO:
        return estado
    return db.ESTADO_SEPARACAO_INICIAL


def _chave_ordem(encomenda: dict) -> tuple[str, str, int]:
    """Datas/horas ascendentes: as encomendas mais próximas primeiro."""
    return (
        str(encomenda.get("data_levantamento") or ""),
        str(encomenda.get("hora_levantamento") or "99:99:99"),
        int(encomenda.get("numero_encomenda") or 0),
    )


def _chave_widget(encomenda_id: int) -> str:
    return f"separacao_{encomenda_id}"


def _mudar_estado(
    encomenda_id: int,
    numero: object,
    estado_atual: str,
    chave: str,
) -> None:
    novo = st.session_state.get(chave)
    if novo not in db.ESTADOS_SEPARACAO or novo == estado_atual:
        return

    try:
        db.atualizar_estado_separacao(encomenda_id, novo)
    except db.ErroBaseDados as exc:
        st.session_state[chave] = estado_atual
        ui.flash(
            "erro",
            f"Não foi possível atualizar a separação de "
            f"{formatar_numero(numero)}. {exc}",
        )
        return

    ui.flash(
        "sucesso",
        f"Encomenda {formatar_numero(numero)} atualizada para «{novo}».",
    )


def _cartao(encomenda: dict, visao: str) -> None:
    ident = int(encomenda.get("id"))
    com_controlo = visao == "todas"
    numero_bruto = encomenda.get("numero_encomenda")
    numero = formatar_numero(numero_bruto)
    estado = _estado(encomenda)

    with st.container(border=True):
        topo_esquerda, topo_direita = st.columns([3, 1.2])
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
            telefone = (encomenda.get("telefone") or "").strip()
            funcionario = (encomenda.get("funcionario") or "").strip()
            detalhes.append(f"📞 {telefone or '—'}")
            detalhes.append(f"👤 {funcionario or '—'}")
            st.caption(" · ".join(detalhes))
        with topo_direita:
            st.markdown(
                ui.badge_pagamento(encomenda.get("estado_pagamento")),
                unsafe_allow_html=True,
            )
            if not com_controlo:
                st.markdown(
                    ui.badge_separacao(estado),
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

        if com_controlo:
            chave = _chave_widget(ident)
            valor_atual = st.session_state.get(chave)
            if valor_atual not in db.ESTADOS_SEPARACAO or valor_atual != estado:
                st.session_state[chave] = estado
            st.segmented_control(
                "Separação",
                db.ESTADOS_SEPARACAO,
                key=chave,
                on_change=_mudar_estado,
                args=(ident, numero_bruto, estado, chave),
                label_visibility="collapsed",
                width="stretch",
            )
        elif visao == "a_separar":
            if st.button(
                "✅ Passar a separado",
                key=f"passar_separado_{ident}",
                type="primary",
            ):
                try:
                    db.atualizar_estado_separacao(ident, "Separado")
                except db.ErroBaseDados as exc:
                    st.error(f"Não foi possível atualizar a encomenda. {exc}")
                else:
                    ui.flash(
                        "sucesso",
                        f"Encomenda {numero} passou para «Separado».",
                    )
                    st.rerun()


def _filtrar(visao: str, encomendas: list[dict]) -> list[dict]:
    # "Encomendas" é a fila de trabalho ainda por iniciar; assim que uma
    # encomenda passa para "A separar" deixa de aparecer nesta aba.
    if visao == "todas":
        return [e for e in encomendas if _estado(e) == "Não separado"]
    if visao == "a_separar":
        return [e for e in encomendas if _estado(e) == "A separar"]
    if visao == "separado":
        return [e for e in encomendas if _estado(e) == "Separado"]
    return []


def render(
    visao: str,
    encomendas: list[dict] | None,
    erro: str | None = None,
) -> None:
    """Mostra a lista de uma das três vistas de organização."""
    if visao not in VISOES:
        raise ValueError(f"Vista de separação desconhecida: {visao}")

    if erro:
        st.error(f"Não foi possível carregar as encomendas. {erro}")
        return

    filtradas = sorted(_filtrar(visao, encomendas or []), key=_chave_ordem)

    if not filtradas:
        if visao == "a_separar":
            st.info("Não há encomendas em separação.")
        elif visao == "separado":
            st.info("Ainda não há encomendas separadas.")
        else:
            st.info("Não há encomendas por separar.")
        return

    rotulo = {
        "todas": "por separar",
        "a_separar": "a separar",
        "separado": "separada(s)",
    }[visao]
    st.caption(
        f"**{len(filtradas)}** encomenda(s) {rotulo} · "
        "ordenadas da data mais próxima para a mais distante"
    )

    for encomenda in filtradas:
        _cartao(encomenda, visao)
