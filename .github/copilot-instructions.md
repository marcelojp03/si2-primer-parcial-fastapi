# Instrucciones FastAPI — Auxilio Mecánico · SI2 2026

> Documentación completa en el workspace raíz `.github/`:
> - `DATABASE.md` → diseño de BD y nombres exactos de campos
> - `API.md` → contrato de todos los endpoints
> - `FASTAPI.md` → plan de implementación, fórmula del motor, estado actual

---

## Stack

- Python 3.11+, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic v2
- PostgreSQL 15+ · schema `auxilio_mecanico` (nunca `public`)
- JWT (Bearer token), AWS S3, Firebase FCM, OpenAI (Whisper + GPT-5.4-mini)

## Estructura de carpetas

```
app/
  api/v1/endpoints/   → routers FastAPI (un archivo por dominio)
  core/               → config, security, exceptions, logging
  db/                 → session async, base, init_db
  middlewares/        → error_handler, request_id
  models/             → modelos SQLAlchemy (mapeo a auxilio_mecanico.*)
  repositories/       → acceso a BD (async, sin lógica de negocio)
  schemas/            → Pydantic v2 (Request/Response por dominio)
  services/           → lógica de negocio + llamadas a IA/S3/FCM
  utils/              → haversine, s3_client, fcm_client, openai_client
```

## Reglas críticas

1. **Flujo obligatorio:** `endpoint → service → repository`. Nunca saltar capas.
2. **Schema `auxilio_mecanico`** en todos los modelos:
   ```python
   __table_args__ = {"schema": "auxilio_mecanico"}
   ```
3. **snake_case** en todo: variables, funciones, campos de BD, rutas.
4. **Async/await** en todos los handlers y servicios sin excepción.
5. **PKs:** `Identity()` → `BIGINT GENERATED ALWAYS AS IDENTITY`.
6. **Archivos** (fotos, audios) van a **S3**, nunca a la BD.
   - `url_archivo` = URL pública/presigned
   - `clave_archivo` = key en el bucket
7. **No WebSockets.** El estado se actualiza por polling o recarga.
8. **Distancias** con fórmula Haversine (`utils/haversine.py`), no OSRM.
9. **Notificaciones push** vía Firebase FCM desde `services/notification_service.py`.
10. **JWT** en header `Authorization: Bearer <token>`. Login y register son públicos.

## Sincronización con API.md — OBLIGATORIO

Cada vez que se modifique, agregue o elimine un endpoint, se **debe** actualizar `.github/API.md` en el workspace raíz:

1. **Modificar** la sección correspondiente en `API.md` con los nuevos campos, estados o comportamiento.
2. **Marcar el endpoint cambiado** agregando `⚠️ UPDATED` al título del endpoint:
   ```markdown
   ### POST /api/v1/incidents ⚠️ UPDATED
   ```
3. Al inicio de `API.md`, actualizar el bloque de cambios recientes:
   ```markdown
   ## Últimos cambios
   | Fecha | Endpoint | Tipo | Descripción |
   |-------|----------|------|-------------|
   | 2026-04-29 | POST /api/v1/incidents | MODIFIED | Agregado campo `titulo` obligatorio |
   ```
4. Angular y Flutter deben revisar los endpoints marcados con `⚠️ UPDATED` antes de integrar.
5. Una vez que Angular y Flutter confirmen la integración, retirar el marcador `⚠️ UPDATED`.

## Nombres de campos clave (BD real)

| Tabla                        | Campos importantes |
|------------------------------|--------------------|
| `usuarios`                   | `nombre_completo`, `correo_electronico`, `contrasena_hash`, `estado` (ACTIVO/INACTIVO/SUSPENDIDO) |
| `talleres`                   | `administrador_usuario_id`, `tiene_remolque`, `atiende_24_horas`, `estado` |
| `horarios_taller`            | `dia_semana` (LUNES…DOMINGO), `hora_inicio`, `hora_fin` |
| `tecnicos`                   | `nombre_completo`, `ci`, `estado_disponibilidad` (DISPONIBLE/OCUPADO/INACTIVO) |
| `incidentes`                 | `titulo`, `nivel_prioridad` (BAJA/MEDIA/ALTA/CRITICA/INCIERTA), `requiere_remolque`, `estado_incidente_id` |
| `evidencias_incidente`       | `url_archivo`, `clave_archivo`, `tipo_evidencia` (IMAGEN/AUDIO/VIDEO/DOCUMENTO) |
| `analisis_ia_incidente`      | `audio_transcrito`, `resumen_generado`, `tipo_incidente_predicho_id`, `puntaje_confianza` (0-100) |
| `candidatos_taller_incidente`| `puntaje`, `distancia_km`, `tiempo_estimado_llegada_min`, `estado_respuesta` (PENDIENTE/ACEPTADO/RECHAZADO/EXPIRADO) |
| `asignaciones_servicio`      | `especialidad_id`, `costo_estimado`, `costo_final`, `estado_asignacion` (ASIGNADO/EN_CAMINO/EN_PROCESO/ATENDIDO/CANCELADO/PENDIENTE_PAGO/PAGADO) |
| `pagos`                      | `asignacion_servicio_id`, `metodo_pago` (QR/EFECTIVO/TRANSFERENCIA), `moneda` (default BOB) |
| `notificaciones`             | `canal` (PUSH/EMAIL/SMS/IN_APP), `mensaje`, `estado` (PENDIENTE/ENVIADA/LEIDA/FALLIDA) |

## Motor de Asignación (fórmula)

```
score = (w_dist × norm_distancia) + (w_esp × coincide_especialidad) + (w_disp × disponibilidad) + (w_prio × prioridad)
```

Pesos por defecto: distancia 40%, especialidad 30%, disponibilidad 20%, prioridad 10%.
Se seleccionan los top-N talleres (default 5, configurable vía `ASSIGNMENT_MAX_CANDIDATES`), se registran en `candidatos_taller_incidente` y se notifica vía FCM. `max_candidates=0` desactiva el límite.

## Pipeline de IA

1. `POST /api/v1/incidents/{id}/analyze`
2. Descargar evidencias de S3
3. Whisper transcribe audios → `audio_transcrito`
4. GPT-5.4-mini Vision analiza imágenes + transcripción + descripción
5. Resultado se guarda en `analisis_ia_incidente`
6. Se actualiza `tipo_incidente_id`, `nivel_prioridad` en `incidentes`
7. Se lanza motor de asignación

## Convenciones de commits

```
feat(auth): implement JWT refresh token
fix(incidents): correct haversine calculation
refactor(assignments): extract scoring to service layer
chore(deps): update openai to 1.x
```
