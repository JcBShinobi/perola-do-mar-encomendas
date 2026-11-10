"""Funções puras de formatação e de análise do texto dos produtos.

Ficam fora dos módulos de UI para serem testáveis e reutilizáveis.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, time
from typing import Iterable

MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)

DIAS_SEMANA = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

# "3 bolos", "3x bolos", "3 × bolos", "(3) bolos", "1,5 kg de amêndoa"
_RE_QUANTIDADE = re.compile(
    r"^\s*\(?(\d+(?:[.,]\d+)?)\)?\s*(?:x|×)?\s*(.+?)\s*$",
    re.IGNORECASE,
)


def _para_data(valor: object) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        try:
            return date.fromisoformat(valor.strip()[:10])
        except ValueError:
            return None
    return None


def _para_hora(valor: object) -> time | None:
    if isinstance(valor, time):
        return valor
    if isinstance(valor, str) and valor.strip():
        texto = valor.strip()
        for formato in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(texto[:8], formato).time()
            except ValueError:
                continue
    return None


def formatar_data(valor: object) -> str:
    """Devolve a data no formato DD/MM/AAAA (ou — se inválida)."""
    dia = _para_data(valor)
    return dia.strftime("%d/%m/%Y") if dia else "—"


def formatar_data_extenso(valor: object) -> str:
    """Ex.: 'quinta-feira, 24 de dezembro de 2026'."""
    dia = _para_data(valor)
    if not dia:
        return "—"
    return f"{DIAS_SEMANA[dia.weekday()]}, {dia.day} de {MESES[dia.month - 1]} de {dia.year}"


def formatar_hora(valor: object) -> str:
    """Devolve HH:MM (ou string vazia se não houver hora)."""
    hora = _para_hora(valor)
    return hora.strftime("%H:%M") if hora else ""


def formatar_numero(valor: object) -> str:
    """Formata o número da encomenda como #0001."""
    if valor is None or str(valor).strip() == "":
        return "—"
    try:
        return f"#{int(valor):04d}"
    except (TypeError, ValueError):
        return "—"


def formatar_quantidade(valor: float) -> str:
    """Mostra 3 em vez de 3.0 e 1,5 em vez de 1.5."""
    numero = float(valor)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.1f}".replace(".", ",")


def proximo_24_dezembro(hoje: date | None = None) -> date:
    """Data de 24 de dezembro mais próxima (este ano ou o seguinte)."""
    referencia = hoje or date.today()
    alvo = date(referencia.year, 12, 24)
    if alvo < referencia:
        return date(referencia.year + 1, 12, 24)
    return alvo


def dividir_linhas(texto: str | None) -> list[str]:
    """Separa um bloco de produtos em linhas individuais.

    Divide por mudanças de linha, ponto e vírgula e vírgulas seguidas de
    quantidade ("2 bolos, 3 pães"), removendo marcadores de lista. As vírgulas
    decimais ("1,5 kg") são preservadas.
    """
    if not texto:
        return []

    linhas: list[str] = []
    for bloco in re.split(r"[\n\r;]+", texto):
        for parte in re.split(r"(?<!\d),\s*(?=\d)", bloco):
            limpa = re.sub(r"^\s*[-•*–—]\s*", "", parte).strip()
            if limpa:
                linhas.append(limpa)
    return linhas


def interpretar_linha(linha: str) -> tuple[float, str, bool]:
    """Extrai (quantidade, produto, quantidade explícita) de uma linha."""
    correspondencia = _RE_QUANTIDADE.match(linha)
    if correspondencia:
        quantidade = float(correspondencia.group(1).replace(",", "."))
        nome = correspondencia.group(2).strip(" .-–—")
        if nome and nome not in {"x", "×"} and quantidade > 0:
            return quantidade, nome, True
    return 1.0, linha.strip(" .-•–—"), False


def _chave_produto(nome: str) -> str:
    """Normaliza o nome para agrupar variantes ('Bolos-Rei' == 'bolo rei')."""
    texto = unicodedata.normalize("NFKC", nome).casefold()
    texto = re.sub(r"[^\w\sÀ-ÿ%]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) > 3 and texto.endswith("s") and not texto.endswith(("ss", "es")):
        texto = texto[:-1].rstrip()
    return texto


def agregar_produtos(textos: Iterable[str | None]) -> list[dict]:
    """Soma as quantidades de todas as linhas de produtos.

    Devolve uma lista de dicionários com:
    produto, quantidade, linhas (nº de menções) e estimada (havia linhas sem
    quantidade explícita, contadas como 1 unidade).
    """
    agregados: dict[str, dict] = {}

    for texto in textos:
        for linha in dividir_linhas(texto):
            quantidade, nome, explicita = interpretar_linha(linha)
            if not nome:
                continue
            chave = _chave_produto(nome)
            if not chave:
                continue

            registo = agregados.setdefault(
                chave,
                {
                    "produto": nome,
                    "quantidade": 0.0,
                    "linhas": 0,
                    "estimada": False,
                },
            )
            registo["quantidade"] += quantidade
            registo["linhas"] += 1
            if not explicita:
                registo["estimada"] = True

    return sorted(
        agregados.values(),
        key=lambda registo: (-registo["quantidade"], registo["produto"].casefold()),
    )
