from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class ServiceAssignment(Base):
    __tablename__ = "asignaciones_servicio"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    workshop_id: Mapped[int] = mapped_column(
        "taller_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.talleres.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    technician_id: Mapped[int | None] = mapped_column(
        "tecnico_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.tecnicos.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    specialty_id: Mapped[int | None] = mapped_column(
        "especialidad_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.especialidades.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        "usuario_asignador_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    performed_service_description: Mapped[str | None] = mapped_column(
        "descripcion_servicio_realizado", Text
    )
    distance_km: Mapped[float | None] = mapped_column("distancia_km", Numeric(10, 2))
    estimated_arrival_minutes: Mapped[int | None] = mapped_column(
        "tiempo_estimado_llegada_min", Integer
    )
    estimated_cost: Mapped[float | None] = mapped_column("costo_estimado", Numeric(10, 2))
    final_cost: Mapped[float | None] = mapped_column("costo_final", Numeric(10, 2))
    assignment_status: Mapped[str] = mapped_column(
        "estado_asignacion", String(30), nullable=False, server_default="ASIGNADO"
    )
    final_notes: Mapped[str | None] = mapped_column("observaciones_finales", Text)
    assigned_at: Mapped[str] = mapped_column(
        "fecha_asignacion", DateTime, nullable=False, server_default=func.now()
    )
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    incident = relationship("Incident", back_populates="assignment")
    workshop = relationship("Workshop")
    technician = relationship("Technician")
    specialty = relationship("Specialty")
    assigned_by_user = relationship("User")
    payment = relationship("Payment", back_populates="assignment", uselist=False)
    rating = relationship("Rating", back_populates="assignment", uselist=False)
