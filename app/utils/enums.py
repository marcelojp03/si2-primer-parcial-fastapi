import enum


class UserRole(enum.StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN_TALLER = "admin_taller"
    TECNICO = "tecnico"
    CLIENTE = "cliente"


class UserStatus(enum.StrEnum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


class Weekday(enum.StrEnum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"


class PriorityLevel(enum.StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EvidenceType(enum.StrEnum):
    FOTO = "foto"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENTO = "documento"


class CandidateResponseStatus(enum.StrEnum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"
    EXPIRADO = "expirado"


class AssignmentStatus(enum.StrEnum):
    ASIGNADO = "asignado"
    EN_CAMINO = "en_camino"
    EN_SITIO = "en_sitio"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


class PaymentMethod(enum.StrEnum):
    EFECTIVO = "efectivo"
    QR = "qr"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"


class PaymentStatus(enum.StrEnum):
    PENDIENTE = "pendiente"
    COMPLETADO = "completado"
    FALLIDO = "fallido"
    REEMBOLSADO = "reembolsado"


class NotificationChannel(enum.StrEnum):
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationStatus(enum.StrEnum):
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    LEIDO = "leido"
    FALLIDO = "fallido"


class TechnicianAvailability(enum.StrEnum):
    DISPONIBLE = "disponible"
    OCUPADO = "ocupado"
    NO_DISPONIBLE = "no_disponible"


class GeneralStatus(enum.StrEnum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
