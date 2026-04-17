from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class TechnicianSpecialty(Base):
    __tablename__ = "tecnico_especialidades"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    technician_id: Mapped[int] = mapped_column(
        "tecnico_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.tecnicos.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    specialty_id: Mapped[int] = mapped_column(
        "especialidad_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.especialidades.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    technician = relationship("Technician", back_populates="specialties")
    specialty = relationship("Specialty")
