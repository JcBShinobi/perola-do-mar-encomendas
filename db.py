"""Acesso ao Supabase para as encomendas de Natal.

Este módulo isola toda a comunicação com a base de dados: a UI só lida com
listas/dicionários e com mensagens de erro já traduzidas para português.
"""
from __future__ import annotations

from datetime import date, time
from typing import Any

import streamlit as st
from supabase import Client, create_client

TABELA = "encomendas"
ESTADOS_PAGAMENTO: tuple[str, ...] = ("Por Pagar", "Pago")
LIMITE_CONSULTA = 1000


class ErroBaseDados(Exception):
    """Falha de comunicação/persistência, já traduzida para a UI."""


class ErroConfiguracao(ErroBaseDados):
    """Credenciais em falta ou mal configuradas em st.secrets."""


def _traduzir(exc: Exception) -> str:
    """Converte erros técnicos do Supabase/PostgREST em mensagens úteis."""
    texto = str(exc)
    minusculo = texto.lower()

    if "numero_encomenda" in minusculo and (
        "null value" in minusculo or "not-null" in minusculo
    ):
        return (
            "A tabela 'encomendas' está sem o número automático da encomenda. "
            "Execute novamente o schema.sql no SQL Editor do Supabase."
        )

    if (
        "could not find the table" in minusculo
        or "schema cache" in minusculo
        or ("relation" in minusculo and "does not exist" in minusculo)
        or "pgrst205" in minusculo
    ):
        return (
            "A tabela 'encomendas' não está disponível no Supabase. "
            "Execute o script schema.sql no SQL Editor do Supabase e tente novamente."
        )

    if "invalid api key" in minusculo or "invalid jwt" in minusculo or "401" in minusculo:
        return (
            "A SUPABASE_KEY foi recusada. Copie novamente a chave 'anon public' "
            "do Supabase para .streamlit/secrets.toml."
        )

    if (
        "row-level security" in minusculo
        or "permission denied" in minusculo
        or "42501" in minusculo
    ):
        return (
            "Sem permissão para aceder à tabela. Execute a parte final do schema.sql "
            "(RLS e GRANTs) no Supabase."
        )

    if "duplicate key" in minusculo or "23505" in minusculo:
        return "Conflito no número da encomenda. Tente guardar novamente."

    if any(
        pista in minusculo
        for pista in (
            "getaddrinfo",
            "name or service not known",
            "nodename nor servname",
            "timed out",
            "timeout",
            "connection",
            "network",
            "ssl",
            "temporary failure",
        )
    ):
        return "Sem ligação à internet ou ao Supabase. Verifique a rede e a SUPABASE_URL."

    return f"Erro inesperado da base de dados: {texto}"


@st.cache_resource(show_spinner="A ligar ao Supabase…")
def get_client() -> Client:
    """Cria (e reutiliza) o cliente oficial do Supabase."""
    try:
        url = str(st.secrets["SUPABASE_URL"]).strip()
        chave = str(st.secrets["SUPABASE_KEY"]).strip()
    except (KeyError, FileNotFoundError):
        raise ErroConfiguracao(
            "faltam SUPABASE_URL e SUPABASE_KEY em .streamlit/secrets.toml."
        ) from None

    if not url.startswith("https://") or not chave:
        raise ErroConfiguracao(
            "SUPABASE_URL deve começar por https:// e SUPABASE_KEY não pode estar vazia."
        )

    try:
        return create_client(url, chave)
    except Exception as exc:  # URL/key estruturalmente inválidas
        raise ErroBaseDados(
            f"Não foi possível iniciar o cliente Supabase. {exc}"
        ) from exc


def verificar_ligacao() -> None:
    """Confirma que o cliente e a tabela estão acessíveis."""
    cliente = get_client()
    try:
        cliente.table(TABELA).select("id").limit(1).execute()
    except ErroBaseDados:
        raise
    except Exception as exc:
        raise ErroBaseDados(_traduzir(exc)) from exc


