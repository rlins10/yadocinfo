"""Descoberta não recursiva de arquivos dentro dos diretórios-base configurados."""

from pathlib import Path

from yadocinfo.config import expand_path


class Scanner:
    """Valida o diretório solicitado e enumera apenas seus arquivos imediatos."""

    def __init__(self, config: dict):
        """Prepara a lista de diretórios-base declarados no YAML."""
        self.roots = [
            (item["name"], expand_path(item["path"]))
            for item in config.get("directories", [])
        ]
        self.include_hidden = bool(config.get("processing", {}).get("include_hidden", False))

    def resolve_directory(self, requested: str) -> tuple[str, Path, str]:
        """Resolve diretório sob uma base e retorna nome da base, base e caminho relativo."""
        target = expand_path(requested)
        if not target.is_dir():
            raise ValueError(f"Diretório não encontrado: {target}")
        for name, root in self.roots:
            try:
                relative = target.relative_to(root)
                return name, root, relative.as_posix()
            except ValueError:
                continue
        raise ValueError(f"O diretório {target} não pertence a nenhuma base configurada.")

    def files(self, directory: Path):
        """Retorna arquivos regulares do primeiro nível, sem seguir subdiretórios."""
        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue
            if not self.include_hidden and path.name.startswith("."):
                continue
            yield path
