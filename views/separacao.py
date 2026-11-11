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


def _atualizar_estado(encomenda_id: int, novo: str) -> None:
    """Atualiza no callback, antes do único rerun normal do Streamlit."""
    try:
        db.atualizar_estado_separacao(encomenda_id, novo)
    except db.ErroBaseDados as exc:
        ui.flash("erro", f"Não foi possível atualizar a encomenda. {exc}")
        return

    ui.marcar_dados_alterados()


def _cartao(encomenda: dict, visao: str) -> None:
    ident = int(encomenda.get("id"))
    com_controlo = visao == "todas"
    numero = formatar_numero(encomenda.get("numero_encomenda"))
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
            col_a_separar, col_separado = st.columns(2)
            with col_a_separar:
                st.button(
                    "→ A separar",
                    key=f"para_separar_{ident}",
                    type="primary",
                    on_click=_atualizar_estado,
                    args=(ident, "A separar"),
                )
            with col_separado:
                st.button(
                    "✅ Separado",
                    key=f"para_separado_{ident}",
                    on_click=_atualizar_estado,
                    args=(ident, "Separado"),
                )
        elif visao == "a_separar":
            col_voltar, col_avancar = st.columns(2)
            with col_voltar:
                st.button(
                    "← Não separado",
                    key=f"a_separar_para_nao_{ident}",
                    on_click=_atualizar_estado,
                    args=(ident, "Não separado"),
                )
            with col_avancar:
                st.button(
                    "✅ Passar a separado",
                    key=f"passar_separado_{ident}",
                    type="primary",
                    on_click=_atualizar_estado,
                    args=(ident, "Separado"),
                )
        elif visao == "separado":
            col_voltar_nao, col_voltar_a_separar = st.columns(2)
            with col_voltar_nao:
                st.button(
                    "← Não separado",
                    key=f"separado_para_nao_{ident}",
                    on_click=_atualizar_estado,
                    args=(ident, "Não separado"),
                )
            with col_voltar_a_separar:
                st.button(
                    "← A separar",
                    key=f"separado_para_a_separar_{ident}",
                    on_click=_atualizar_estado,
                    args=(ident, "A separar"),
                )


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

    quantidade = len(filtradas)
    if visao == "separado":
        adjetivo = "separada" if quantidade == 1 else "separadas"
    else:
        adjetivo = "por separar" if visao == "todas" else "a separar"
    substantivo = "encomenda" if quantidade == 1 else "encomendas"
    st.markdown(
        f"<div class='fila-contador'>"
        f"<span class='fila-numero'>{quantidade}</span>"
        f"<span class='fila-texto'>{substantivo} {adjetivo}"
        "<br>ordenadas da data mais próxima para a mais distante"
        "</span></div>",
        unsafe_allow_html=True,
    )

    if not filtradas:
        if visao == "a_separar":
            st.info("Não há encomendas em separação.")
        elif visao == "separado":
            st.info("Ainda não há encomendas separadas.")
        else:
            st.info("Não há encomendas por separar.")
        return

    for encomenda in filtradas:
        _cartao(encomenda, visao)