def criar_encomenda(dados: dict[str, Any]) -> dict[str, Any]:
    """Insere uma encomenda e devolve o registo completo (com o nº gerado)."""
    nome = (dados.get("nome_cliente") or "").strip()
    produtos = (dados.get("produtos") or "").strip()
    dia = dados.get("data_levantamento")

    if not nome:
        raise ErroBaseDados("O nome do cliente é obrigatório.")
    if not produtos:
        raise ErroBaseDados("Indique os produtos da encomenda.")
    if not isinstance(dia, date):
        raise ErroBaseDados("A data de levantamento é obrigatória.")

    hora = dados.get("hora_levantamento")
    pagamento = dados.get("estado_pagamento") or "Por Pagar"
    if pagamento not in ESTADOS_PAGAMENTO:
        pagamento = "Por Pagar"

    registo = {
        "nome_cliente": nome,
        "telefone": (dados.get("telefone") or "").strip() or None,
        "produtos": produtos,
        "data_levantamento": dia.isoformat(),
        "hora_levantamento": hora.strftime("%H:%M:%S") if isinstance(hora, time) else None,
        "estado_pagamento": pagamento,
        "observacoes": (dados.get("observacoes") or "").strip() or None,
    }

    cliente = get_client()
    try:
        # numero_encomenda é preenchido pela sequência definida no schema.sql.
        resposta = cliente.table(TABELA).insert(registo).select("*").execute()
    except Exception as exc:
        raise ErroBaseDados(_traduzir(exc)) from exc

    linhas = resposta.data or []
    if not linhas:
        raise ErroBaseDados(
            "A encomenda foi enviada mas não foi possível confirmar a gravação. "
            "Verifique a aba de consulta antes de a repetir."
        )
    return linhas[0]


def listar_encomendas(
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[dict[str, Any]]:
    """Lista encomendas ordenadas por data/hora (opcionalmente num intervalo)."""
    cliente = get_client()
    try:
        consulta = cliente.table(TABELA).select("*")
        if data_inicio is not None:
            consulta = consulta.gte("data_levantamento", data_inicio.isoformat())
        if data_fim is not None:
            consulta = consulta.lte("data_levantamento", data_fim.isoformat())

        resposta = (
            consulta.order("data_levantamento")
            .order("hora_levantamento")
            .order("numero_encomenda")
            .limit(LIMITE_CONSULTA)
            .execute()
        )
    except Exception as exc:
        raise ErroBaseDados(_traduzir(exc)) from exc

    return list(resposta.data or [])


def atualizar_estado_pagamento(encomenda_id: int, pago: bool) -> None:
    """Marca a encomenda como paga ou por pagar."""
    _atualizar(
        encomenda_id,
        {"estado_pagamento": "Pago" if pago else "Por Pagar"},
    )


def atualizar_encomenda(encomenda_id: int, dados: dict[str, Any]) -> None:
    """Atualiza os dados editáveis de uma encomenda existente."""
    nome = (dados.get("nome_cliente") or "").strip()
    produtos = (dados.get("produtos") or "").strip()
    dia = dados.get("data_levantamento")

    if not nome:
        raise ErroBaseDados("O nome do cliente é obrigatório.")
    if not produtos:
        raise ErroBaseDados("Indique os produtos da encomenda.")
    if not isinstance(dia, date):
        raise ErroBaseDados("A data de levantamento é obrigatória.")

    hora = dados.get("hora_levantamento")
    pagamento = dados.get("estado_pagamento") or "Por Pagar"
    if pagamento not in ESTADOS_PAGAMENTO:
        pagamento = "Por Pagar"

    _atualizar(
        encomenda_id,
        {
            "nome_cliente": nome,
            "telefone": (dados.get("telefone") or "").strip() or None,
            "produtos": produtos,
            "data_levantamento": dia.isoformat(),
            "hora_levantamento": hora.strftime("%H:%M:%S")
            if isinstance(hora, time)
            else None,
            "estado_pagamento": pagamento,
            "observacoes": (dados.get("observacoes") or "").strip() or None,
        },
    )


def apagar_encomenda(encomenda_id: int) -> None:
    """Elimina permanentemente uma encomenda."""
    cliente = get_client()
    try:
        cliente.table(TABELA).delete().eq("id", int(encomenda_id)).execute()
    except Exception as exc:
        raise ErroBaseDados(_traduzir(exc)) from exc


def _atualizar(encomenda_id: int, alteracoes: dict[str, Any]) -> None:
    cliente = get_client()
    try:
        cliente.table(TABELA).update(alteracoes).eq("id", int(encomenda_id)).execute()
    except Exception as exc:
        raise ErroBaseDados(_traduzir(exc)) from exc
