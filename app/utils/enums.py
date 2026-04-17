import enum


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN_TALLER = "admin_taller"
    CLIENTE = "cliente"


class UserStatus(str, enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


class Weekday(str, enum.Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"


class PriorityLevel(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EvidenceType(str, enum.Enum):
    FOTO = "foto"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENTO = "documento"


class CandidateResponseStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"


class AssignmentStatus(str, enum.Enum):
    ASIGNADO = "asignado"
    EN_CAMINO = "en_camino"
    EN_SITIO = "en_sitio"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


class PaymentMethod(str, enum.Enum):
    EFECTIVO = "efectivo"
    QR = "qr"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"


class PaymentStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    COMPLETADO = "completado"
    FALLIDO = "fallido"
    REEMBOLSADO = "reembolsado"


class NotificationChannel(str, enum.Enum):
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    LEIDO = "leido"
    FALLIDO = "fallido"


class TechnicianAvailability(str, enum.Enum):
    DISPONIBLE = "disponible"
    OCUPADO = "ocupado"
    NO_DISPONIBLE = "no_disponible"


class GeneralStatus(str, enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
