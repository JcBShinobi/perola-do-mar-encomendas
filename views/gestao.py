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
    link_sms,
    proximo_24_dezembro,
)



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


def _selos(encomenda: dict) -> str:
    """Estado de separação e selos das categorias já prontas."""
    selos = ui.badge_separacao(encomenda.get("estado_separacao"))
    for _, rotulo, campo_produtos, campo_pronto in db.CATEGORIAS_PRODUTOS:
        if (
            (encomenda.get(campo_produtos) or "").strip()
            and bool(encomenda.get(campo_pronto))
        ):
            selos += " " + ui.badge_pronto(rotulo)
    return selos


def _mostrar_produtos(encomenda: dict) -> None:
    """Mostra os produtos por categoria, com fallback para registos antigos."""
    blocos: list[tuple[str, str]] = []
    for _, rotulo, campo_produtos, _ in db.CATEGORIAS_PRODUTOS:
        texto = (encomenda.get(campo_produtos) or "").strip()
        if texto:
            blocos.append((rotulo, texto))

    if not blocos:
        legado = (encomenda.get("produtos") or "").strip()
        if legado:
            blocos.append(("Produtos", legado))

    for rotulo, texto in blocos:
        st.markdown(
            "<div class='produto-categoria'>"
            f"<div class='produto-categoria-label'>{html.escape(rotulo)}</div>"
            "<div class='ordem-produtos'>"
            + html.escape(texto).replace("\n", "<br>")
            + "</div></div>",
            unsafe_allow_html=True,
        )


def _cartao(encomenda: dict) -> None:
    ident = int(encomenda.get("id"))
    numero = formatar_numero(encomenda.get("numero_encomenda"))

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
            st.markdown(_selos(encomenda), unsafe_allow_html=True)

        _mostrar_produtos(encomenda)

        observacoes = (encomenda.get("observacoes") or "").strip()
        if observacoes:
            st.markdown(
                f"<div class='ordem-obs'>📝 {html.escape(observacoes)}</div>",
                unsafe_allow_html=True,
            )

        link = link_sms(encomenda)
        col_mensagem, col_editar, col_apagar = st.columns([2.2, 1, 1])
        with col_mensagem:
            if link:
                st.link_button("💬 Enviar mensagem", link)
        with col_editar:
            st.button(
                "Editar",
                key=f"editar_{ident}",
                type="tertiary",
                on_click=_abrir_edicao,
                args=(encomenda,),
            )
        with col_apagar:
            st.button(
                "Apagar",
                key=f"apagar_{ident}",
                type="tertiary",
                on_click=_abrir_apagar,
                args=(encomenda,),
            )


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


def _abrir_edicao(encomenda: dict) -> None:
    st.session_state["encomenda_edicao"] = encomenda


def _abrir_apagar(encomenda: dict) -> None:
    st.session_state["encomenda_apagar"] = encomenda


def _apagar_definitivamente(ident: int, numero: str) -> None:
    try:
        db.apagar_encomenda(ident)
    except db.ErroBaseDados as exc:
        ui.flash("erro", f"Não foi possível apagar a encomenda. {exc}")
        return

    ui.marcar_dados_alterados()
    st.session_state.pop("encomenda_apagar", None)
    ui.flash("sucesso", f"Encomenda {numero} apagada.")


@st.dialog("Editar encomenda", width="large", on_dismiss=_fechar_edicao)
def _dialogo_editar(encomenda: dict) -> None:
    ident = int(encomenda["id"])
    numero = formatar_numero(encomenda.get("numero_encomenda"))

    st.caption(f"Encomenda {numero} · {encomenda.get('nome_cliente') or '—'}")

    with st.form(f"editar_{ident}"):
        nome = st.text_input(
            "Nome do cliente *", value=encomenda.get("nome_cliente") or ""
        )
        telefone = st.text_input("Telefone", value=encomenda.get("telefone") or "")
        st.caption(
            "Produtos e quantidades por área. Preencha pelo menos uma das três "
            "caixas; alterar o texto repõe essa área como por concluir."
        )
        col_padaria, col_pastelaria, col_cozinha = st.columns(3)
        with col_padaria:
            padaria = st.text_area(
                "Padaria",
                value=encomenda.get("produtos_padaria") or "",
                height=120,
            )
        with col_pastelaria:
            pastelaria = st.text_area(
                "Pastelaria",
                value=encomenda.get("produtos_pastelaria") or "",
                height=120,
            )
        with col_cozinha:
            cozinha = st.text_area(
                "Cozinha",
                value=encomenda.get("produtos_cozinha") or "",
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
        observacoes = st.text_area(
            "Observações", value=encomenda.get("observacoes") or "", height=80
        )
        guardar = st.form_submit_button("Guardar alterações", type="primary")

    if guardar:
        erros: list[str] = []
        if not nome.strip():
            erros.append("Indique o nome do cliente.")
        if not any((padaria.strip(), pastelaria.strip(), cozinha.strip())):
            erros.append("Preencha pelo menos uma área: Padaria, Pastelaria ou Cozinha.")
        if not isinstance(dia, date):
            erros.append("Escolha a data de levantamento.")
        if erros:
            for erro in erros:
                st.error(erro)
            return

        novos_produtos = {
            "produtos_padaria": padaria,
            "produtos_pastelaria": pastelaria,
            "produtos_cozinha": cozinha,
        }
        alteracoes = {
            "nome_cliente": nome,
            "telefone": telefone,
            **novos_produtos,
            "data_levantamento": dia,
            "hora_levantamento": hora,
            "observacoes": observacoes,
        }

        # Uma categoria cujo texto mudou deixa de estar concluída até ser
        # novamente confirmada no perfil Fabrico.
        for _, _, campo_produtos, campo_pronto in db.CATEGORIAS_PRODUTOS:
            if novos_produtos[campo_produtos].strip() != (
                encomenda.get(campo_produtos) or ""
            ).strip():
                alteracoes[campo_pronto] = False

        try:
            db.atualizar_encomenda(ident, alteracoes)
        except db.ErroBaseDados as exc:
            st.error(f"Não foi possível atualizar a encomenda. {exc}")
            return

        ui.marcar_dados_alterados()
        st.session_state.pop("encomenda_edicao", None)
        ui.flash("sucesso", f"Encomenda {numero} atualizada.")
        st.rerun()

    st.button("Cancelar", on_click=_fechar_edicao)


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
        st.button("Cancelar", on_click=_fechar_apagar)
    with col_apagar:
        st.button(
            "Apagar definitivamente",
            type="primary",
            on_click=_apagar_definitivamente,
            args=(ident, numero),
        )


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
        st.session_state["gestao_pagina"] = 1

    if not filtradas:
        st.info("Não há encomendas para estes filtros.")
        return

    st.caption(f"**{len(filtradas)}** encomenda(s)")

    pagina_itens, pagina, total_paginas = ui.paginar(filtradas, "gestao_pagina")
    for encomenda in pagina_itens:
        _cartao(encomenda)

    ui.navegacao_paginas("gestao_pagina", pagina, total_paginas)
