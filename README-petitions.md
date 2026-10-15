# Gerador local de minutas previdenciárias

O `petition_generator.py` lê dados estruturados em YAML e gera uma minuta
editável em **Word (.docx)** ou **texto simples (.txt)**. Os dois formatos usam
os mesmos parágrafos. O gerador funciona localmente e não realiza chamadas de
rede, telemetria nem envio dos casos para APIs.

## Instalação

Use Python 3.10 ou superior. Para Word:

```sh
python -m pip install -r requirements-petitions.txt
```

Para executar os testes:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

O modo de texto simples continua usando apenas a biblioteca padrão do Python.
As dependências de petições ficam separadas das dependências do aplicativo
Flask existente; não é necessário iniciar o servidor de vídeos.

## Gerar arquivos

O exemplo incluído é inteiramente fictício, com CPF de zeros, registro profissional
ilustrativo e endereço eletrônico no domínio reservado `example.invalid`.

```sh
# Word em A4
python petition_generator.py -i cases/exemplo_ficticio.yaml -o out/peticao.docx --page-size a4

# Texto UTF-8
python petition_generator.py -i cases/exemplo_ficticio.yaml -o out/peticao.txt

# Texto no terminal, preservando o comando anterior
python petition_generator.py -i cases/exemplo_ficticio.yaml
```

O formato é inferido pela extensão, sem diferenciar maiúsculas de minúsculas.
Também é possível usar `--format txt` ou `--format docx`. Uma extensão incompatível
com o formato é rejeitada. Word exige `-o`; não é enviado como binário ao terminal.
Arquivos sem extensão usam texto por padrão, ou Word com `--format docx`.
Pastas de saída são criadas automaticamente. A CLI impede usar a própria entrada
como saída. Arquivos de saída existentes são substituídos somente após a geração
bem-sucedida; uma falha de gravação mantém o documento anterior.

## Formatação do Word

- Texto real selecionável e editável, sem imagens do texto e sem proteção de edição.
- Times New Roman 12, texto preto, corpo justificado e espaçamento de 1,5 linha.
- Margens superior e esquerda de 3 cm; inferior e direita de 2 cm.
- Recuo da primeira linha de 1,25 cm; pedidos com recuo pendente.
- Título centralizado, estilos `Title`, `Heading 1` e `Heading 2` e endereçamento em negrito.
- Títulos mantidos com o parágrafo seguinte, controle de linhas órfãs e assinatura agrupada.
- Rodapé com campo de número de página que o editor atualiza ao paginar.
- Idioma de revisão `pt-BR` e metadados genéricos, sem nome de cliente, CPF ou e-mail.

Escolha `--page-size a4` para A4 ou `--page-size letter` para Carta.
Na ausência da opção, o padrão é Carta (8,5 × 11 polegadas).
A fonte precisa estar disponível no computador; substituições feitas pelo Word
ou LibreOffice podem alterar a paginação. Essas escolhas são um padrão visual
configurável no editor, não uma certificação de exigências de cada juízo.

## Dados e compatibilidade

Os campos anteriores continuam disponíveis: `processo`, `partes`, `advogada`,
`beneficio`, `tempos`, `carencia_meses`, `pedidos` e `observacoes`. Consulte
`cases/exemplo_ficticio.yaml` para a estrutura completa.

O campo opcional `data_assinatura: "2026-10-15"` fixa a data nos dois formatos;
sem ele, usa-se a data local do computador. As datas devem ser reais e estar no
formato `AAAA-MM-DD`.

A OAB é normalizada uma única vez na qualificação e na assinatura:

| Entrada | Saída |
| --- | --- |
| `PR 00000` | `OAB/PR 00000` |
| `OAB/PR 00000` | `OAB/PR 00000` |
| `OAB OAB/PR 00000` | `OAB/PR 00000` |
| `00000` | `OAB 00000` |
| ausente ou vazia | `OAB ***` |

Mantenha números de registro entre aspas para preservar zeros à esquerda.
Essa normalização não consulta nem valida uma inscrição profissional.

O parser original aceita um **subconjunto de YAML**: objetos indentados com
espaços, listas de objetos e escalares. Use textos em uma única linha e entre
aspas; use `true`/`false` para booleanos. Recursos completos de YAML, como blocos
multilinha `|`/`>`, âncoras, tags, comentários no fim de uma linha e listas inline,
não são suportados. Não utilize esses recursos no arquivo de entrada.
Para observações com vários parágrafos, a API Python aceita uma string com `\n`.

## API Python

```python
from pathlib import Path
from petition_generator import load_case_data, generate_petition, generate_petition_docx, save_petition

case = load_case_data(Path("cases/exemplo_ficticio.yaml"))
text = generate_petition(case)                       # str, sem dependências externas
word = generate_petition_docx(case, page_size="a4")  # Document editável em memória
save_petition(case, Path("out/peticao.docx"), page_size="a4")
save_petition(case, Path("out/peticao.txt"))
```

O retorno de `generate_petition(case)` continua sendo `str`. A separação de
parágrafos foi uniformizada; não se deve depender dos espaços em branco exatos
da versão anterior. Os pedidos opcionais agora recebem letras contínuas.

## Confidencialidade

Trabalhe com casos reais em uma pasta protegida fora do repositório. Não substitua
os dados do exemplo por dados de clientes. As pastas `cases/` (exceto o exemplo
fictício), `private-data/`, `out/` e os arquivos `.docx` estão no `.gitignore`.
O `.gitignore` não protege arquivos já rastreados nem arquivos em outros locais;
revise as alterações antes de qualquer commit.

O programa não registra o conteúdo dos casos em logs. Os erros da CLI não
reproduzem linhas de entrada ou dados do cliente. Quando não se usa `-o`, o texto
é impresso intencionalmente no terminal; use saída em arquivo para evitar que
o conteúdo vá para históricos de sessões ou logs de execução.

A gravação por `save_petition` é atômica e utiliza permissões privadas (`0600`)
em sistemas POSIX. No Windows, o acesso depende das permissões da pasta.
Os arquivos produzidos contêm os dados fornecidos no corpo da petição e **não
são criptografados**. Metadados são genéricos na geração; um editor pode inserir
seus próprios metadados depois. Não há anonimização automática do corpo.

## Limites da minuta e testes

O modelo herdado foi escrito para concessão por tempo de contribuição, usa
qualificação feminina e ainda requer adequação do conteúdo a cada caso.
Não calcula tempo ou carência, não confere documentos, não seleciona regras de
transição nem verifica direito ao benefício. A informação de carência agora é
apresentada como dado informado sujeito à conferência, sem concluir que o número
é suficiente. O pedido de gratuidade não insere uma referência legal fixa.
Fundamentos jurídicos e requisitos da peça devem ser conferidos pela advogada
antes do protocolo; esta alteração é de software e apresentação, sem auditoria
jurisprudencial do modelo original.

Os testes usam somente dados fictícios e cobrem OAB, equivalência entre formatos,
edição e reabertura do Word, estilos, margens, paginação, datas, comandos de saída,
dependência opcional, erros sem exposição de dados, ausência de conexões de rede,
metadados e preservação de arquivo anterior em falha de gravação.
