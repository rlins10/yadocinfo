"""Assistente interativo para criar a configuração inicial e as tabelas."""

from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import text

from yadocinfo.config import APP_DIR, CONFIG_PATH, DEFAULT_CONFIG, write_config
from yadocinfo.database.connection import build_engine, ensure_database
from yadocinfo.database.models import Base


def _ask(prompt: str, default: str = "") -> str:
    """Solicita texto ao usuário, aceitando o valor padrão com Enter."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def run_installer() -> None:
    """Coleta parâmetros, grava YAML, testa conexão e cria tabelas."""
    print("yadocinfo — configuração inicial")
    config = {
        "database": DEFAULT_CONFIG["database"].copy(),
        "directories": [],
        "integrity": DEFAULT_CONFIG["integrity"].copy(),
        "ai": DEFAULT_CONFIG["ai"].copy(),
        "processing": DEFAULT_CONFIG["processing"].copy(),
    }
    print("\nBanco de dados: 1) SQLite  2) MariaDB  3) PostgreSQL")
    choice = _ask("Escolha", "1")
    driver = {"1": "sqlite", "2": "mariadb", "3": "postgresql"}.get(choice)
    if not driver:
        raise ValueError("Opção de banco inválida.")
    config["database"]["driver"] = driver
    if driver == "sqlite":
        config["database"]["sqlite_path"] = _ask("Arquivo SQLite", "~/.config/yadocinfo/yadocinfo.db")
    else:
        section = config["database"][driver]
        default_port = "3306" if driver == "mariadb" else "5432"
        section["host"] = _ask("Servidor", "localhost")
        section["port"] = int(_ask("Porta", default_port))
        section["database"] = _ask("Nome do banco", "yadocinfo")
        section["username"] = _ask("Usuário", "yadocinfo")
        section["password"] = _ask("Senha")
    print("\nDiretórios-base. Informe pelo menos um caminho.")
    index = 1
    while True:
        path = _ask(f"Diretório-base {index} (Enter para terminar)", str(Path.home() / "Documentos") if index == 1 else "")
        if not path:
            break
        expanded = Path(path).expanduser().resolve()
        if not expanded.is_dir():
            print(f"Diretório inexistente: {expanded}")
            continue
        name = _ask("Nome lógico da base", f"base{index}")
        config["directories"].append({"name": name, "path": str(expanded)})
        index += 1
    if not config["directories"]:
        raise ValueError("É necessário configurar pelo menos um diretório-base.")
    print("\nModelo de IA")
    config["ai"]["provider"] = "ollama"
    config["ai"]["endpoint"] = _ask("Endpoint Ollama", "http://localhost:11434")
    config["ai"]["model"] = _ask("Modelo", "gemma4:12b")
    config["ai"]["input_mode"] = _ask("Modo (text/vision/auto)", "auto").lower()
    config["integrity"]["algorithm"] = _ask("Hash (sha256/md5)", "sha256").lower()
    config["processing"]["ocr_enabled"] = _ask("Ativar OCR Tesseract? (s/N)", "N").lower() == "s"
    APP_DIR.mkdir(parents=True, exist_ok=True)
    write_config(config)
    ensure_database(config)
    engine = build_engine(config)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.execute(text("SELECT 1"))
    print(f"\nConfiguração gravada em: {CONFIG_PATH}")
    print("Conexão testada e tabelas criadas/verificadas.")
