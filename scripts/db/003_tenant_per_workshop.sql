-- =============================================================================
-- Migration 003: Tenant por taller existente
-- Fecha: 2026-06-07
-- Descripcion:
--   - Crea un tenant estable por cada taller existente.
--   - Reasigna talleres, ADMIN_TALLER y asignaciones_servicio al tenant del taller.
--   - Mantiene CLIENTE y SUPERADMIN como usuarios globales con tenant_id NULL.
--   - No elimina el tenant default.
--   - No agrega ni modifica tenant_id en incidentes.
--
-- IMPORTANTE:
--   Revisar los SELECT de validacion al final antes y despues de ejecutar.
-- =============================================================================

BEGIN;

SET search_path TO auxilio_mecanico;

-- ---------------------------------------------------------------------------
-- 1. Crear un tenant por cada taller existente.
--    Slug estable: taller-{id}. No depende del nombre del taller.
-- ---------------------------------------------------------------------------
INSERT INTO auxilio_mecanico.tenants (nombre, slug, estado)
SELECT
    LEFT(COALESCE(NULLIF(t.nombre, ''), 'Taller ' || t.id::TEXT), 150) AS nombre,
    'taller-' || t.id::TEXT AS slug,
    'ACTIVO' AS estado
FROM auxilio_mecanico.talleres t
WHERE NOT EXISTS (
    SELECT 1
    FROM auxilio_mecanico.tenants existing
    WHERE existing.slug = 'taller-' || t.id::TEXT
);

-- ---------------------------------------------------------------------------
-- 2. Asociar cada taller a su tenant propio.
-- ---------------------------------------------------------------------------
UPDATE auxilio_mecanico.talleres t
SET tenant_id = tenant.id,
    fecha_actualizacion = NOW()
FROM auxilio_mecanico.tenants tenant
WHERE tenant.slug = 'taller-' || t.id::TEXT
  AND t.tenant_id IS DISTINCT FROM tenant.id;

-- ---------------------------------------------------------------------------
-- 3. Asociar cada ADMIN_TALLER al tenant del taller que administra.
-- ---------------------------------------------------------------------------
UPDATE auxilio_mecanico.usuarios u
SET tenant_id = t.tenant_id,
    fecha_actualizacion = NOW()
FROM auxilio_mecanico.talleres t
WHERE t.administrador_usuario_id = u.id
  AND u.rol = 'ADMIN_TALLER'
  AND u.tenant_id IS DISTINCT FROM t.tenant_id;

-- ---------------------------------------------------------------------------
-- 4. Limpiar ADMIN_TALLER sin taller administrado.
-- ---------------------------------------------------------------------------
UPDATE auxilio_mecanico.usuarios u
SET tenant_id = NULL,
    fecha_actualizacion = NOW()
WHERE u.rol = 'ADMIN_TALLER'
  AND NOT EXISTS (
      SELECT 1
      FROM auxilio_mecanico.talleres t
      WHERE t.administrador_usuario_id = u.id
  )
  AND u.tenant_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 5. Mantener usuarios globales sin tenant.
-- ---------------------------------------------------------------------------
UPDATE auxilio_mecanico.usuarios
SET tenant_id = NULL,
    fecha_actualizacion = NOW()
WHERE rol IN ('CLIENTE', 'SUPERADMIN')
  AND tenant_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 6. Actualizar asignaciones_servicio.tenant_id segun el taller asignado.
-- ---------------------------------------------------------------------------
UPDATE auxilio_mecanico.asignaciones_servicio a
SET tenant_id = t.tenant_id,
    fecha_actualizacion = NOW()
FROM auxilio_mecanico.talleres t
WHERE a.taller_id = t.id
  AND a.tenant_id IS DISTINCT FROM t.tenant_id;

COMMIT;

-- =============================================================================
-- SELECTs de validacion
-- Ejecutar manualmente antes/despues segun corresponda.
-- =============================================================================

-- Tenants creados por esta migracion.
-- SELECT id, nombre, slug, estado, fecha_creacion
-- FROM auxilio_mecanico.tenants
-- WHERE slug = 'default' OR slug LIKE 'taller-%'
-- ORDER BY id;

-- Talleres por tenant. Debe haber un tenant taller-{id} por cada taller.
-- SELECT
--     t.id AS taller_id,
--     t.nombre AS taller_nombre,
--     t.tenant_id,
--     tenant.slug AS tenant_slug,
--     tenant.nombre AS tenant_nombre
-- FROM auxilio_mecanico.talleres t
-- JOIN auxilio_mecanico.tenants tenant ON tenant.id = t.tenant_id
-- ORDER BY t.id;

-- ADMIN_TALLER con tenant correcto segun taller administrado.
-- SELECT
--     u.id AS usuario_id,
--     u.correo_electronico,
--     u.tenant_id AS usuario_tenant_id,
--     t.id AS taller_id,
--     t.tenant_id AS taller_tenant_id,
--     tenant.slug AS tenant_slug
-- FROM auxilio_mecanico.usuarios u
-- JOIN auxilio_mecanico.talleres t ON t.administrador_usuario_id = u.id
-- LEFT JOIN auxilio_mecanico.tenants tenant ON tenant.id = u.tenant_id
-- WHERE u.rol = 'ADMIN_TALLER'
-- ORDER BY u.id;

-- ADMIN_TALLER con taller pero tenant NULL o distinto al del taller.
-- Debe devolver 0 filas despues de la migracion.
-- SELECT
--     u.id AS usuario_id,
--     u.correo_electronico,
--     u.tenant_id AS usuario_tenant_id,
--     t.id AS taller_id,
--     t.tenant_id AS taller_tenant_id
-- FROM auxilio_mecanico.usuarios u
-- JOIN auxilio_mecanico.talleres t ON t.administrador_usuario_id = u.id
-- WHERE u.rol = 'ADMIN_TALLER'
--   AND u.tenant_id IS DISTINCT FROM t.tenant_id
-- ORDER BY u.id;

-- ADMIN_TALLER sin taller administrado.
-- Deben quedar con tenant_id NULL despues de la migracion.
-- SELECT
--     u.id,
--     u.correo_electronico,
--     u.tenant_id
-- FROM auxilio_mecanico.usuarios u
-- WHERE u.rol = 'ADMIN_TALLER'
--   AND NOT EXISTS (
--       SELECT 1
--       FROM auxilio_mecanico.talleres t
--       WHERE t.administrador_usuario_id = u.id
--   )
-- ORDER BY u.id;

-- Asignaciones con tenant distinto al tenant del taller asignado.
-- Debe devolver 0 filas despues de la migracion.
-- SELECT
--     a.id AS asignacion_id,
--     a.incidente_id,
--     a.taller_id,
--     a.tenant_id AS asignacion_tenant_id,
--     t.tenant_id AS taller_tenant_id
-- FROM auxilio_mecanico.asignaciones_servicio a
-- JOIN auxilio_mecanico.talleres t ON t.id = a.taller_id
-- WHERE a.tenant_id IS DISTINCT FROM t.tenant_id
-- ORDER BY a.id;

-- Usuarios globales que no deben tener tenant.
-- Debe devolver 0 filas despues de la migracion.
-- SELECT id, correo_electronico, rol, tenant_id
-- FROM auxilio_mecanico.usuarios
-- WHERE rol IN ('CLIENTE', 'SUPERADMIN')
--   AND tenant_id IS NOT NULL
-- ORDER BY id;
