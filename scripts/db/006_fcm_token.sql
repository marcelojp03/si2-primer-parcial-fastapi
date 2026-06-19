-- Migration 006: FCM token para push notifications

ALTER TABLE auxilio_mecanico.usuarios
  ADD COLUMN IF NOT EXISTS fcm_token TEXT NULL;

COMMENT ON COLUMN auxilio_mecanico.usuarios.fcm_token IS 'Firebase Cloud Messaging token para push notifications';
