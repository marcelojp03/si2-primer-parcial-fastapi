"""Servicio para generación de reportes en lenguaje natural (CU35).

Convierte una consulta en español a SQL usando OpenAI, valida que sea
solo lectura y la ejecuta contra la base de datos.
"""

import re

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError

# ─── Contexto del esquema (simplificado para el prompt) ──────────────────────
_SCHEMA_CONTEXT = """
Schema: auxilio_mecanico

Tablas principales:
  incidentes(id, titulo, descripcion_texto, estado_incidente_id, prioridad, latitud, longitud,
             solicitado_en, aceptado_en, finalizado_en, uuid_cliente, tipo_incidente_id,
             usuario_cliente_id, vehiculo_id)
  estados_incidente(id, nombre)                   -- nombre: PENDIENTE, ASIGNADO, EN_CAMINO, EN_SERVICIO, FINALIZADO, CANCELADO
  tipos_incidente(id, nombre, sla_minutos)
  asignaciones_servicio(id, incidente_id, taller_id, estado_asignacion, tenant_id,
                        creado_en, actualizado_en)
  talleres(id, nombre, tenant_id, estado, puntaje_reputacion)
  tenants(id, nombre, slug, estado)
  usuarios(id, nombre_completo, email, rol, tenant_id)   -- rol: CLIENTE, ADMIN_TALLER, SUPERADMIN
  vehiculos(id, usuario_id, placa, marca, modelo, anio)
  pagos(id, asignacion_id, monto, metodo_pago, estado_pago, creado_en)
  calificaciones(id, asignacion_id, puntaje, comentario, creado_en)
  tecnicos(id, taller_id, nombre_completo, disponible)
  seguimiento_ubicacion_incidente(id, incidente_id, latitud, longitud, registrado_en)
"""

# ─── Prompt del sistema ───────────────────────────────────────────────────────
_SYSTEM_PROMPT = f"""
Eres un asistente que convierte preguntas en español sobre la plataforma de auxilio mecánico
a consultas SQL para PostgreSQL.

{_SCHEMA_CONTEXT}

REGLAS CRÍTICAS (debes cumplirlas todas):
1. SOLO genera consultas SELECT. Nunca INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, GRANT, etc.
2. Usa el schema auxilio_mecanico. Prefija SIEMPRE las tablas: auxilio_mecanico.incidentes, etc.
3. Devuelve ÚNICAMENTE el SQL, sin explicaciones, sin markdown, sin backticks.
4. Si la pregunta pide datos de un tenant específico y se proporciona un tenant_id, añade
   el filtro WHERE <tabla>.tenant_id = <tenant_id> o mediante JOIN.
5. Limita resultados con LIMIT 500 si no se especifica un límite.
6. Usa aliases descriptivos en español para los campos del SELECT.
7. Si la pregunta no puede responderse con el esquema dado, devuelve exactamente: ERROR: pregunta_fuera_de_alcance
""".strip()


def _is_safe_sql(sql: str) -> bool:
    """Verifica que el SQL generado sea solo lectura."""
    normalized = sql.strip().upper()
    # Debe empezar con SELECT o WITH (CTEs)
    if not re.match(r"^\s*(SELECT|WITH)\b", normalized):
        return False
    # No debe contener palabras DML/DDL peligrosas
    dangerous = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|EXEC|EXECUTE|"
        r"CALL|MERGE|REPLACE|COPY|VACUUM|ANALYZE|LOCK|SET\s+ROLE|SET\s+SEARCH_PATH)\b"
    )
    if dangerous.search(normalized):
        return False
    return True


class NLReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def run(self, query: str, tenant_id: int | None = None) -> dict:
        sql = await self._generate_sql(query, tenant_id)

        if sql.startswith("ERROR:"):
            raise BadRequestError(f"No se puede responder la consulta: {sql}")

        if not _is_safe_sql(sql):
            raise BadRequestError("El SQL generado no es seguro o no es de solo lectura")

        rows = await self._execute_sql(sql)
        return {
            "query": query,
            "sql": sql,
            "data": rows,
            "rows_count": len(rows),
        }

    async def _generate_sql(self, question: str, tenant_id: int | None) -> str:
        tenant_hint = (
            f"\nEl tenant_id del usuario actual es: {tenant_id}." if tenant_id else ""
        )
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"{question}{tenant_hint}",
                },
            ],
            temperature=0,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    async def _execute_sql(self, sql: str) -> list[dict]:
        result = await self.session.execute(text(sql))
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]
