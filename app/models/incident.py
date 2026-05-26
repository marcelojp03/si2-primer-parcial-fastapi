from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Incident(Base):
    __tablename__ = "incidentes"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_user_id: Mapped[int] = mapped_column(
        "cliente_usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[int] = mapped_column(
        "vehiculo_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.vehiculos.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    incident_type_id: Mapped[int | None] = mapped_column(
        "tipo_incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.tipos_incidente.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    incident_status_id: Mapped[int] = mapped_column(
        "estado_incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.estados_incidente.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    client_uuid: Mapped[str | None] = mapped_column(
        "uuid_cliente", UUID(as_uuid=False), unique=True, nullable=True
    )
    title: Mapped[str] = mapped_column("titulo", String(150), nullable=False)
    description_text: Mapped[str | None] = mapped_column("descripcion_texto", Text)
    reference_address: Mapped[str | None] = mapped_column("direccion_referencia", String(255))
    latitude: Mapped[float | None] = mapped_column("latitud", Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column("longitud", Numeric(9, 6))
    priority_level: Mapped[str | None] = mapped_column("nivel_prioridad", String(20))
    requires_tow: Mapped[bool] = mapped_column(
        "requiere_remolque", Boolean, nullable=False, server_default="false"
    )
    requested_at: Mapped[str] = mapped_column(
        "fecha_solicitud", DateTime, nullable=False, server_default=func.now()
    )
    accepted_at: Mapped[str | None] = mapped_column("fecha_aceptacion", DateTime)
    started_at: Mapped[str | None] = mapped_column("fecha_inicio_atencion", DateTime)
    finished_at: Mapped[str | None] = mapped_column("fecha_finalizacion", DateTime)
    cancelled_at: Mapped[str | None] = mapped_column("fecha_cancelacion", DateTime)
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    client_user = relationship("User", back_populates="incidents")
    vehicle = relationship("Vehicle", back_populates="incidents")
    incident_type = relationship("IncidentType")
    incident_status = relationship("IncidentStatus")
    evidences = relationship(
        "IncidentEvidence", back_populates="incident", cascade="all, delete-orphan"
    )
    ai_analysis = relationship("IncidentAiAnalysis", back_populates="incident", uselist=False)
    status_history = relationship(
        "IncidentStatusHistory", back_populates="incident", cascade="all, delete-orphan"
    )
    workshop_candidates = relationship(
        "WorkshopCandidate", back_populates="incident", cascade="all, delete-orphan"
    )
    location_tracks = relationship(
        "IncidentLocationTrack", back_populates="incident", cascade="all, delete-orphan"
    )
    assignment = relationship("ServiceAssignment", back_populates="incident", uselist=False)
