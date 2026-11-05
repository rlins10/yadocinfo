# yadocinfo

**Yet Another Document Information** — catalogador local de documentos com extração de conteúdo e geração de descrições por modelos de linguagem.

A ideia é manter um índice pesquisável de documentos heterogêneos sem mover nem alterar os arquivos originais. O yadocinfo registra o diretório-base, o caminho relativo, o nome do arquivo, tamanho, data de modificação e hash SHA-256, além da descrição e dos metadados produzidos durante a interpretação.

## Características

- Varredura **não recursiva**: somente os arquivos do diretório informado na linha de comando.
- Um ou mais diretórios-base configurados em `~/.config/yadocinfo/config.yaml`.
- Caminhos persistidos como diretório-base + caminho relativo + nome do arquivo.
- Verificação de integridade por SHA-256 (padrão) ou MD5.
- SQLite como banco padrão; MariaDB e PostgreSQL opcionais.
- Ollama local como provedor padrão e `gemma4:12b` como modelo padrão.
- Modos de envio `text`, `vision` e `auto`.
- Extratores iniciais para PDF, DOCX, XLSX, PPTX, TXT, CSV, HTML e RTF (RTF com extração textual básica).
- OCR opcional via Tesseract para PDFs digitalizados.
- Arquivos originais nunca são modificados.

## Requisitos

- Python 3.11 ou superior.
- Para interpretação por IA: Ollama instalado e em execução.
- Para OCR opcional: Tesseract instalado no sistema e o extra opcional `ocr`.

## Instalação do Ollama

Consulte o repositório oficial do Ollama:

- https://github.com/ollama/ollama
- Site e instruções oficiais: https://ollama.com/download

No Linux, a instalação padrão indicada pelo projeto é:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Inicie o serviço (a forma exata depende da distribuição/instalação):

```bash
ollama serve
```

Em outro terminal, baixe o modelo Gemma 4:

```bash
ollama pull gemma4:12b
```

Confirme que está disponível:

```bash
ollama list
```

O modelo pode exigir memória significativa. Ajuste `ai.model` no YAML caso utilize outra variante Gemma 4 ou outro modelo compatível com texto/imagem.

## Instalação do yadocinfo

Instalação diretamente do GitHub:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "git+https://github.com/SEU_USUARIO/yadocinfo.git"
```

Substitua `SEU_USUARIO` pelo proprietário do repositório quando o projeto for publicado.

Para instalar a partir de um clone:

```bash
git clone https://github.com/SEU_USUARIO/yadocinfo.git
cd yadocinfo
python -m pip install .
```

Dependências opcionais:

```bash
python -m pip install ".[mariadb]"
python -m pip install ".[postgresql]"
python -m pip install ".[ocr]"
```

Para OCR, instale também o Tesseract no sistema operacional. Em Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-por
```

## Configuração inicial

Execute:

```bash
yadocinfo init
```

O instalador interativo:

1. Cria `~/.config/yadocinfo/`.
2. Pergunta qual banco será utilizado (SQLite, MariaDB ou PostgreSQL).
3. Solicita os parâmetros de conexão quando necessário.
4. Define um ou mais diretórios-base.
5. Configura provedor, endpoint, modelo e modo de envio ao modelo.
6. Grava o YAML e cria as tabelas.

Para MariaDB e PostgreSQL, o instalador tenta criar o banco informado caso ainda não exista; o usuário configurado precisa ter permissão de criação de bancos e tabelas. No PostgreSQL, a conexão administrativa inicial é feita ao banco padrão `postgres`. O SQLite é criado automaticamente.

## Exemplo de configuração

O arquivo fica em `~/.config/yadocinfo/config.yaml`:

```yaml
database:
  driver: sqlite
  sqlite_path: "~/.config/yadocinfo/yadocinfo.db"
  mariadb:
    host: localhost
    port: 3306
    database: yadocinfo
    username: yadocinfo
    password: ""
  postgresql:
    host: localhost
    port: 5432
    database: yadocinfo
    username: yadocinfo
    password: ""

directories:
  - name: documentos
    path: "~/Documentos"
  - name: arquivo
    path: "/srv/arquivo"

integrity:
  algorithm: sha256

ai:
  provider: ollama
  endpoint: "http://localhost:11434"
  model: "gemma4:12b"
  input_mode: auto
  max_pages: 8
  max_chars: 24000
  timeout: 300
  temperature: 0.1

processing:
  ocr_enabled: false
  ocr_language: por
  include_hidden: false
```

Senhas podem ser definidas no YAML, mas recomenda-se restringir suas permissões:

```bash
chmod 600 ~/.config/yadocinfo/config.yaml
```

## Uso

Liste os diretórios-base:

```bash
yadocinfo bases
```

Analise um diretório-base inteiro (somente o primeiro nível):

```bash
yadocinfo scan ~/Documentos
```

Ou informe um subdiretório dentro de uma base configurada:

```bash
yadocinfo scan ~/Documentos/Contratos
```

A varredura não desce para subdiretórios. O diretório analisado precisa estar dentro de um dos diretórios-base configurados. Arquivos fora dessas bases são recusados.

Reanalise arquivos mesmo quando o hash não mudou:

```bash
yadocinfo scan ~/Documentos --force
```

Pesquise por palavra ou trecho no nome, assunto, descrição, palavras-chave e texto extraído:

```bash
yadocinfo search "aquisição de equipamentos"
yadocinfo search fornecedor --limit 20
```

Verifique os hashes dos documentos já catalogados:

```bash
yadocinfo verify
```

Exiba a configuração efetiva:

```bash
yadocinfo config
```

## Banco de dados

O padrão é SQLite. Para MariaDB ou PostgreSQL, instale o extra correspondente e ajuste `database.driver` e as credenciais no YAML. O SQLAlchemy usa a mesma estrutura de tabelas nos três bancos.

O instalador executa `metadata.create_all()`: cria as tabelas ausentes, mas não apaga nem migra tabelas existentes. Mudanças futuras de esquema deverão ser tratadas por migrações explícitas.

## Estado da implementação 0.1.0

Esta versão fornece a estrutura funcional inicial: instalação, configuração, conexão aos três bancos, varredura não recursiva, hashes, extração dos formatos listados e interpretação pelo endpoint compatível com a API de chat do Ollama. O modo `vision` envia imagens de páginas PDF ao modelo; `auto` usa visão quando o PDF não contém texto extraível.

A pesquisa textual básica já está disponível pelo comando `search`. A pesquisa semântica/vetorial, interface gráfica, suporte a arquivos DOC/XLS legados e migrações automáticas de banco ficam para versões futuras. A descrição textual e os metadados ficam armazenados em SQLite/MariaDB/PostgreSQL e também podem ser consultados por SQL.

## Licença

MIT.
