from __future__ import annotations

from pathlib import Path

from petition_generator import (
    build_cli,
    format_date,
    generate_petition,
    load_case_data,
    main,
)


def test_format_date_pt_br():
    assert format_date("2024-05-20") == "20 de maio de 2024"


def test_generate_petition_structure(tmp_path: Path):
    yaml_data = {
        "processo": {"foro": "JEF", "secao": "SJ/PR"},
        "partes": {
            "autora": "Maria",  # nome fictício
            "cpf": "000.000.000-00",
            "endereco": "Rua X",
        },
        "advogada": {
            "nome": "Fulana",
            "oab": "OAB/PR 00000",
            "email": "fulana@example.com",
        },
        "beneficio": {
            "tipo": "aposentadoria por tempo",
            "der": "2024-05-20",
            "regra_transicao": "pontos",
        },
        "tempos": {
            "vinculos": [
                {
                    "inicio": "1986-08-28",
                    "fim": "1991-10-30",
                    "categoria": "rural",
                }
            ],
            "especial": [
                {
                    "inicio": "1995-03-01",
                    "fim": "2002-07-31",
                    "agente": "ruído > 85 dB",
                    "ppp": True,
                }
            ],
            "conversao_especial": True,
        },
        "carencia_meses": 180,
        "pedidos": {
            "tutela_implantacao": True,
            "correcao_juros": "SELIC",
            "gratuidade": True,
        },
        "observacoes": "Documentos anexos.",
    }

    yaml_file = tmp_path / "caso.yaml"
    yaml_file.write_text(
        """
processo:
  foro: "JEF"
  secao: "SJ/PR"
partes:
  autora: "Maria"
  cpf: "000.000.000-00"
  endereco: "Rua X"
advogada:
  nome: "Fulana"
  oab: "OAB/PR 00000"
  email: "fulana@example.com"
beneficio:
  tipo: "aposentadoria por tempo"
  der: "2024-05-20"
  regra_transicao: "pontos"
tempos:
  vinculos:
    - inicio: "1986-08-28"
      fim: "1991-10-30"
      categoria: "rural"
  especial:
    - inicio: "1995-03-01"
      fim: "2002-07-31"
      agente: "ruído > 85 dB"
      ppp: true
  conversao_especial: true
carencia_meses: 180
pedidos:
  tutela_implantacao: true
  correcao_juros: "SELIC"
  gratuidade: true
observacoes: "Documentos anexos."
""".strip(),
        encoding="utf-8",
    )

    texto = generate_petition(yaml_data)
    carregado = load_case_data(yaml_file)

    assert carregado["partes"]["autora"] == "Maria"
    assert carregado["tempos"]["especial"][0]["ppp"] is True

    assert "Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) Federal" in texto
    assert "AÇÃO PREVIDENCIÁRIA DE CONCESSÃO DE BENEFÍCIO" in texto
    assert "Documentos anexos." in texto
    assert "OAB OAB/PR 00000" in texto


def test_cli_help_mentions_example_usage():
    help_text = build_cli().format_help()
    assert "python petition_generator.py -i" in help_text


def test_main_creates_output_directory(tmp_path: Path):
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text(
        """
processo:
  foro: "JEF"
  secao: "SJ/PR"
partes:
  autora: "Maria"
  cpf: "000.000.000-00"
  endereco: "Rua X"
advogada:
  nome: "Fulana"
  oab: "OAB/PR 00000"
  email: "fulana@example.com"
beneficio:
  tipo: "aposentadoria por tempo"
  der: "2024-05-20"
  regra_transicao: "pontos"
tempos:
  vinculos:
    - inicio: "1986-08-28"
      fim: "1991-10-30"
      categoria: "rural"
carencia_meses: 180
pedidos:
  gratuidade: true
""".strip(),
        encoding="utf-8",
    )

    output_file = tmp_path / "subdir" / "peticao.txt"
    main(["-i", str(yaml_file), "-o", str(output_file)])

    texto = output_file.read_text(encoding="utf-8")
    assert "Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) Federal" in texto
    assert output_file.exists()

