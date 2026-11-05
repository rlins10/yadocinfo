"""Cálculo de hash criptográfico para verificar identidade e alterações em arquivos."""

import hashlib
from pathlib import Path


def calculate_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Calcula SHA-256 ou MD5 em blocos, sem carregar o arquivo inteiro na memória."""
    if algorithm not in {"sha256", "md5"}:
        raise ValueError("Algoritmo permitido: sha256 ou md5.")
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
