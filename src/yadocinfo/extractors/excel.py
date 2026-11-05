"""Extração de planilhas XLSX com nomes de abas, dimensões e valores."""

from openpyxl import load_workbook

from yadocinfo.extractors.base import BaseExtractor, ExtractionResult


class ExcelExtractor(BaseExtractor):
    """Extrai valores e estrutura das abas de uma pasta de trabalho XLSX."""

    extensions = (".xlsx", ".xlsm")

    def extract(self, path, config: dict) -> ExtractionResult:
        """Converte cada aba em texto tabular, preservando nomes de linhas e colunas."""
        workbook = load_workbook(path, read_only=True, data_only=True)
        chunks = []
        sheets = []
        max_chars = int(config["ai"].get("max_chars", 24000))
        for sheet in workbook.worksheets:
            sheets.append({"name": sheet.title, "max_row": sheet.max_row, "max_column": sheet.max_column})
            chunks.append(f"[Planilha: {sheet.title}; {sheet.max_row} linhas x {sheet.max_column} colunas]")
            for row in sheet.iter_rows(values_only=True):
                values = ["" if value is None else str(value) for value in row]
                if any(values):
                    chunks.append(" | ".join(values))
                if sum(len(part) for part in chunks) >= max_chars:
                    chunks.append("[Conteúdo truncado pelo limite configurado]")
                    break
            if sum(len(part) for part in chunks) >= max_chars:
                break
        workbook.close()
        return ExtractionResult(text="\n".join(chunks)[:max_chars], document_type="Planilha Excel",
                                metadata={"sheets": sheets})
