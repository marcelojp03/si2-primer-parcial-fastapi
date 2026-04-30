#!/usr/bin/env python3
"""
Seed de datos demo — Plataforma Auxilio Mecánico
Santa Cruz de la Sierra, Bolivia

Uso:
    cd si2-primer-parcial-fastapi
    .venv/Scripts/python.exe scripts/db/seed_demo.py

Credenciales de todos los usuarios demo:
    Contraseña: Auxilio2026!

Requisito previo: la app debe haberse ejecutado al menos una vez para que
  init_db cree los catálogos (especialidades, tipos_incidente, estados_incidente).
  Alternativa: python -c "import asyncio; from app.db.init_db import run_init_db; asyncio.run(run_init_db())"
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

# ── Locate project root (.env lives here) ────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]  # si2-primer-parcial-fastapi/


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


_load_dotenv(ROOT / ".env")

import asyncpg  # noqa: E402 — needs venv active

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/auxilio_mecanico",
)
DSN = re.sub(r"^postgresql\+asyncpg://", "postgresql://", DATABASE_URL)
S = "auxilio_mecanico"
DEMO_PASSWORD = "Auxilio2026!"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _t(hhmm: str) -> time:
    """'HH:MM' → datetime.time."""
    h, m = map(int, hhmm.split(":"))
    return time(h, m)


def _hash_password(password: str) -> str:
    import bcrypt as _bcrypt  # type: ignore[import-untyped]

    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


async def _upsert_user(
    conn: asyncpg.Connection,
    email: str,
    rol: str,
    nombre: str,
    ci: str,
    tel: str,
    pw_hash: str,
) -> int:
    existing = await conn.fetchval(
        f"SELECT id FROM {S}.usuarios WHERE correo_electronico = $1", email
    )
    if existing:
        return existing
    return await conn.fetchval(
        f"""INSERT INTO {S}.usuarios
                (rol, nombre_completo, ci, telefono, correo_electronico, contrasena_hash)
            VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
        rol,
        nombre,
        ci,
        tel,
        email,
        pw_hash,
    )


# ── Data ──────────────────────────────────────────────────────────────────────

SUPERADMIN = {
    "nombre": "Sistema Superadmin",
    "ci": "00000001",
    "tel": "78000000",
    "email": "superadmin@auxilio.bo",
}

