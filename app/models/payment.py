from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class Payment(Base):
    __tablename__ = "pagos"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service_assignment_id: Mapped[int] = mapped_column(
        "asignacion_servicio_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.asignaciones_servicio.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    client_user_id: Mapped[int] = mapped_column(
        "cliente_usuario_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column("monto", Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        "moneda", String(10), nullable=False, server_default="BOB"
    )
    payment_method: Mapped[str] = mapped_column("metodo_pago", String(30), nullable=False)
    payment_provider: Mapped[str | None] = mapped_column("proveedor_pago", String(50))
    external_reference: Mapped[str | None] = mapped_column("referencia_externa", String(150))
    payment_status: Mapped[str] = mapped_column(
        "estado_pago", String(30), nullable=False, server_default="PENDIENTE"
    )
    paid_at: Mapped[str | None] = mapped_column("fecha_pago", DateTime)
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    assignment = relationship("ServiceAssignment", back_populates="payment")
    client_user = relationship("User")
