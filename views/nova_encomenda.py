"""Registo de uma nova encomenda de Natal."""
from __future__ import annotations

import html
from datetime import date, timedelta

import streamlit as st

import db
import ui
from utils import formatar_data, formatar_hora, formatar_numero, link_sms


def _fechar_ultima() -> None:
    st.session_state.pop("ultima_encomenda", None)


def _mostrar_ultima_encomenda() -> None:
    """Cartão gigante com o número que o funcionário deve dizer ao cliente."""
    registo = st.session_state.get("ultima_encomenda")
    if not registo:
        return

    nome = registo.get("nome_cliente") or ""
    quando = formatar_data(registo.get("data_levantamento"))
    hora = formatar_hora(registo.get("hora_levantamento"))
    if hora:
        quando = f"{quando} às {hora}"
    detalhe = " · ".join(parte for parte in (nome, quando) if parte)

    st.markdown(
        f"""
        <div class="numero-destaque">
            <div class="nd-label">Encomenda registada</div>
            <div class="nd-valor">{html.escape(formatar_numero(registo.get("numero_encomenda")))}</div>
            <div class="nd-info">{html.escape(detalhe)}</div>
            <div class="nd-hint">Comunique este número ao cliente 🎄</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    link = link_sms(registo)
    if link:
        col_mensagem, col_nova = st.columns(2)
        with col_mensagem:
            st.link_button(
                "💬 Enviar mensagem",
                link,
                type="primary",
                width="stretch",
            )
        with col_nova:
            st.button(
                "Registar outra encomenda",
                key="fechar_ultima",
                width="stretch",
                on_click=_fechar_ultima,
            )
    else:
        st.button(
            "Registar outra encomenda",
            key="fechar_ultima",
            on_click=_fechar_ultima,
        )


def _guardar(
    nome: str,
    telefone: str,
    funcionario: str,
    padaria: str,
    pastelaria: str,
    cozinha: str,
    dia: date,
    hora: object,
    observacoes: str,
) -> None:
    erros: list[str] = []
    if not nome.strip():
        erros.append("Indique o nome do cliente.")
    if not telefone.strip():
        erros.append("Indique o número de telefone.")
    if not funcionario.strip():
        erros.append("Indique o funcionário.")
    if not any((padaria.strip(), pastelaria.strip(), cozinha.strip())):
        erros.append("Preencha pelo menos uma área: Padaria, Pastelaria ou Cozinha.")
    if not isinstance(dia, date):
        erros.append("Escolha a data de levantamento.")
    if erros:
        for erro in erros:
            st.error(erro)
        return

    try:
        registo = db.criar_encomenda(
            {
                "nome_cliente": nome,
                "telefone": telefone,
                "funcionario": funcionario,
                "produtos_padaria": padaria,
                "produtos_pastelaria": pastelaria,
                "produtos_cozinha": cozinha,
                "data_levantamento": dia,
                "hora_levantamento": hora,
                "observacoes": observacoes,
            }
        )
    except db.ErroBaseDados as exc:
        st.error(f"Não foi possível guardar a encomenda. {exc}")
        return

    ui.marcar_dados_alterados()

    # Nova chave de formulário => todos os campos voltam ao estado inicial.
    st.session_state["ultima_encomenda"] = registo
    st.session_state["form_versao"] = st.session_state.get("form_versao", 0) + 1
    st.rerun()


def render() -> None:
    _mostrar_ultima_encomenda()

    versao = st.session_state.get("form_versao", 0)
    with st.form(f"nova_encomenda_{versao}"):
        nome = st.text_input(
            "Nome do cliente *",
            key=f"nc_nome_{versao}",
            placeholder="Ex.: Maria Silva",
        )
        col_telefone, col_funcionario = st.columns(2)
        with col_telefone:
            telefone = st.text_input(
                "Telefone *",
                key=f"nc_telefone_{versao}",
                placeholder="Ex.: 912 345 678",
            )
        with col_funcionario:
            funcionario = st.text_input(
                "Funcionário *",
                key=f"nc_funcionario_{versao}",
                placeholder="Ex.: Ana",
            )
        col_padaria, col_pastelaria, col_cozinha = st.columns(3)
        with col_padaria:
            padaria = st.text_area(
                "Padaria",
                key=f"nc_padaria_{versao}",
                height=130,
                placeholder="Ex.:\n2 pães de ló\n12 pães de Deus",
            )
        with col_pastelaria:
            pastelaria = st.text_area(
                "Pastelaria",
                key=f"nc_pastelaria_{versao}",
                height=130,
                placeholder="Ex.:\n2 bolos-rei tradicionais\n12 filhós",
            )
        with col_cozinha:
            cozinha = st.text_area(
                "Cozinha",
                key=f"nc_cozinha_{versao}",
                height=130,
                placeholder="Ex.:\n40 rissóis\n20 empadas",
            )

        col_data, col_hora = st.columns(2)
        with col_data:
            dia = st.date_input(
                "Data de levantamento *",
                value=date.today() + timedelta(days=1),
                min_value=date.today(),
                format="DD/MM/YYYY",
                key=f"nc_data_{versao}",
            )
        with col_hora:
            hora = st.time_input(
                "Hora (opcional)",
                value=None,
                step=timedelta(minutes=15),
                key=f"nc_hora_{versao}",
            )

        observacoes = st.text_area(
            "Observações",
            key=f"nc_observacoes_{versao}",
            height=80,
            placeholder="Ex.: sem frutos secos; embalagem com laço",
        )

        submetido = st.form_submit_button("✅ Guardar encomenda", type="primary")

    if submetido:
        _guardar(
            nome,
            telefone,
            funcionario,
            padaria,
            pastelaria,
            cozinha,
            dia,
            hora,
            observacoes,
        )
