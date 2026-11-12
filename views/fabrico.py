"""Vista de fabrico: encomendas agrupadas por área de produção."""
from __future__ import annotations

import html

import streamlit as st

import db
import ui
from utils import formatar_data, formatar_hora, formatar_numero


def carregar() -> tuple[list[dict] | None, str | None]:
    """Carrega uma vez as encomendas usadas pelas três abas de fabrico."""
    try:
        return db.listar_encomendas(), None
    except db.ErroBaseDados as exc:
        return None, str(exc)


def _categoria(chave: str) -> tuple[str, str, str]:
    for categoria, rotulo, campo_produtos, campo_pronto in db.CATEGORIAS_PRODUTOS:
        if categoria == chave:
            return rotulo, campo_produtos, campo_pronto
    raise ValueError(f"Categoria de fabrico desconhecida: {chave}")


def _chave_ordem(encomenda: dict) -> tuple[str, str, int]:
    """Datas/horas ascendentes: as encomendas mais próximas primeiro."""
    return (
        str(encomenda.get("data_levantamento") or ""),
        str(encomenda.get("hora_levantamento") or "99:99:99"),
        int(encomenda.get("numero_encomenda") or 0),
    )


def _alternar_pronto(
    encomenda_id: int,
    categoria: str,
    pronto: bool,
    chave_widget: str,
) -> None:
    """Atualiza a categoria no callback, antes do rerun normal do Streamlit."""
    try:
        db.atualizar_pronto_categoria(encomenda_id, categoria, pronto)
    except db.ErroBaseDados as exc:
        # A gravação falhou: repõe a checkbox no estado que está na base.
        st.session_state[chave_widget] = not pronto
        ui.flash("erro", f"Não foi possível atualizar a encomenda. {exc}")
        return

    ui.marcar_dados_alterados()
    rotulo, _, _ = _categoria(categoria)
    if pronto:
        ui.flash("sucesso", f"{rotulo} marcada como pronta.")
    else:
        ui.flash("sucesso", f"{rotulo} novamente por concluir.")


def _cartao(
    encomenda: dict,
    categoria: str,
    rotulo: str,
    campo_produtos: str,
    campo_pronto: str,
) -> None:
    ident = int(encomenda.get("id"))
    numero = formatar_numero(encomenda.get("numero_encomenda"))
    pronto = bool(encomenda.get(campo_pronto))
    produtos = (encomenda.get(campo_produtos) or "").strip()

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
            telefone = (encomenda.get("telefone") or "").strip()
            funcionario = (encomenda.get("funcionario") or "").strip()
            if telefone:
                detalhes.append(f"📞 {telefone}")
            if funcionario:
                detalhes.append(f"👤 {funcionario}")
            st.caption(" · ".join(detalhes))
        with topo_direita:
            selos = ""
            if pronto:
                selos += ui.badge_pronto(rotulo)
            st.markdown(selos, unsafe_allow_html=True)

        st.markdown(
            "<div class='produto-categoria'>"
            f"<div class='produto-categoria-label'>{html.escape(rotulo)}</div>"
            "<div class='ordem-produtos'>"
            + html.escape(produtos).replace("\n", "<br>")
            + "</div></div>",
            unsafe_allow_html=True,
        )

        observacoes = (encomenda.get("observacoes") or "").strip()
        if observacoes:
            st.markdown(
                f"<div class='ordem-obs'>📝 {html.escape(observacoes)}</div>",
                unsafe_allow_html=True,
            )

        chave_widget = f"pronto_{categoria}_{ident}_{int(pronto)}"
        st.checkbox(
            "Concluído / Pronto",
            value=pronto,
            key=chave_widget,
            on_change=_alternar_pronto,
            args=(ident, categoria, not pronto, chave_widget),
        )


def render(
    categoria: str,
    encomendas: list[dict] | None,
    erro: str | None = None,
) -> None:
    """Mostra as encomendas que têm produtos de uma categoria."""
    rotulo, campo_produtos, campo_pronto = _categoria(categoria)

    if erro:
        st.error(f"Não foi possível carregar as encomendas. {erro}")
        return

    filtradas = sorted(
        [
            encomenda
            for encomenda in (encomendas or [])
            if (encomenda.get(campo_produtos) or "").strip()
        ],
        key=_chave_ordem,
    )

    quantidade = len(filtradas)
    substantivo = "encomenda" if quantidade == 1 else "encomendas"
    st.markdown(
        f"<div class='fila-contador'>"
        f"<span class='fila-numero'>{quantidade}</span>"
        f"<span class='fila-texto'>{substantivo} com {html.escape(rotulo.lower())}"
        "<br>ordenadas da data mais próxima para a mais distante"
        "</span></div>",
        unsafe_allow_html=True,
    )

    if not filtradas:
        st.info(f"Não há encomendas com produtos de {rotulo.lower()}.")
        return

    pagina_itens, pagina, total_paginas = ui.paginar(
        filtradas, f"fab_pagina_{categoria}"
    )
    for encomenda in pagina_itens:
        _cartao(
            encomenda,
            categoria,
            rotulo,
            campo_produtos,
            campo_pronto,
        )

    ui.navegacao_paginas(f"fab_pagina_{categoria}", pagina, total_paginas)
