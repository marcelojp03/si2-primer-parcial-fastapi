from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class WorkshopSchedule(Base):
    __tablename__ = "horarios_taller"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        "taller_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.talleres.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    weekday: Mapped[str] = mapped_column("dia_semana", String(20), nullable=False)
    start_time = mapped_column("hora_inicio", Time, nullable=False)
    end_time = mapped_column("hora_fin", Time, nullable=False)
    active: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, server_default="true")
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    workshop = relationship("Workshop", back_populates="schedules")
