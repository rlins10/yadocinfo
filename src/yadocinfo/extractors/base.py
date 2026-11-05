"""Tipos e contrato comum para extratores de documentos."""

from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    """Conteúdo extraído de um arquivo, incluindo imagens opcionais para visão."""

    text: str = ""
    images: list[str] = field(default_factory=list)
    document_type: str = "Documento"
    metadata: dict = field(default_factory=dict)


class BaseExtractor:
    """Contrato que deve ser implementado por cada extrator de formato."""

    extensions: tuple[str, ...] = ()

    def extract(self, path, config: dict) -> ExtractionResult:
        """Extrai conteúdo do arquivo; subclasses devem implementar este método."""
        raise NotImplementedError
