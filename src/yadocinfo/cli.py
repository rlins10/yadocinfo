"""Interface de linha de comando do yadocinfo."""

from pathlib import Path

import typer
import yaml
from sqlalchemy.orm import Session

from yadocinfo import __version__
from yadocinfo.config import load_config
from yadocinfo.database.connection import build_engine
from yadocinfo.database.models import Base
from yadocinfo.database.repository import CatalogRepository
from yadocinfo.installer import run_installer
from yadocinfo.services.catalog import CatalogService
from yadocinfo.services.scanner import Scanner
from yadocinfo.services.checksum import calculate_checksum

app = typer.Typer(help="yadocinfo — Yet Another Document Information", no_args_is_help=True)


@app.command()
def version():
    """Exibe a versão instalada."""
    typer.echo(f"yadocinfo {__version__}")


@app.command()
def init():
    """Executa o instalador, grava o YAML e cria as tabelas."""
    run_installer()


@app.command()
def config():
    """Exibe o YAML de configuração."""
    data = load_config()
    typer.echo(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


@app.command()
def bases():
    """Lista os diretórios-base configurados."""
    data = load_config()
    for item in data["directories"]:
        typer.echo(f'{item["name"]}: {Path(item["path"]).expanduser()}')


@app.command()
def scan(directory: str = typer.Argument(..., help="Diretório a analisar; somente o primeiro nível."),
         force: bool = typer.Option(False, "--force", help="Reinterpreta arquivos mesmo com hash inalterado.")):
    """Cataloga os arquivos imediatos do diretório informado, sem recursão."""
    data = load_config()
    scanner = Scanner(data)
    root_name, root_path, relative = scanner.resolve_directory(directory)
    target = Path(directory).expanduser().resolve()
    engine = build_engine(data)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = CatalogService(session, data)
        count = 0
        for path in scanner.files(target):
            try:
                result = service.process_file(path, root_name, root_path, relative, force)
                typer.echo(f"[{result}] {path.name}")
                count += 1
            except Exception as exc:
                session.rollback()
                typer.echo(f"[ERRO] {path.name}: {exc}", err=True)
        typer.echo(f"Concluído: {count} arquivo(s) verificado(s).")


@app.command()
def search(term: str = typer.Argument(..., help="Palavra ou trecho a localizar no catálogo."),
          limit: int = typer.Option(50, "--limit", min=1, help="Quantidade máxima de resultados.")):
    """Pesquisa no nome, assunto, descrição, palavras-chave e texto extraído."""
    data = load_config()
    engine = build_engine(data)
    with Session(engine) as session:
        repository = CatalogRepository(session)
        results = repository.search_documents(term, limit)
        for document in results:
            location = Path(document.root.path) / document.relative_path / document.filename
            typer.echo(f"\n[{document.document_type}] {location}")
            if document.subject:
                typer.echo(f"Assunto: {document.subject}")
            if document.description:
                typer.echo(f"Descrição: {document.description}")
            if document.keywords:
                typer.echo(f"Palavras-chave: {document.keywords}")
        typer.echo(f"\n{len(results)} resultado(s).")


@app.command()
def verify():
    """Recalcula os hashes e informa arquivos ausentes ou modificados."""
    data = load_config()
    engine = build_engine(data)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = CatalogRepository(session)
        roots = {item["name"]: Path(item["path"]).expanduser().resolve() for item in data["directories"]}
        for document in repository.all_documents():
            root = roots.get(document.root.name)
            if root is None:
                typer.echo(f"[BASE AUSENTE] {document.root.name}: {document.filename}")
                continue
            path = root / document.relative_path / document.filename
            if not path.is_file():
                typer.echo(f"[AUSENTE] {path}")
                continue
            current = calculate_checksum(path, document.checksum_algorithm)
            if current != document.checksum:
                typer.echo(f"[ALTERADO] {path}")
            else:
                typer.echo(f"[OK] {path}")


if __name__ == "__main__":
    app()
