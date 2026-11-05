"""Extração de texto, metadados e imagens de páginas PDF."""

import base64

import fitz

from yadocinfo.extractors.base import BaseExtractor, ExtractionResult


class PDFExtractor(BaseExtractor):
    """Extrai texto de PDFs e renderiza páginas para OCR/visão quando necessário."""

    extensions = (".pdf",)

    def extract(self, path, config: dict) -> ExtractionResult:
        """Lê texto nativo e, conforme o modo, renderiza páginas como imagens PNG."""
        result = ExtractionResult(document_type="PDF")
        mode = config["ai"].get("input_mode", "auto")
        max_pages = int(config["ai"].get("max_pages", 8))
        with fitz.open(path) as pdf:
            result.metadata = {
                "pages": pdf.page_count,
                "title": pdf.metadata.get("title") or "",
                "author": pdf.metadata.get("author") or "",
                "subject": pdf.metadata.get("subject") or "",
            }
            pages_text = [page.get_text("text").strip() for page in pdf]
            result.text = "\n\n".join(f"[Página {i + 1}]\n{value}" for i, value in enumerate(pages_text) if value)
            need_images = mode == "vision" or (mode == "auto" and not result.text.strip())
            if need_images:
                for page in list(pdf)[:max_pages]:
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    result.images.append(base64.b64encode(pix.tobytes("png")).decode("ascii"))
        if not result.text and not result.images and config["processing"].get("ocr_enabled"):
            result.text = self._ocr(path, config["processing"].get("ocr_language", "por"))
        return result

    @staticmethod
    def _ocr(path, language: str) -> str:
        """Executa Tesseract opcional nas páginas do PDF e retorna texto reconhecido."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("OCR solicitado: instale yadocinfo[ocr] e o Tesseract.") from exc
        chunks = []
        with fitz.open(path) as pdf:
            for number, page in enumerate(pdf):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                chunks.append(f"[Página {number + 1}]\n{pytesseract.image_to_string(image, lang=language)}")
        return "\n\n".join(chunks)
