"""Criação do engine SQLAlchemy a partir da configuração do yadocinfo."""

from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

from yadocinfo.config import expand_path


def build_engine(config: dict) -> Engine:
    """Cria um engine SQLite, MariaDB ou PostgreSQL conforme o YAML."""
    db = config["database"]
    driver = db["driver"]
    if driver == "sqlite":
        path = expand_path(db.get("sqlite_path", "~/.config/yadocinfo/yadocinfo.db"))
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{path}"
        return create_engine(url, future=True)
    section = db[driver]
    username = quote_plus(str(section["username"]))
    password = quote_plus(str(section.get("password", "")))
    host = section.get("host", "localhost")
    port = int(section.get("port", 3306 if driver == "mariadb" else 5432))
    database = section["database"]
    if driver == "mariadb":
        url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    else:
        url = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
    return create_engine(url, pool_pre_ping=True, future=True)


def ensure_database(config: dict) -> None:
    """Cria o banco MariaDB/PostgreSQL se ainda não existir. SQLite é criado sob demanda."""
    db = config["database"]
    driver = db["driver"]
    if driver == "sqlite":
        return
    section = db[driver]
    username = str(section["username"])
    password = str(section.get("password", ""))
    host = section.get("host", "localhost")
    port = int(section.get("port", 3306 if driver == "mariadb" else 5432))
    database = str(section["database"])
    if not database.replace("_", "").isalnum():
        raise ValueError("Nome do banco inválido; use somente letras, números e underscore.")
    if driver == "mariadb":
        admin_url = URL.create("mysql+pymysql", username=username, password=password, host=host, port=port)
        engine = create_engine(admin_url, future=True)
        try:
            with engine.begin() as connection:
                connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        finally:
            engine.dispose()
        return
    admin_url = URL.create("postgresql+psycopg", username=username, password=password, host=host, port=port, database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)
    try:
        with engine.connect() as connection:
            exists = connection.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database}).scalar()
            if not exists:
                quoted = connection.dialect.identifier_preparer.quote(database)
                connection.exec_driver_sql(f"CREATE DATABASE {quoted}")
    finally:
        engine.dispose()
