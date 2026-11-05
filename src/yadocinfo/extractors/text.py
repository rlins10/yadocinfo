"""Extração de arquivos de texto, CSV, HTML e RTF."""

from bs4 import BeautifulSoup

from yadocinfo.extractors.base import BaseExtractor, ExtractionResult


class TextExtractor(BaseExtractor):
    """Extrai texto de arquivos simples e formatos textuais comuns."""

    extensions = (".txt", ".md", ".csv", ".html", ".htm", ".rtf", ".log")

    def extract(self, path, config: dict) -> ExtractionResult:
        """Lê o arquivo e remove marcação HTML/RTF básica quando aplicável."""
        suffix = path.suffix.lower()
        raw = path.read_text(encoding="utf-8", errors="replace")
        if suffix in {".html", ".htm"}:
            raw = BeautifulSoup(raw, "html.parser").get_text("\n", strip=True)
        elif suffix == ".rtf":
            import re
            raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
            raw = re.sub(r"[{}]", " ", raw)
        return ExtractionResult(text=raw, document_type={
            ".csv": "CSV", ".html": "HTML", ".htm": "HTML", ".rtf": "RTF"
        }.get(suffix, "Texto"))
