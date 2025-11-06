"""Utility for generating Previdenciary petitions from YAML case data.

This module parses structured YAML information that describes a social
security claim and turns it into a ready-to-edit draft petition in
Portuguese.  The goal is to give lawyers a quick starting point with all
relevant facts, links, and pedidos already organized in a textual format.
"""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path
from typing import Any, Dict, Iterable, List

MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def load_case_data(source: Path) -> Dict[str, Any]:
    """Load the YAML case description from ``source``.

    This implementation intentionally avoids external dependencies so the
    project can run in restricted environments.  The supported YAML subset
    covers dictionaries, lists and scalar values (strings, numbers and
    booleans), which is sufficient for the structured data used by the
    application.
    """

    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - thin wrapper
        raise SystemExit(f"Arquivo não encontrado: {source}") from exc

    return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a minimal subset of YAML into Python structures."""

    lines = [
        (len(line) - len(line.lstrip(" ")), line.strip())
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    value, index = _parse_block(lines, 0, 0)
    if index != len(lines):  # pragma: no cover - defensive branch
        raise ValueError("Não foi possível interpretar todo o arquivo YAML.")
    if not isinstance(value, dict):
        raise ValueError("A raiz do YAML deve ser um objeto (mapping).")
    return value


def _parse_block(lines: List[tuple[int, str]], start: int, indent: int):
    result: Any = None
    idx = start

    while idx < len(lines):
        line_indent, content = lines[idx]
        if line_indent < indent:
            break

        if content.startswith("- "):
            if result is None:
                result = []
            elif not isinstance(result, list):
                break

            value_part = content[2:].strip()
            idx += 1

            if not value_part:
                item, idx = _parse_block(lines, idx, line_indent + 2)
                result.append(item)
                continue

            if ":" in value_part:
                key, raw_val = value_part.split(":", 1)
                key = key.strip()
                raw_val = raw_val.strip()
                item: Dict[str, Any] = {}

                if raw_val:
                    item[key] = _parse_scalar(raw_val)
                else:
                    child, idx = _parse_block(lines, idx, line_indent + 2)
                    item[key] = child

                if idx < len(lines) and lines[idx][0] > line_indent:
                    extra, idx = _parse_block(lines, idx, line_indent + 2)
                    if isinstance(extra, dict):
                        item.update(extra)
                    else:  # pragma: no cover - malformed structure
                        raise ValueError("Estrutura de lista inválida.")

                result.append(item)
            else:
                result.append(_parse_scalar(value_part))
                if idx < len(lines) and lines[idx][0] > line_indent:
                    extra, idx = _parse_block(lines, idx, line_indent + 2)
                    result[-1] = extra

            continue

        if result is None:
            result = {}
        elif not isinstance(result, dict):
            break

        if ":" not in content:
            raise ValueError(f"Linha inválida no YAML: {content}")

        key, raw_val = content.split(":", 1)
        key = key.strip()
        raw_val = raw_val.strip()
        idx += 1

        if raw_val:
            result[key] = _parse_scalar(raw_val)
        else:
            child, idx = _parse_block(lines, idx, line_indent + 2)
            result[key] = child

    if result is None:
        result = {}

    return result, idx


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None

    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def format_date(date_str: str) -> str:
    """Convert an ISO date string (YYYY-MM-DD) to long Portuguese format."""

    if not date_str:
        return ""

    year, month, day = map(int, date_str.split("-"))
    month_name = MONTHS_PT.get(month, str(month))
    return f"{day:02d} de {month_name} de {year}"


def _format_vinculos(vinculos: Iterable[Dict[str, Any]]) -> List[str]:
    formatted = []
    for vinculo in vinculos:
        inicio = format_date(vinculo.get("inicio", ""))
        fim = format_date(vinculo.get("fim", ""))
        categoria = vinculo.get("categoria", "não informado")
        formatted.append(
            f"Período de {inicio} a {fim}, na qualidade de segurada {categoria}."
        )
    return formatted


def _format_especial(especial: Iterable[Dict[str, Any]]) -> List[str]:
    formatted = []
    for periodo in especial:
        inicio = format_date(periodo.get("inicio", ""))
        fim = format_date(periodo.get("fim", ""))
        agente = periodo.get("agente", "agente nocivo não informado")
        ppp = "com PPP anexado" if periodo.get("ppp") else "sem PPP comprovado"
        formatted.append(
            f"Atividade especial de {inicio} a {fim}, exposta a {agente}, {ppp}."
        )
    return formatted


def generate_petition(case_data: Dict[str, Any]) -> str:
    """Generate a textual petition draft from the case data."""

    processo = case_data.get("processo", {})
    partes = case_data.get("partes", {})
    advogada = case_data.get("advogada", {})
    beneficio = case_data.get("beneficio", {})
    tempos = case_data.get("tempos", {})
    pedidos = case_data.get("pedidos", {})
    observacoes = case_data.get("observacoes")

    header = (
        f"Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) Federal da "
        f"{processo.get('foro', 'Vara Federal')} da Seção Judiciária "
        f"{processo.get('secao', '')}"
    ).strip()

    intro = (
        f"{partes.get('autora', 'A autora')}, brasileira, portadora do CPF nº "
        f"{partes.get('cpf', '***')}, residente na {partes.get('endereco', '')}, "
        "por sua advogada que esta subscreve (" +
        f"OAB {advogada.get('oab', '***')}), com endereço eletrônico "
        f"{advogada.get('email', '***')}, vem, respeitosamente, propor a presente\n"
        "AÇÃO PREVIDENCIÁRIA DE CONCESSÃO DE BENEFÍCIO por tempo de contribuição."  # noqa: E501
    )

    beneficio_descr = (
        f"Requer a concessão do benefício de {beneficio.get('tipo', '').upper()}"
        f", com DER em {format_date(beneficio.get('der', ''))}, sob a regra de "
        f"transição {beneficio.get('regra_transicao', 'não informada')}.")

    vinculos = _format_vinculos(tempos.get("vinculos", []))
    especial = _format_especial(tempos.get("especial", []))

    narrativa: List[str] = [
        "\n1. DOS FATOS",
        beneficio_descr,
        "",  # blank line
        "1.1. Do tempo rural/urbano",
    ]

    if vinculos:
        narrativa.extend(vinculos)
    else:
        narrativa.append("Não foram informados vínculos comuns.")

    narrativa.extend(["", "1.2. Do tempo especial"])

    if especial:
        narrativa.extend(especial)
    else:
        narrativa.append("Não foram informados períodos especiais.")

    if tempos.get("conversao_especial"):
        narrativa.append(
            "Requer a conversão do tempo especial em comum, com aplicação do fator correspondente."  # noqa: E501
        )

    carencia = case_data.get("carencia_meses")
    narrativa.extend(
        [
            "",
            "1.3. Da carência",
            f"A segurada comprova {carencia} contribuições, suficientes para a carência exigida." if carencia else "A carência deverá ser comprovada em instrução.",  # noqa: E501
        ]
    )

    pedidos_list = ["\n2. DOS PEDIDOS"]

    if pedidos.get("gratuidade"):
        pedidos_list.append(
            "a) A concessão dos benefícios da justiça gratuita, nos termos da Lei nº 1.060/50 e do CPC."  # noqa: E501
        )

    pedidos_list.append(
        "b) O reconhecimento dos períodos de labor acima descritos, com a devida averbação."  # noqa: E501
    )

    if pedidos.get("tutela_implantacao"):
        pedidos_list.append(
            "c) A concessão de tutela de urgência para imediata implantação do benefício."  # noqa: E501
        )

    juros = pedidos.get("correcao_juros", "")
    if juros:
        pedidos_list.append(
            f"d) A aplicação do índice de atualização {juros} até o efetivo pagamento."  # noqa: E501
        )

    pedidos_list.append(
        "e) A condenação do INSS ao pagamento das parcelas vencidas, acrescidas de juros e correção monetária."  # noqa: E501
    )

    if observacoes:
        pedidos_list.extend(
            [
                "",
                "3. DAS PROVAS",
                "A parte autora se vale dos documentos já acostados, em especial:",
                observacoes,
            ]
        )

    data_assinatura = format_date(_dt.date.today().isoformat())
    rodape = (
        f"\nTermos em que,\nPede deferimento.\n\n{processo.get('secao', '')}, {data_assinatura}.\n"
        f"{advogada.get('nome', 'Advogada')}\nOAB {advogada.get('oab', '***')}"
    )

    sections = [header, "", intro, "", *narrativa, "", *pedidos_list, rodape]
    return "\n".join(line for line in sections if line is not None)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera minuta de petição previdenciária a partir de um YAML."
    )
    parser.add_argument(
        "arquivo",
        type=Path,
        help="Caminho para o arquivo YAML com os dados do processo.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Arquivo de saída (opcional). Caso não informado, imprime no terminal.",
    )
    return parser


def main(args: List[str] | None = None) -> None:
    parser = build_cli()
    namespace = parser.parse_args(args)
    case_data = load_case_data(namespace.arquivo)
    texto = generate_petition(case_data)

    if namespace.output:
        namespace.output.write_text(texto, encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

