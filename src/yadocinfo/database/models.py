"""Modelos SQLAlchemy que representam diretórios-base e documentos catalogados."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe-base declarativa do SQLAlchemy."""


class DocumentRoot(Base):
    """Diretório-base configurado, identificado por nome e caminho atual."""

    __tablename__ = "document_roots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    documents: Mapped[list["Document"]] = relationship(back_populates="root")


class Document(Base):
    """Registro de um arquivo, sem armazenar nem modificar seu conteúdo original."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("root_id", "relative_path", "filename", name="uq_document_location"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    root_id: Mapped[int] = mapped_column(ForeignKey("document_roots.id"), nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, default="", nullable=False)
    filename: Mapped[str] = mapped_column(String(1024), nullable=False)
    extension: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checksum_algorithm: Mapped[str] = mapped_column(String(16), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    document_type: Mapped[str] = mapped_column(String(120), default="unknown", nullable=False)
    subject: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    keywords: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    root: Mapped[DocumentRoot] = relationship(back_populates="documents")
