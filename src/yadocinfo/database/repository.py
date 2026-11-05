"""Operações de consulta e atualização dos registros do catálogo."""

import json
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from yadocinfo.database.models import Document, DocumentRoot


class CatalogRepository:
    """Encapsula as operações SQL usadas pelos serviços de catalogação."""

    def __init__(self, session: Session):
        """Recebe uma sessão SQLAlchemy já aberta."""
        self.session = session

    def get_or_create_root(self, name: str, path: str) -> DocumentRoot:
        """Localiza um diretório-base pelo nome ou o cria/atualiza."""
        root = self.session.scalar(select(DocumentRoot).where(DocumentRoot.name == name))
        if root is None:
            root = DocumentRoot(name=name, path=path)
            self.session.add(root)
            self.session.flush()
        else:
            root.path = path
        return root

    def find_document(self, root_id: int, relative_path: str, filename: str) -> Document | None:
        """Localiza um documento pela sua localização lógica dentro da base."""
        return self.session.scalar(select(Document).where(
            Document.root_id == root_id,
            Document.relative_path == relative_path,
            Document.filename == filename,
        ))

    def save_document(self, values: dict) -> Document:
        """Insere ou atualiza um documento e serializa seus metadados em JSON."""
        document = self.find_document(values["root_id"], values["relative_path"], values["filename"])
        if document is None:
            document = Document(**values)
            self.session.add(document)
        else:
            for key, value in values.items():
                setattr(document, key, value)
            document.indexed_at = datetime.now(timezone.utc)
        self.session.flush()
        return document

    def all_documents(self) -> list[Document]:
        """Retorna os documentos catalogados para verificação de integridade."""
        return list(self.session.scalars(select(Document).order_by(Document.id)))


    def search_documents(self, term: str, limit: int = 50) -> list[Document]:
        """Pesquisa trecho textual em nome, assunto, descrição, palavras-chave e texto extraído."""
        pattern = f"%{term.strip()}%"
        statement = select(Document).where(or_(
            Document.filename.ilike(pattern),
            Document.subject.ilike(pattern),
            Document.description.ilike(pattern),
            Document.keywords.ilike(pattern),
            Document.extracted_text.ilike(pattern),
        )).order_by(Document.id).limit(limit)
        return list(self.session.scalars(statement))
