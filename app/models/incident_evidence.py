from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class IncidentEvidence(Base):
    __tablename__ = "evidencias_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column("tipo_evidencia", String(20), nullable=False)
    file_url: Mapped[str | None] = mapped_column("url_archivo", String(255))
    file_key: Mapped[str | None] = mapped_column("clave_archivo", String(255))
    mime_type: Mapped[str | None] = mapped_column("tipo_mime", String(100))
    file_name: Mapped[str | None] = mapped_column("nombre_archivo", String(150))
    file_size: Mapped[int | None] = mapped_column("tamano_archivo", BigInteger)
    uploaded_at: Mapped[str] = mapped_column(
        "fecha_carga", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    incident = relationship("Incident", back_populates="evidences")
