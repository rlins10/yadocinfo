"""Contrato para provedores de interpretação de documentos."""

from dataclasses import dataclass


@dataclass
class Interpretation:
    """Descrição estruturada retornada pelo modelo."""

    subject: str = ""
    description: str = ""
    keywords: list[str] | None = None
    document_type: str = ""
    entities: list[str] | None = None
    dates: list[str] | None = None


class AIProvider:
    """Interface comum para provedores de IA."""

    def interpret(self, text: str, images: list[str], metadata: dict, config: dict) -> Interpretation:
        """Interpreta o conteúdo e retorna campos padronizados."""
        raise NotImplementedError
