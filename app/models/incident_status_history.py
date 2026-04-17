from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class IncidentStatusHistory(Base):
    __tablename__ = "historial_estados_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    incident_status_id: Mapped[int] = mapped_column(
        "estado_incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.estados_incidente.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        "usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    observation: Mapped[str | None] = mapped_column("observacion", String(255))
    changed_at: Mapped[str] = mapped_column(
        "fecha_cambio", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    incident = relationship("Incident", back_populates="status_history")
    incident_status = relationship("IncidentStatus")
    user = relationship("User")
