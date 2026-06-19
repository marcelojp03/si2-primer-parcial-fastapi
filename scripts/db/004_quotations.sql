-- Migration 004: Cotizaciones (presupuestos) en asignaciones_servicio
-- Agrega columnas para que el taller emita una cotización y el cliente la apruebe/rechace.

ALTER TABLE auxilio_mecanico.asignaciones_servicio
  ADD COLUMN IF NOT EXISTS estado_cotizacion VARCHAR(20) NULL,
  ADD COLUMN IF NOT EXISTS descripcion_cotizacion TEXT NULL,
  ADD COLUMN IF NOT EXISTS tiempo_estimado_reparacion_min INTEGER NULL;

COMMENT ON COLUMN auxilio_mecanico.asignaciones_servicio.estado_cotizacion IS 'PENDIENTE | APROBADO | RECHAZADO';
COMMENT ON COLUMN auxilio_mecanico.asignaciones_servicio.descripcion_cotizacion IS 'Descripción del trabajo a realizar (lo que el taller propone)';
COMMENT ON COLUMN auxilio_mecanico.asignaciones_servicio.tiempo_estimado_reparacion_min IS 'Tiempo estimado de reparación en minutos';
