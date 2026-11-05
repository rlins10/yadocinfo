"""Orquestra extração, interpretação por IA e persistência do catálogo."""

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from yadocinfo.ai.interpreter import get_provider
from yadocinfo.database.repository import CatalogRepository
from yadocinfo.extractors.excel import ExcelExtractor
from yadocinfo.extractors.pdf import PDFExtractor
from yadocinfo.extractors.powerpoint import PowerPointExtractor
from yadocinfo.extractors.text import TextExtractor
from yadocinfo.extractors.word import WordExtractor
from yadocinfo.services.checksum import calculate_checksum

EXTRACTORS = {
    extension: extractor()
    for extractor in (PDFExtractor, WordExtractor, ExcelExtractor, PowerPointExtractor, TextExtractor)
    for extension in extractor.extensions
}


class CatalogService:
    """Processa arquivos e mantém os metadados e descrições no banco de dados."""

    def __init__(self, session: Session, config: dict):
        """Recebe sessão e configuração e prepara repositório e provedor de IA."""
        self.session = session
        self.config = config
        self.repository = CatalogRepository(session)
        self.provider = get_provider(config)

    def process_file(self, path: Path, root_name: str, root_path: Path, relative_dir: str, force: bool = False) -> str:
        """Verifica hash, extrai conteúdo, interpreta e insere ou atualiza o registro."""
        algorithm = self.config["integrity"].get("algorithm", "sha256")
        checksum = calculate_checksum(path, algorithm)
        relative_path = "" if relative_dir in {"", "."} else relative_dir
        root = self.repository.get_or_create_root(root_name, str(root_path))
        existing = self.repository.find_document(root.id, relative_path, path.name)
        if existing and existing.checksum == checksum and not force:
            return "inalterado"

        extractor = EXTRACTORS.get(path.suffix.lower())
        if extractor is None:
            return "formato não suportado"
        extracted = extractor.extract(path, self.config)
        max_chars = int(self.config["ai"].get("max_chars", 24000))
        interpretation = self.provider.interpret(extracted.text[:max_chars], extracted.images, extracted.metadata, self.config)
        stat = path.stat()
        values = {
            "root_id": root.id,
            "relative_path": relative_path,
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc),
            "checksum_algorithm": algorithm,
            "checksum": checksum,
            "document_type": interpretation.document_type or extracted.document_type,
            "subject": interpretation.subject,
            "description": interpretation.description,
            "keywords": ", ".join(interpretation.keywords or []),
            "extracted_text": extracted.text[:max_chars],
            "metadata_json": json.dumps({
                **extracted.metadata,
                "entities": interpretation.entities or [],
                "dates": interpretation.dates or [],
            }, ensure_ascii=False),
            "model_name": self.config["ai"].get("model", ""),
        }
        self.repository.save_document(values)
        self.session.commit()
        return "catalogado"
