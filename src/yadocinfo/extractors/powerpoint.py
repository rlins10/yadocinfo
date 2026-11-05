"""Extração de títulos, textos e tabelas de apresentações PPTX."""

from pptx import Presentation

from yadocinfo.extractors.base import BaseExtractor, ExtractionResult


class PowerPointExtractor(BaseExtractor):
    """Extrai texto e tabelas de cada slide de uma apresentação PPTX."""

    extensions = (".pptx",)

    def extract(self, path, config: dict) -> ExtractionResult:
        """Percorre slides e formas e reúne os elementos textuais."""
        presentation = Presentation(path)
        chunks = []
        for number, slide in enumerate(presentation.slides, start=1):
            chunks.append(f"[Slide {number}]")
            for shape in slide.shapes:
                if getattr(shape, "has_text_frame", False) and shape.text.strip():
                    chunks.append(shape.text.strip())
                if getattr(shape, "has_table", False):
                    for row in shape.table.rows:
                        chunks.append(" | ".join(cell.text.strip() for cell in row.cells))
        return ExtractionResult(text="\n".join(chunks), document_type="Apresentação PowerPoint",
                                metadata={"slides": len(presentation.slides)})