# 12 talleres en Santa Cruz de la Sierra
# Coordenadas reales de barrios/zonas de la ciudad
WORKSHOPS = [
    {
        "admin": {
            "nombre": "Roberto Salvatierra Paz",
            "ci": "5521234",
            "tel": "77812345",
            "email": "admin.cruzdelsur@auxilio.bo",
        },
        "taller": {
            "nombre": "AutoService Cruz del Sur",
            "descripcion": "Taller mecánico integral con más de 15 años de experiencia en el centro",
            "telefono": "77812345",
            "email": "autoservice.cruzdelsur@gmail.com",
            "direccion": "Av. Cañoto #256 esq. Mercado, Centro, Santa Cruz",
            "latitud": -17.7880,
            "longitud": -63.1820,
            "tiene_remolque": True,
            "atiende_24_horas": True,
        },
        "especialidades": ["BATERIA", "MOTOR", "SUSPENSION", "REMOLQUE"],
        "horarios": [
            ("LUNES", _t("07:00"), _t("19:00")),
            ("MARTES", _t("07:00"), _t("19:00")),
            ("MIERCOLES", _t("07:00"), _t("19:00")),
            ("JUEVES", _t("07:00"), _t("19:00")),
            ("VIERNES", _t("07:00"), _t("19:00")),
            ("SABADO", _t("08:00"), _t("14:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Carlos Mamani Quispe",
                "ci": "5521001",
                "tel": "77100001",
                "especialidades": ["MOTOR", "SUSPENSION"],
            },
            {
                "nombre": "Luis Vargas Peña",
                "ci": "6312345",
                "tel": "77100002",
                "especialidades": ["BATERIA", "MOTOR"],
            },
            {
                "nombre": "Miguel Flores Zurita",
                "ci": "7143456",
                "tel": "77100003",
                "especialidades": ["REMOLQUE"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Héctor Quintanilla López",
            "ci": "6023450",
            "tel": "77823456",
            "email": "admin.losandes@auxilio.bo",
        },
        "taller": {
            "nombre": "Mecánica Los Andes",
            "descripcion": "Especialistas en llantas y suspensión. Zona Equipetrol Norte",
            "telefono": "77823456",
            "email": "mecanica.losandes@gmail.com",
            "direccion": "Av. San Martín 2do Anillo, Equipetrol Norte, Santa Cruz",
            "latitud": -17.7580,
            "longitud": -63.2012,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["LLANTAS", "SUSPENSION", "CERRAJERIA_VEHICULAR"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:00")),
            ("MARTES", _t("08:00"), _t("18:00")),
            ("MIERCOLES", _t("08:00"), _t("18:00")),
            ("JUEVES", _t("08:00"), _t("18:00")),
            ("VIERNES", _t("08:00"), _t("18:00")),
            ("SABADO", _t("08:00"), _t("13:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Rolando Caballero Vaca",
                "ci": "6023001",
                "tel": "77200001",
                "especialidades": ["LLANTAS", "SUSPENSION"],
            },
            {
                "nombre": "Fernando Pinto Roca",
                "ci": "7134512",
                "tel": "77200002",
                "especialidades": ["CERRAJERIA_VEHICULAR", "LLANTAS"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Alejandro Méndez Torrico",
            "ci": "7234567",
            "tel": "77834567",
            "email": "admin.elturbo@auxilio.bo",
        },
        "taller": {
            "nombre": "Taller El Turbo",
            "descripcion": "Mecánica general, batería y motor. Servicio rápido en Plan 3000",
            "telefono": "77834567",
            "email": "taller.elturbo@gmail.com",
            "direccion": "Av. Santos Dumont #123, Plan 3000, Santa Cruz",
            "latitud": -17.8215,
            "longitud": -63.1142,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["MOTOR", "BATERIA", "LLANTAS"],
        "horarios": [
            ("LUNES", _t("07:30"), _t("18:30")),
            ("MARTES", _t("07:30"), _t("18:30")),
            ("MIERCOLES", _t("07:30"), _t("18:30")),
            ("JUEVES", _t("07:30"), _t("18:30")),
            ("VIERNES", _t("07:30"), _t("18:30")),
            ("SABADO", _t("08:00"), _t("13:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Iván Gutiérrez Flores",
                "ci": "7234001",
                "tel": "77300001",
                "especialidades": ["MOTOR"],
            },
            {
                "nombre": "Jorge Aquino Paz",
                "ci": "8145001",
                "tel": "77300002",
                "especialidades": ["BATERIA", "MOTOR"],
            },
            {
                "nombre": "Víctor Sandoval Cruz",
                "ci": "9056001",
                "tel": "77300003",
                "especialidades": ["LLANTAS"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Patricia Ureña Castro",
            "ci": "8034560",
            "tel": "77845678",
            "email": "admin.barriolindo@auxilio.bo",
        },
        "taller": {
            "nombre": "Mecánica Barrio Lindo",
            "descripcion": "Batería y cerrajería vehicular al norte de la ciudad",
            "telefono": "77845678",
            "email": "mecanica.barriolindo@gmail.com",
            "direccion": "Av. Los Cusis, Barrio Lindo, Santa Cruz",
            "latitud": -17.7472,
            "longitud": -63.1835,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["BATERIA", "CERRAJERIA_VEHICULAR"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:00")),
            ("MARTES", _t("08:00"), _t("18:00")),
            ("MIERCOLES", _t("08:00"), _t("18:00")),
            ("JUEVES", _t("08:00"), _t("18:00")),
            ("VIERNES", _t("08:00"), _t("18:00")),
            ("SABADO", _t("08:00"), _t("17:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Ernesto Chávez Rojas",
                "ci": "8034001",
                "tel": "77400001",
                "especialidades": ["BATERIA"],
            },
            {
                "nombre": "Óscar Heredia Lima",
                "ci": "9045001",
                "tel": "77400002",
                "especialidades": ["CERRAJERIA_VEHICULAR", "BATERIA"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Marcelo Zeballos Nogales",
            "ci": "9145671",
            "tel": "77856789",
            "email": "admin.autorescate@auxilio.bo",
        },
        "taller": {
            "nombre": "AutoRescate 24h",
            "descripcion": "Asistencia vehicular las 24 horas con remolque. Av. Banzer",
            "telefono": "77856789",
            "email": "autorescate24h@gmail.com",
            "direccion": "Av. Banzer 3er Anillo Externo, Santa Cruz",
            "latitud": -17.7682,
            "longitud": -63.1978,
            "tiene_remolque": True,
            "atiende_24_horas": True,
        },
        "especialidades": ["REMOLQUE", "BATERIA", "MOTOR", "LLANTAS"],
        "horarios": [
            ("LUNES", _t("00:00"), _t("23:59")),
            ("MARTES", _t("00:00"), _t("23:59")),
            ("MIERCOLES", _t("00:00"), _t("23:59")),
            ("JUEVES", _t("00:00"), _t("23:59")),
            ("VIERNES", _t("00:00"), _t("23:59")),
            ("SABADO", _t("00:00"), _t("23:59")),
            ("DOMINGO", _t("00:00"), _t("23:59")),
        ],
        "tecnicos": [
            {
                "nombre": "Ramiro Flores Navia",
                "ci": "9145001",
                "tel": "77500001",
                "especialidades": ["REMOLQUE", "BATERIA"],
            },
            {
                "nombre": "Gustavo Montero Ibáñez",
                "ci": "0156001",
                "tel": "77500002",
                "especialidades": ["MOTOR", "LLANTAS"],
            },
            {
                "nombre": "Daniel Pedraza Valverde",
                "ci": "1067001",
                "tel": "77500003",
                "especialidades": ["REMOLQUE"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Silvia Antelo Morales",
            "ci": "0256782",
            "tel": "77867890",
            "email": "admin.villamayor@auxilio.bo",
        },
        "taller": {
            "nombre": "Taller Villa Mayor",
            "descripcion": "Motor y suspensión, zona Villa 1ro de Mayo",
            "telefono": "77867890",
            "email": "taller.villamayor@gmail.com",
            "direccion": "Av. Mutualista, Villa 1ro de Mayo, Santa Cruz",
            "latitud": -17.8358,
            "longitud": -63.1722,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["MOTOR", "SUSPENSION"],
        "horarios": [
            ("LUNES", _t("07:00"), _t("18:00")),
            ("MARTES", _t("07:00"), _t("18:00")),
            ("MIERCOLES", _t("07:00"), _t("18:00")),
            ("JUEVES", _t("07:00"), _t("18:00")),
            ("VIERNES", _t("07:00"), _t("18:00")),
            ("SABADO", _t("07:00"), _t("12:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Rodrigo Céspedes Barrientos",
                "ci": "0256001",
                "tel": "77600001",
                "especialidades": ["MOTOR", "SUSPENSION"],
            },
            {
                "nombre": "Javier Ribero Paredes",
                "ci": "1167001",
                "tel": "77600002",
                "especialidades": ["MOTOR"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Gonzalo Rivero Altamirano",
            "ci": "1367893",
            "tel": "77878901",
            "email": "admin.elcristo@auxilio.bo",
        },
        "taller": {
            "nombre": "Mecánica El Cristo Norte",
            "descripcion": "Batería, llantas y motor. Zona Cristo Norte",
            "telefono": "77878901",
            "email": "mecanica.elcristo@gmail.com",
            "direccion": "Av. Cristo Redentor, Zona Norte, Santa Cruz",
            "latitud": -17.7488,
            "longitud": -63.1982,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["BATERIA", "LLANTAS", "MOTOR"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:30")),
            ("MARTES", _t("08:00"), _t("18:30")),
            ("MIERCOLES", _t("08:00"), _t("18:30")),
            ("JUEVES", _t("08:00"), _t("18:30")),
            ("VIERNES", _t("08:00"), _t("18:30")),
        ],
        "tecnicos": [
            {
                "nombre": "Álvaro Soto Azcui",
                "ci": "1367001",
                "tel": "77700001",
                "especialidades": ["BATERIA", "LLANTAS"],
            },
            {
                "nombre": "Mauricio Durán Cuellar",
                "ci": "2478001",
                "tel": "77700002",
                "especialidades": ["MOTOR"],
            },
            {
                "nombre": "Sebastián Vargas Orellana",
                "ci": "3589001",
                "tel": "77700003",
                "especialidades": ["BATERIA"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Carmen Rosa Vaca Pedraza",
            "ci": "2478904",
            "tel": "77889012",
            "email": "admin.servauto@auxilio.bo",
        },
        "taller": {
            "nombre": "ServAuto Pampa",
            "descripcion": "Suspensión y remolque, zona Pampa de la Isla",
            "telefono": "77889012",
            "email": "servauto.pampa@gmail.com",
            "direccion": "Av. Beni #450, Pampa de la Isla, Santa Cruz",
            "latitud": -17.7548,
            "longitud": -63.1658,
            "tiene_remolque": True,
            "atiende_24_horas": False,
        },
        "especialidades": ["SUSPENSION", "REMOLQUE"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:00")),
            ("MARTES", _t("08:00"), _t("18:00")),
            ("MIERCOLES", _t("08:00"), _t("18:00")),
            ("JUEVES", _t("08:00"), _t("18:00")),
            ("VIERNES", _t("08:00"), _t("18:00")),
            ("SABADO", _t("08:00"), _t("13:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Nicolás Araujo Ticona",
                "ci": "2478001",
                "tel": "77800001",
                "especialidades": ["SUSPENSION", "REMOLQUE"],
            },
            {
                "nombre": "Pablo Montoya Jiménez",
                "ci": "3589002",
                "tel": "77800002",
                "especialidades": ["REMOLQUE"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Félix Araúz Terán",
            "ci": "3589015",
            "tel": "77890123",
            "email": "admin.loslotes@auxilio.bo",
        },
        "taller": {
            "nombre": "Taller Los Lotes",
            "descripcion": "Mecánica integral, zona Doble Vía La Guardia",
            "telefono": "77890123",
            "email": "taller.loslotes@gmail.com",
            "direccion": "Doble Vía La Guardia, Los Lotes, Santa Cruz",
            "latitud": -17.8092,
            "longitud": -63.1902,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["MOTOR", "BATERIA", "LLANTAS", "SUSPENSION"],
        "horarios": [
            ("LUNES", _t("07:30"), _t("18:00")),
            ("MARTES", _t("07:30"), _t("18:00")),
            ("MIERCOLES", _t("07:30"), _t("18:00")),
            ("JUEVES", _t("07:30"), _t("18:00")),
            ("VIERNES", _t("07:30"), _t("18:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Walter Roca Suárez",
                "ci": "3589003",
                "tel": "77900001",
                "especialidades": ["MOTOR", "BATERIA"],
            },
            {
                "nombre": "Raúl Justiniano Peña",
                "ci": "4690001",
                "tel": "77900002",
                "especialidades": ["LLANTAS", "SUSPENSION"],
            },
            {
                "nombre": "Eduardo Balcázar Vidal",
                "ci": "5701001",
                "tel": "77900003",
                "especialidades": ["MOTOR"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Teresa Justiniano Herbas",
            "ci": "4690126",
            "tel": "77901234",
            "email": "admin.urbari@auxilio.bo",
        },
        "taller": {
            "nombre": "AutoMec Urbarí",
            "descripcion": "Batería, cerrajería y llantas, zona Urbarí",
            "telefono": "77901234",
            "email": "automec.urbari@gmail.com",
            "direccion": "Av. Urbarí #89, Zona Sur, Santa Cruz",
            "latitud": -17.7758,
            "longitud": -63.1682,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["BATERIA", "CERRAJERIA_VEHICULAR", "LLANTAS"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:00")),
            ("MARTES", _t("08:00"), _t("18:00")),
            ("MIERCOLES", _t("08:00"), _t("18:00")),
            ("JUEVES", _t("08:00"), _t("18:00")),
            ("VIERNES", _t("08:00"), _t("18:00")),
            ("SABADO", _t("08:00"), _t("14:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Andrés Claros Montero",
                "ci": "4690002",
                "tel": "77010001",
                "especialidades": ["BATERIA", "CERRAJERIA_VEHICULAR"],
            },
            {
                "nombre": "Felipe Agreda Vásquez",
                "ci": "5701002",
                "tel": "77010002",
                "especialidades": ["LLANTAS", "BATERIA"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Santiago Leigue Coronado",
            "ci": "5801237",
            "tel": "77912345",
            "email": "admin.roca@auxilio.bo",
        },
        "taller": {
            "nombre": "Mecánica Roca",
            "descripcion": "Motor, suspensión y remolque. Centro sur de Santa Cruz",
            "telefono": "77912345",
            "email": "mecanica.roca@gmail.com",
            "direccion": "Av. Roca y Coronado #345, Centro Sur, Santa Cruz",
            "latitud": -17.7915,
            "longitud": -63.1795,
            "tiene_remolque": True,
            "atiende_24_horas": False,
        },
        "especialidades": ["MOTOR", "SUSPENSION", "REMOLQUE"],
        "horarios": [
            ("LUNES", _t("07:00"), _t("19:00")),
            ("MARTES", _t("07:00"), _t("19:00")),
            ("MIERCOLES", _t("07:00"), _t("19:00")),
            ("JUEVES", _t("07:00"), _t("19:00")),
            ("VIERNES", _t("07:00"), _t("19:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Tomás Mercado Quiroga",
                "ci": "5801001",
                "tel": "77110001",
                "especialidades": ["MOTOR", "SUSPENSION"],
            },
            {
                "nombre": "Alberto Navia Romero",
                "ci": "6912001",
                "tel": "77110002",
                "especialidades": ["REMOLQUE"],
            },
            {
                "nombre": "Hernán Soliz Torrez",
                "ci": "7023001",
                "tel": "77110003",
                "especialidades": ["MOTOR"],
            },
        ],
    },
    {
        "admin": {
            "nombre": "Viviana Caballero Ríos",
            "ci": "6912348",
            "tel": "77923456",
            "email": "admin.tallerpro@auxilio.bo",
        },
        "taller": {
            "nombre": "TallerPro SC",
            "descripcion": "Servicio integral: llantas, batería, motor, cerrajería y suspensión",
            "telefono": "77923456",
            "email": "tallerpro.sc@gmail.com",
            "direccion": "4to Anillo Este esq. Av. Paragua, Santa Cruz",
            "latitud": -17.7800,
            "longitud": -63.1408,
            "tiene_remolque": False,
            "atiende_24_horas": False,
        },
        "especialidades": ["LLANTAS", "BATERIA", "MOTOR", "CERRAJERIA_VEHICULAR", "SUSPENSION"],
        "horarios": [
            ("LUNES", _t("08:00"), _t("18:00")),
            ("MARTES", _t("08:00"), _t("18:00")),
            ("MIERCOLES", _t("08:00"), _t("18:00")),
            ("JUEVES", _t("08:00"), _t("18:00")),
            ("VIERNES", _t("08:00"), _t("18:00")),
            ("SABADO", _t("08:00"), _t("18:00")),
        ],
        "tecnicos": [
            {
                "nombre": "Cristian Pérez Oblitas",
                "ci": "6912002",
                "tel": "77120001",
                "especialidades": ["LLANTAS", "BATERIA"],
            },
            {
                "nombre": "Marco Polo Rivero",
                "ci": "7023002",
                "tel": "77120002",
                "especialidades": ["MOTOR", "SUSPENSION"],
            },
            {
                "nombre": "David Guzmán Arrieta",
                "ci": "8134001",
                "tel": "77120003",
                "especialidades": ["CERRAJERIA_VEHICULAR", "LLANTAS"],
            },
        ],
    },
]

# 10 clientes
CLIENTES = [
    {"nombre": "Juan Carlos Pérez Ortiz",    "ci": "7812340", "tel": "76100001", "email": "juan.perez@gmail.com"},
    {"nombre": "María García Fernández",      "ci": "8923451", "tel": "76100002", "email": "maria.garcia@gmail.com"},
    {"nombre": "Carlos Rodríguez Vaca",       "ci": "9034562", "tel": "76100003", "email": "carlos.rodriguez@gmail.com"},
    {"nombre": "Ana López Suárez",            "ci": "0145673", "tel": "76100004", "email": "ana.lopez@gmail.com"},
    {"nombre": "Pedro Mamani Quispe",         "ci": "1256784", "tel": "76100005", "email": "pedro.mamani@gmail.com"},
    {"nombre": "Lucía Vargas Méndez",         "ci": "2367895", "tel": "76100006", "email": "lucia.vargas@gmail.com"},
    {"nombre": "Roberto Quispe Flores",       "ci": "3478906", "tel": "76100007", "email": "roberto.quispe@gmail.com"},
    {"nombre": "Sofía Mendoza Paz",           "ci": "4589017", "tel": "76100008", "email": "sofia.mendoza@gmail.com"},
    {"nombre": "Diego Flores Arteaga",        "ci": "5690128", "tel": "76100009", "email": "diego.flores@gmail.com"},
    {"nombre": "Elena Chávez Romero",         "ci": "6701239", "tel": "76100010", "email": "elena.chavez@gmail.com"},
]

# 2 vehículos por cliente (20 total)
# [cliente_idx, placa, marca, modelo, anio_fabricacion, color]
# Placas bolivianas: pre-2000 → NNN-AAA | post-2000 → NNNN-AAA
VEHICLES = [
    [0, "3421-FKN", "Toyota",      "Corolla",       2019, "Blanco"],
    [0,  "892-TXP", "Honda",       "Civic",         1998, "Gris"],
    [1, "7234-RBM", "Nissan",      "Sentra",        2022, "Negro"],
    [1, "2189-WLS", "Suzuki",      "Grand Vitara",  2015, "Plateado"],
    [2, "4856-JZC", "Toyota",      "Hilux",         2020, "Gris"],
    [2,  "743-ZPK", "Ford",        "Ranger",        1995, "Rojo"],
    [3, "8912-DLV", "Hyundai",     "Tucson",        2023, "Blanco"],
    [3, "1578-NQR", "Mitsubishi",  "Montero",       2000, "Verde"],
    [4, "2367-KTW", "Kia",         "Sportage",      2018, "Azul"],
    [4,  "651-YBM", "Chevrolet",   "S10",           1997, "Rojo"],
    [5, "3145-PHX", "Volkswagen",  "Gol",           2016, "Rojo"],
    [5, "6789-AKJ", "Toyota",      "RAV4",          2021, "Blanco"],
    [6, "4523-CMN", "Toyota",      "Prado",         2017, "Negro"],
    [6, "1890-STV", "Isuzu",       "D-Max",         2012, "Plateado"],
    [7, "5671-RWF", "Suzuki",      "Vitara",        2020, "Gris"],
    [7, "2456-BQT", "Chevrolet",   "Trailblazer",   2014, "Negro"],
    [8, "3987-LPD", "Nissan",      "Frontier",      2019, "Blanco"],
    [8,  "478-JEM", "Ford",        "F-150",         1993, "Negro"],
    [9, "7654-MNZ", "Honda",       "CR-V",          2022, "Plata"],
    [9, "4312-VKB", "Renault",     "Duster",        2018, "Naranja"],
]

# Incidentes — 15 casos en distintos estados del flujo
# Keys:
#   estado        → estado del incidente (y base para el estado de asignación)
#   tipo          → tipo de incidente (clave en tipos_incidente)
#   prioridad     → BAJA|MEDIA|ALTA|CRITICA|INCIERTA
#   cliente_i     → índice en CLIENTES
#   vehiculo_i    → índice en VEHICLES
#   taller_i      → índice en WORKSHOPS (None = sin asignación)
#   tecnico_i     → índice del técnico dentro del taller (None = sin técnico)
#   titulo, descripcion, direccion, lat, lon, requiere_remolque
#   monto         → monto del servicio (float o None)
#   calificacion  → 1-5 (solo para PAGADO, opcional)
#   comentario    → comentario de calificación (opcional)
#   candidatos    → lista de workshop_idx candidatos (solo para NOTIFICADO)
INCIDENTS = [
    # ── PAGADO (3) ──────────────────────────────────────────────────────────
    {
        "estado": "PAGADO", "tipo": "BATERIA", "prioridad": "MEDIA",
        "cliente_i": 0, "vehiculo_i": 0, "taller_i": 0, "tecnico_i": 0,
        "titulo": "Batería descargada en el centro",
        "descripcion": "El Toyota Corolla no enciende. Batería totalmente descargada, quedé varado frente al mercado.",
        "direccion": "Av. Cañoto esq. Mercado, Centro, Santa Cruz",
        "lat": -17.7858, "lon": -63.1815, "requiere_remolque": False,
        "monto": 150.00, "calificacion": 5, "comentario": "Excelente servicio, muy rápidos y profesionales",
    },
    {
        "estado": "PAGADO", "tipo": "LLANTA", "prioridad": "BAJA",
        "cliente_i": 1, "vehiculo_i": 2, "taller_i": 1, "tecnico_i": 0,
        "titulo": "Pinchazo en zona Equipetrol",
        "descripcion": "Llanta delantera derecha pinchada. No tengo gata ni llanta de repuesto.",
        "direccion": "Av. San Martín, Equipetrol Norte, Santa Cruz",
        "lat": -17.7625, "lon": -63.1970, "requiere_remolque": False,
        "monto": 80.00, "calificacion": 4, "comentario": "Buen servicio, aunque tardó un poco en llegar",
    },
    {
        "estado": "PAGADO", "tipo": "MOTOR", "prioridad": "ALTA",
        "cliente_i": 4, "vehiculo_i": 9, "taller_i": 3, "tecnico_i": 0,
        "titulo": "Motor recalentado, humo blanco",
        "descripcion": "El Chevrolet S10 larga humo blanco del capot, el motor se sobrecalentó.",
        "direccion": "Av. Los Cusis, Barrio Lindo, Santa Cruz",
        "lat": -17.7480, "lon": -63.1820, "requiere_remolque": False,
        "monto": 350.00, "calificacion": 5, "comentario": "Muy eficientes, resolvieron el problema rápido",
    },
    # ── ATENDIDO (2) ────────────────────────────────────────────────────────
    {
        "estado": "ATENDIDO", "tipo": "MOTOR", "prioridad": "ALTA",
        "cliente_i": 2, "vehiculo_i": 4, "taller_i": 2, "tecnico_i": 0,
        "titulo": "Motor no arranca en Plan 3000",
        "descripcion": "La Toyota Hilux no arranca, el motor gira pero no enciende. Quedé parado en la avenida.",
        "direccion": "Av. Santos Dumont, Plan 3000, Santa Cruz",
        "lat": -17.8188, "lon": -63.1158, "requiere_remolque": False,
        "monto": 280.00,
    },
    {
        "estado": "ATENDIDO", "tipo": "BATERIA", "prioridad": "MEDIA",
        "cliente_i": 9, "vehiculo_i": 18, "taller_i": 9, "tecnico_i": 0,
        "titulo": "Batería agotada en Urbarí",
        "descripcion": "El Honda CR-V no enciende, quedé varada en la avenida Urbarí.",
        "direccion": "Av. Urbarí, Zona Sur, Santa Cruz",
        "lat": -17.7770, "lon": -63.1672, "requiere_remolque": False,
        "monto": 130.00,
    },
    # ── PENDIENTE_PAGO (2) ──────────────────────────────────────────────────
    {
        "estado": "PENDIENTE_PAGO", "tipo": "LLANTA", "prioridad": "BAJA",
        "cliente_i": 5, "vehiculo_i": 10, "taller_i": 4, "tecnico_i": 0,
        "titulo": "Llanta pinchada en Av. Banzer",
        "descripcion": "Pinchazo trasero izquierdo del Volkswagen Gol. Necesito cambio urgente.",
        "direccion": "Av. Banzer 3er Anillo, Santa Cruz",
        "lat": -17.7695, "lon": -63.1965, "requiere_remolque": False,
        "monto": 75.00,
    },
    {
        "estado": "PENDIENTE_PAGO", "tipo": "CHOQUE", "prioridad": "ALTA",
        "cliente_i": 6, "vehiculo_i": 12, "taller_i": 5, "tecnico_i": 0,
        "titulo": "Colisión leve, necesito remolque",
        "descripcion": "Tuve un golpe lateral, el Toyota Prado no puede moverse. Necesito remolque al taller.",
        "direccion": "Av. Mutualista, Villa 1ro de Mayo, Santa Cruz",
        "lat": -17.8340, "lon": -63.1710, "requiere_remolque": True,
        "monto": 250.00,
    },
    # ── EN_PROCESO (2) ──────────────────────────────────────────────────────
    {
        "estado": "EN_PROCESO", "tipo": "BATERIA", "prioridad": "MEDIA",
        "cliente_i": 3, "vehiculo_i": 6, "taller_i": 6, "tecnico_i": 0,
        "titulo": "Batería muerta en zona norte",
        "descripcion": "El Hyundai Tucson no enciende desde esta mañana, la batería no da señal.",
        "direccion": "Av. Cristo Redentor, Zona Norte, Santa Cruz",
        "lat": -17.7510, "lon": -63.1975, "requiere_remolque": False,
        "monto": None,
    },
    {
        "estado": "EN_PROCESO", "tipo": "LLAVE", "prioridad": "MEDIA",
        "cliente_i": 7, "vehiculo_i": 14, "taller_i": 11, "tecnico_i": 2,
        "titulo": "Llave olvidada dentro del vehículo",
        "descripcion": "Las llaves quedaron dentro de la Suzuki Vitara con el seguro central activado.",
        "direccion": "4to Anillo Este, Santa Cruz",
        "lat": -17.7810, "lon": -63.1420, "requiere_remolque": False,
        "monto": None,
    },
    # ── ACEPTADO (2) ────────────────────────────────────────────────────────
    {
        "estado": "ACEPTADO", "tipo": "LLANTA", "prioridad": "BAJA",
        "cliente_i": 8, "vehiculo_i": 16, "taller_i": 8, "tecnico_i": 1,
        "titulo": "Llanta reventada en Los Lotes",
        "descripcion": "Reventón de llanta trasera derecha de la Nissan Frontier en la autopista.",
        "direccion": "Doble Vía La Guardia, Los Lotes, Santa Cruz",
        "lat": -17.8068, "lon": -63.1888, "requiere_remolque": False,
        "monto": None,
    },
    {
        "estado": "ACEPTADO", "tipo": "MOTOR", "prioridad": "ALTA",
        "cliente_i": 0, "vehiculo_i": 1, "taller_i": 11, "tecnico_i": 1,
        "titulo": "Honda Civic apagado, falla de motor",
        "descripcion": "El Honda Civic 98 se apagó de repente en el 4to anillo y no vuelve a encender.",
        "direccion": "4to Anillo Este esq. Av. Paragua, Santa Cruz",
        "lat": -17.7822, "lon": -63.1418, "requiere_remolque": False,
        "monto": None,
    },
    # ── NOTIFICADO (2) ──────────────────────────────────────────────────────
    {
        "estado": "NOTIFICADO", "tipo": "BATERIA", "prioridad": "MEDIA",
        "cliente_i": 1, "vehiculo_i": 3, "taller_i": None, "tecnico_i": None,
        "titulo": "Batería descargada en centro sur",
        "descripcion": "La Suzuki Grand Vitara no enciende, la batería ya estaba fallando hace días.",
        "direccion": "Av. Roca y Coronado, Centro Sur, Santa Cruz",
        "lat": -17.7920, "lon": -63.1790, "requiere_remolque": False,
        "monto": None,
        "candidatos": [10, 0],  # Mecánica Roca, AutoService Cruz del Sur
    },
    {
        "estado": "NOTIFICADO", "tipo": "LLANTA", "prioridad": "BAJA",
        "cliente_i": 2, "vehiculo_i": 5, "taller_i": None, "tecnico_i": None,
        "titulo": "Llanta pinchada, Ford Ranger 95",
        "descripcion": "Llanta trasera pinchada del Ford Ranger del 95. Sin llanta de repuesto.",
        "direccion": "Av. San Martín, Equipetrol, Santa Cruz",
        "lat": -17.7635, "lon": -63.1962, "requiere_remolque": False,
        "monto": None,
        "candidatos": [1, 6],  # Mecánica Los Andes, Mecánica El Cristo Norte
    },
    # ── PENDIENTE (2) ───────────────────────────────────────────────────────
    {
        "estado": "PENDIENTE", "tipo": "INCIERTO", "prioridad": "INCIERTA",
        "cliente_i": 4, "vehiculo_i": 8, "taller_i": None, "tecnico_i": None,
        "titulo": "Kia Sportage con falla desconocida",
        "descripcion": "El auto hace un ruido extraño al acelerar y perdió potencia. No sé qué es.",
        "direccion": "Av. Alemana, Zona Norte, Santa Cruz",
        "lat": -17.7530, "lon": -63.2002, "requiere_remolque": False,
        "monto": None,
    },
    {
        "estado": "PENDIENTE", "tipo": "MOTOR", "prioridad": "ALTA",
        "cliente_i": 9, "vehiculo_i": 19, "taller_i": None, "tecnico_i": None,
        "titulo": "Renault Duster recalentado",
        "descripcion": "El Duster largó vapor por el capot y se apagó. Necesito ayuda urgente.",
        "direccion": "Av. Monseñor Rivero, Zona Norte, Santa Cruz",
        "lat": -17.7610, "lon": -63.1875, "requiere_remolque": True,
        "monto": None,
    },
]

# Mapa: tipo de incidente → especialidad del taller recomendada
TIPO_A_ESPECIALIDAD = {
    "BATERIA":  "BATERIA",
    "LLANTA":   "LLANTAS",
    "MOTOR":    "MOTOR",
    "CHOQUE":   "REMOLQUE",
    "LLAVE":    "CERRAJERIA_VEHICULAR",
    "INCIERTO": None,
}

# Estado incidente → estado asignación
ESTADO_A_ASIGNACION = {
    "ACEPTADO":      "ASIGNADO",
    "EN_PROCESO":    "EN_PROCESO",
    "ATENDIDO":      "ATENDIDO",
    "PENDIENTE_PAGO":"PENDIENTE_PAGO",
    "PAGADO":        "PAGADO",
}


# ── Seed ──────────────────────────────────────────────────────────────────────


async def seed(conn: asyncpg.Connection) -> None:
    # ── 0. Idempotency check ─────────────────────────────────────────────────
    existing = await conn.fetchval(
        f"SELECT id FROM {S}.usuarios WHERE correo_electronico = $1",
        SUPERADMIN["email"],
    )
    if existing:
        print("ℹ️  Datos demo ya sembrados. Para re-sembrar, elimina primero el usuario superadmin@auxilio.bo.")
        return

    # ── 1. Fetch catalog IDs ─────────────────────────────────────────────────
    rows = await conn.fetch(f"SELECT nombre, id FROM {S}.especialidades")
    spec_ids: dict[str, int] = {r["nombre"]: r["id"] for r in rows}
    if not spec_ids:
        print("❌  Las especialidades no están sembradas. Ejecuta init_db primero (corre la app una vez).")
        return

    rows = await conn.fetch(f"SELECT nombre, id FROM {S}.tipos_incidente")
    type_ids: dict[str, int] = {r["nombre"]: r["id"] for r in rows}

    rows = await conn.fetch(f"SELECT nombre, id FROM {S}.estados_incidente")
    status_ids: dict[str, int] = {r["nombre"]: r["id"] for r in rows}

    # ── 2. Password hash (computed once, reused for all demo users) ──────────
    print("🔐  Generando hash de contraseña demo (puede tardar ~1s)...")
    pw_hash = _hash_password(DEMO_PASSWORD)

    # ── 3. Superadmin ────────────────────────────────────────────────────────
    await _upsert_user(
        conn,
        SUPERADMIN["email"], "SUPERADMIN",
        SUPERADMIN["nombre"], SUPERADMIN["ci"], SUPERADMIN["tel"],
        pw_hash,
    )
    print("✓  Superadmin")

    # ── 4. Admin_Taller + Talleres + Técnicos ────────────────────────────────
    print(f"🏪  Insertando {len(WORKSHOPS)} talleres con técnicos...")
    workshop_ids: list[int] = []
    tech_ids_per_workshop: list[list[int]] = []

    for ws in WORKSHOPS:
        admin_id = await _upsert_user(
            conn,
            ws["admin"]["email"], "ADMIN_TALLER",
            ws["admin"]["nombre"], ws["admin"]["ci"], ws["admin"]["tel"],
            pw_hash,
        )

        t = ws["taller"]
        ws_id: int = await conn.fetchval(
            f"""INSERT INTO {S}.talleres
                    (administrador_usuario_id, nombre, descripcion, telefono,
                     correo_electronico, direccion, latitud, longitud,
                     tiene_remolque, atiende_24_horas)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id""",
            admin_id,
            t["nombre"], t["descripcion"], t["telefono"], t["email"],
            t["direccion"], t["latitud"], t["longitud"],
            t["tiene_remolque"], t["atiende_24_horas"],
        )
        workshop_ids.append(ws_id)

        for dia, h_ini, h_fin in ws["horarios"]:
            await conn.execute(
                f"""INSERT INTO {S}.horarios_taller (taller_id, dia_semana, hora_inicio, hora_fin)
                    VALUES ($1,$2,$3,$4)
                    ON CONFLICT ON CONSTRAINT uq_horarios_taller DO NOTHING""",
                ws_id, dia, h_ini, h_fin,
            )

        for esp_nombre in ws["especialidades"]:
            eid = spec_ids.get(esp_nombre)
            if eid:
                await conn.execute(
                    f"""INSERT INTO {S}.taller_especialidades (taller_id, especialidad_id)
                        VALUES ($1,$2)
                        ON CONFLICT ON CONSTRAINT uq_taller_especialidad DO NOTHING""",
                    ws_id, eid,
                )

        techs: list[int] = []
        for tec in ws["tecnicos"]:
            tec_id: int = await conn.fetchval(
                f"""INSERT INTO {S}.tecnicos (taller_id, nombre_completo, ci, telefono)
                    VALUES ($1,$2,$3,$4) RETURNING id""",
                ws_id, tec["nombre"], tec["ci"], tec["tel"],
            )
            techs.append(tec_id)
            for esp_nombre in tec["especialidades"]:
                eid = spec_ids.get(esp_nombre)
                if eid:
                    await conn.execute(
                        f"""INSERT INTO {S}.tecnico_especialidades (tecnico_id, especialidad_id)
                            VALUES ($1,$2)
                            ON CONFLICT ON CONSTRAINT uq_tecnico_especialidad DO NOTHING""",
                        tec_id, eid,
                    )
        tech_ids_per_workshop.append(techs)

    print(f"✓  {len(workshop_ids)} talleres — {sum(len(t) for t in tech_ids_per_workshop)} técnicos")

    # ── 5. Clientes ──────────────────────────────────────────────────────────
    print(f"👤  Insertando {len(CLIENTES)} clientes...")
    client_ids: list[int] = []
    for c in CLIENTES:
        cid = await _upsert_user(
            conn,
            c["email"], "CLIENTE",
            c["nombre"], c["ci"], c["tel"],
            pw_hash,
        )
        client_ids.append(cid)

    # ── 6. Vehículos ─────────────────────────────────────────────────────────
    print(f"🚗  Insertando {len(VEHICLES)} vehículos...")
    vehicle_ids: list[int] = []
    for v in VEHICLES:
        client_i, placa, marca, modelo, anio, color = v
        vid: int = await conn.fetchval(
            f"""INSERT INTO {S}.vehiculos (usuario_id, placa, marca, modelo, anio_fabricacion, color)
                VALUES ($1,$2,$3,$4,$5,$6)
                ON CONFLICT (placa) DO UPDATE SET placa = EXCLUDED.placa
                RETURNING id""",
            client_ids[client_i], placa, marca, modelo, anio, color,
        )
        vehicle_ids.append(vid)
    print(f"✓  Clientes y vehículos")

    # ── 7. Incidentes con cadena completa ────────────────────────────────────
    print(f"🚨  Insertando {len(INCIDENTS)} incidentes...")
    now = datetime.now(UTC).replace(tzinfo=None)  # naive UTC — columnas son TIMESTAMP sin zone

    for i, inc in enumerate(INCIDENTS):
        estado = inc["estado"]
        estado_id = status_ids[estado]
        tipo_id = type_ids.get(inc["tipo"])
        client_id = client_ids[inc["cliente_i"]]
        vehicle_id = vehicle_ids[inc["vehiculo_i"]]

        # Timestamps distribuidos en los últimos 30 días
        days_ago = 30 - i * 2
        fecha_solicitud = now - timedelta(days=days_ago)
        has_assignment = estado in ESTADO_A_ASIGNACION
        fecha_aceptacion = fecha_solicitud + timedelta(minutes=15) if has_assignment else None
        fecha_inicio = (
            fecha_aceptacion + timedelta(minutes=30)
            if fecha_aceptacion and estado not in ("ACEPTADO",)
            else None
        )
        fecha_fin = (
            fecha_inicio + timedelta(hours=2)
            if fecha_inicio and estado in ("ATENDIDO", "PENDIENTE_PAGO", "PAGADO")
            else None
        )

        inc_id: int = await conn.fetchval(
            f"""INSERT INTO {S}.incidentes
                    (cliente_usuario_id, vehiculo_id, tipo_incidente_id, estado_incidente_id,
                     titulo, descripcion_texto, direccion_referencia, latitud, longitud,
                     nivel_prioridad, requiere_remolque, fecha_solicitud,
                     fecha_aceptacion, fecha_inicio_atencion, fecha_finalizacion)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING id""",
            client_id, vehicle_id, tipo_id, estado_id,
            inc["titulo"], inc["descripcion"], inc["direccion"],
            inc["lat"], inc["lon"],
            inc["prioridad"], inc["requiere_remolque"], fecha_solicitud,
            fecha_aceptacion, fecha_inicio, fecha_fin,
        )

        # Candidatos para incidentes NOTIFICADO
        if estado == "NOTIFICADO":
            for rank, ws_cand_i in enumerate(inc.get("candidatos", [])):
                ws_cand_id = workshop_ids[ws_cand_i]
                await conn.execute(
                    f"""INSERT INTO {S}.candidatos_taller_incidente
                            (incidente_id, taller_id, puntaje, distancia_km,
                             fue_notificado, estado_respuesta)
                        VALUES ($1,$2,$3,$4,$5,$6)
                        ON CONFLICT ON CONSTRAINT uq_candidato_taller_incidente DO NOTHING""",
                    inc_id, ws_cand_id,
                    round(90.0 - rank * 8, 2), round(1.2 + rank * 1.1, 2),
                    True, "PENDIENTE",
                )

        # Asignación de servicio para ACEPTADO y estados posteriores
        if has_assignment:
            ws_id = workshop_ids[inc["taller_i"]]
            techs = tech_ids_per_workshop[inc["taller_i"]]
            ti = inc.get("tecnico_i")
            tech_id = techs[ti] if ti is not None and ti < len(techs) else None

            esp_nombre = TIPO_A_ESPECIALIDAD.get(inc["tipo"])
            esp_id = spec_ids.get(esp_nombre) if esp_nombre else None
            monto = inc.get("monto")
            costo_final = monto if estado in ("ATENDIDO", "PAGADO") else None
            desc_servicio = (
                f"Servicio de {inc['tipo'].lower()} realizado exitosamente"
                if estado in ("ATENDIDO", "PAGADO")
                else None
            )

            assig_id: int = await conn.fetchval(
                f"""INSERT INTO {S}.asignaciones_servicio
                        (incidente_id, taller_id, tecnico_id, especialidad_id,
                         estado_asignacion, distancia_km, tiempo_estimado_llegada_min,
                         costo_estimado, costo_final, descripcion_servicio_realizado)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id""",
                inc_id, ws_id, tech_id, esp_id,
                ESTADO_A_ASIGNACION[estado],
                round(1.5 + i * 0.4, 2),
                8 + i * 2,
                monto, costo_final, desc_servicio,
            )

            # Pago para PENDIENTE_PAGO y PAGADO
            if estado in ("PENDIENTE_PAGO", "PAGADO"):
                pago_status = "PAGADO" if estado == "PAGADO" else "PENDIENTE"
                fecha_pago = (
                    fecha_fin + timedelta(hours=1) if estado == "PAGADO" and fecha_fin else None
                )
                await conn.execute(
                    f"""INSERT INTO {S}.pagos
                            (asignacion_servicio_id, cliente_usuario_id, monto,
                             metodo_pago, estado_pago, fecha_pago)
                        VALUES ($1,$2,$3,$4,$5,$6)""",
                    assig_id, client_id, monto, "QR", pago_status, fecha_pago,
                )

            # Calificación para PAGADO
            if estado == "PAGADO" and inc.get("calificacion"):
                await conn.execute(
                    f"""INSERT INTO {S}.calificaciones
                            (asignacion_servicio_id, cliente_usuario_id, puntuacion, comentario)
                        VALUES ($1,$2,$3,$4)""",
                    assig_id, client_id, inc["calificacion"], inc.get("comentario"),
                )

    print(f"✓  {len(INCIDENTS)} incidentes con cadenas completas")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print()
    print("=" * 56)
    print("✅  Seed demo completado")
    print("=" * 56)
    print(f"  Contraseña de todos los usuarios: {DEMO_PASSWORD}")
    print()
    print("  Talleres insertados:")
    for ws in WORKSHOPS:
        t = ws["taller"]
        print(f"    · {t['nombre']:35s}  {t['latitud']}, {t['longitud']}")
    print()
    print("  Usuarios ADMIN_TALLER (12) + CLIENTE (10) + SUPERADMIN (1)")
    print("  Vehículos: 20  |  Incidentes: 15")
    print("    PAGADO: 3  |  ATENDIDO: 2  |  PENDIENTE_PAGO: 2")
    print("    EN_PROCESO: 2  |  ACEPTADO: 2  |  NOTIFICADO: 2  |  PENDIENTE: 2")
    print("=" * 56)


async def main() -> None:
    print(f"Conectando a: {re.sub(r':([^:@/]+)@', ':***@', DSN)}")
    conn = await asyncpg.connect(DSN)
    try:
        await seed(conn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
