"""Carregamento, validação e caminhos da configuração YAML do yadocinfo."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

APP_DIR = Path.home() / ".config" / "yadocinfo"
CONFIG_PATH = APP_DIR / "config.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "driver": "sqlite",
        "sqlite_path": "~/.config/yadocinfo/yadocinfo.db",
        "mariadb": {"host": "localhost", "port": 3306, "database": "yadocinfo", "username": "yadocinfo", "password": ""},
        "postgresql": {"host": "localhost", "port": 5432, "database": "yadocinfo", "username": "yadocinfo", "password": ""},
    },
    "directories": [],
    "integrity": {"algorithm": "sha256"},
    "ai": {
        "provider": "ollama", "endpoint": "http://localhost:11434",
        "model": "gemma4:12b", "input_mode": "auto", "max_pages": 8,
        "max_chars": 24000, "timeout": 300, "temperature": 0.1,
    },
    "processing": {"ocr_enabled": False, "ocr_language": "por", "include_hidden": False},
}


class ConfigurationError(ValueError):
    """Erro de configuração ausente, inválida ou incompatível."""


def expand_path(value: str) -> Path:
    """Expande ~ e variáveis de ambiente e retorna um caminho absoluto."""
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Carrega o YAML, valida os campos essenciais e retorna a configuração."""
    if not path.is_file():
        raise ConfigurationError(f"Configuração não encontrada: {path}. Execute 'yadocinfo init'.")
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if not isinstance(data, dict):
        raise ConfigurationError("A raiz do YAML precisa ser um mapa.")
    for key, default in DEFAULT_CONFIG.items():
        data.setdefault(key, default.copy() if isinstance(default, dict) else default)
    driver = data["database"].get("driver", "sqlite").lower()
    if driver not in {"sqlite", "mariadb", "postgresql"}:
        raise ConfigurationError("database.driver deve ser sqlite, mariadb ou postgresql.")
    data["database"]["driver"] = driver
    algorithm = data["integrity"].get("algorithm", "sha256").lower()
    if algorithm not in {"sha256", "md5"}:
        raise ConfigurationError("integrity.algorithm deve ser sha256 ou md5.")
    data["integrity"]["algorithm"] = algorithm
    if data["ai"].get("provider", "ollama") != "ollama":
        raise ConfigurationError("Nesta versão, somente ai.provider=ollama está implementado.")
    if data["ai"].get("input_mode", "auto") not in {"text", "vision", "auto"}:
        raise ConfigurationError("ai.input_mode deve ser text, vision ou auto.")
    if not isinstance(data["directories"], list):
        raise ConfigurationError("directories precisa ser uma lista.")
    for item in data["directories"]:
        if not isinstance(item, dict) or not item.get("name") or not item.get("path"):
            raise ConfigurationError("Cada diretório-base precisa de name e path.")
    return data


def write_config(data: dict[str, Any], path: Path = CONFIG_PATH) -> None:
    """Grava a configuração YAML e restringe as permissões do arquivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
    path.chmod(0o600)
