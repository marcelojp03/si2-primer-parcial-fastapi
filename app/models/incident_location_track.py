from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class IncidentLocationTrack(Base):
    __tablename__ = "seguimiento_ubicacion_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column("latitud", Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column("longitud", Numeric(9, 6), nullable=False)
    recorded_at: Mapped[str] = mapped_column(
        "registrado_en", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    incident = relationship("Incident", back_populates="location_tracks")
