from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Notification(Base):
    __tablename__ = "notificaciones"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        "usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    incident_id: Mapped[int | None] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    notification_type: Mapped[str] = mapped_column(
        "tipo_notificacion", String(50), nullable=False
    )
    channel: Mapped[str] = mapped_column("canal", String(30), nullable=False)
    title: Mapped[str] = mapped_column("titulo", String(150), nullable=False)
    message: Mapped[str] = mapped_column("mensaje", String(255), nullable=False)
    extra_data_json: Mapped[str | None] = mapped_column("datos_adicionales_json", Text)
    status: Mapped[str] = mapped_column(
        "estado", String(30), nullable=False, server_default="PENDIENTE"
    )
    sent_at: Mapped[str | None] = mapped_column("fecha_envio", DateTime)
    read_at: Mapped[str | None] = mapped_column("fecha_lectura", DateTime)
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    user = relationship("User")
    incident = relationship("Incident")
