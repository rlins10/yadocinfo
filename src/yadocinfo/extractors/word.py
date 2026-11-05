"""Extração de parágrafos e tabelas de documentos DOCX."""

from docx import Document as WordDocument

from yadocinfo.extractors.base import BaseExtractor, ExtractionResult


class WordExtractor(BaseExtractor):
    """Extrai parágrafos e tabelas de arquivos DOCX mantendo a ordem básica."""

    extensions = (".docx",)

    def extract(self, path, config: dict) -> ExtractionResult:
        """Lê texto de parágrafos e células de tabelas do documento."""
        doc = WordDocument(path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for index, table in enumerate(doc.tables, start=1):
            rows = [" | ".join(cell.text.replace("\n", " ").strip() for cell in row.cells) for row in table.rows]
            parts.append(f"[Tabela {index}]\n" + "\n".join(rows))
        return ExtractionResult(text="\n".join(parts), document_type="Documento Word",
                                metadata={"paragraphs": len(doc.paragraphs), "tables": len(doc.tables)})
