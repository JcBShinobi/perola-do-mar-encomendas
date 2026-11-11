"""Painel de consulta, pesquisa e gestão das encomendas."""
from __future__ import annotations

import html
import re
from datetime import date, time, timedelta

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
    termo_digitos = re.sub(r"\D", "", termo)
    resultado: list[dict] = []

    for encomenda in encomendas:
        if termo:
            nome = (encomenda.get("nome_cliente") or "").lower()
            numero = str(encomenda.get("numero_encomenda") or "")
            telefone = (encomenda.get("telefone") or "").lower()
            telefone_digitos = re.sub(r"\D", "", telefone)
            if (
                termo not in nome
                and termo not in numero
                and termo not in telefone
                and not (termo_digitos and termo_digitos in telefone_digitos)
            ):
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

        col_pago, col_editar, col_apagar = st.columns([2.2, 1, 1])
        with col_pago:
            st.toggle(
                "Pagamento recebido",
                value=pago,
                key=f"pago_{ident}_{int(pago)}",
                on_change=_mudar_pagamento,
                args=(
                    ident,
                    encomenda.get("numero_encomenda"),
                    pago,
                    f"pago_{ident}_{int(pago)}",
                ),
            )
        with col_editar:
            if st.button("Editar", key=f"editar_{ident}", type="tertiary"):
                st.session_state["encomenda_edicao"] = encomenda
                st.rerun()
        with col_apagar:
            if st.button("Apagar", key=f"apagar_{ident}", type="tertiary"):
                st.session_state["encomenda_apagar"] = encomenda
                st.rerun()


def _data_do_registo(encomenda: dict) -> date:
    try:
        return date.fromisoformat(str(encomenda.get("data_levantamento"))[:10])
    except (TypeError, ValueError):
        return date.today()


def _hora_do_registo(encomenda: dict) -> time | None:
    valor = encomenda.get("hora_levantamento")
    if not valor:
        return None
    try:
        return time.fromisoformat(str(valor)[:8])
    except ValueError:
        return None


def _fechar_edicao() -> None:
    st.session_state.pop("encomenda_edicao", None)


def _fechar_apagar() -> None:
    st.session_state.pop("encomenda_apagar", None)


@st.dialog("Editar encomenda", width="large", on_dismiss=_fechar_edicao)
def _dialogo_editar(encomenda: dict) -> None:
    ident = int(encomenda["id"])
    numero = formatar_numero(encomenda.get("numero_encomenda"))
    pagamento_atual = encomenda.get("estado_pagamento") or "Por Pagar"
    indice_pagamento = (
        db.ESTADOS_PAGAMENTO.index(pagamento_atual)
        if pagamento_atual in db.ESTADOS_PAGAMENTO
        else 0
    )

    st.caption(f"Encomenda {numero} · {encomenda.get('nome_cliente') or '—'}")

    with st.form(f"editar_{ident}"):
        nome = st.text_input(
            "Nome do cliente *", value=encomenda.get("nome_cliente") or ""
        )
        telefone = st.text_input("Telefone", value=encomenda.get("telefone") or "")
        produtos = st.text_area(
            "Produtos e quantidades *",
            value=encomenda.get("produtos") or "",
            height=120,
        )
        dia = st.date_input(
            "Data de levantamento *",
            value=_data_do_registo(encomenda),
            format="DD/MM/YYYY",
        )
        hora = st.time_input(
            "Hora (opcional)",
            value=_hora_do_registo(encomenda),
            step=timedelta(minutes=15),
        )
        pagamento = st.radio(
            "Estado do pagamento",
            db.ESTADOS_PAGAMENTO,
            index=indice_pagamento,
            horizontal=True,
        )
        observacoes = st.text_area(
            "Observações", value=encomenda.get("observacoes") or "", height=80
        )
        guardar = st.form_submit_button("Guardar alterações", type="primary")

    if guardar:
        erros: list[str] = []
        if not nome.strip():
            erros.append("Indique o nome do cliente.")
        if not produtos.strip():
            erros.append("Indique os produtos e as quantidades.")
        if not isinstance(dia, date):
            erros.append("Escolha a data de levantamento.")
        if erros:
            for erro in erros:
                st.error(erro)
            return

        try:
            db.atualizar_encomenda(
                ident,
                {
                    "nome_cliente": nome,
                    "telefone": telefone,
                    "produtos": produtos,
                    "data_levantamento": dia,
                    "hora_levantamento": hora,
                    "estado_pagamento": pagamento,
                    "observacoes": observacoes,
                },
            )
        except db.ErroBaseDados as exc:
            st.error(f"Não foi possível atualizar a encomenda. {exc}")
            return

        st.session_state.pop("encomenda_edicao", None)
        ui.flash("sucesso", f"Encomenda {numero} atualizada.")
        st.rerun()

    if st.button("Cancelar"):
        st.session_state.pop("encomenda_edicao", None)
        st.rerun()


@st.dialog("Apagar encomenda", on_dismiss=_fechar_apagar)
def _dialogo_apagar(encomenda: dict) -> None:
    ident = int(encomenda["id"])
    numero = formatar_numero(encomenda.get("numero_encomenda"))
    nome = encomenda.get("nome_cliente") or "—"

    st.warning(
        f"Tens a certeza de que queres apagar a encomenda {numero} de {nome}? "
        "Esta ação é permanente e não pode ser desfeita."
    )
    st.caption("O cliente, os produtos e as observações serão removidos.")

    col_cancelar, col_apagar = st.columns(2)
    with col_cancelar:
        if st.button("Cancelar"):
            st.session_state.pop("encomenda_apagar", None)
            st.rerun()
    with col_apagar:
        if st.button("Apagar definitivamente", type="primary"):
            try:
                db.apagar_encomenda(ident)
            except db.ErroBaseDados as exc:
                st.error(f"Não foi possível apagar a encomenda. {exc}")
                return
            st.session_state.pop("encomenda_apagar", None)
            ui.flash("sucesso", f"Encomenda {numero} apagada.")
            st.rerun()


def render() -> None:
    if st.session_state.get("encomenda_edicao"):
        _dialogo_editar(st.session_state["encomenda_edicao"])
    if st.session_state.get("encomenda_apagar"):
        _dialogo_apagar(st.session_state["encomenda_apagar"])

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
            "Pesquisar por nº, nome ou telefone",
            key="gestao_pesquisa",
            placeholder="Ex.: 42, Maria ou 912 345 678",
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
