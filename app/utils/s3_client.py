"""Cliente S3 async para evidencias del sistema (imágenes, audios, documentos).

Operaciones disponibles:
  upload_file(file_bytes, s3_key, content_type, metadata) → str (clave)
  download_file(s3_key) → bytes | None
  delete_file(s3_key) → bool
  generate_presigned_url(s3_key, expiration) → str | None

Las llamadas boto3 son síncronas pero se ejecutan en un thread-pool para no
bloquear el event loop de asyncio.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from functools import partial

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cliente boto3 (lazy singleton) — las credenciales se leen del entorno o
# del rol IAM asignado (App Runner / EC2 / ECS).
# ---------------------------------------------------------------------------
_s3: object | None = None


def _get_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    return _s3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_key(folder: str, filename: str) -> str:
    """
    Construye una S3 key con timestamp y UUID para evitar colisiones.

    Ejemplo: evidencias/incidente-42/2026-04-29T15-02-33Z_8f2c0c7a.jpg
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    unique = str(uuid.uuid4())[:8]
    return f"{folder}/{timestamp}_{unique}_{filename}"


def _sanitize_metadata(text: str) -> str:
    """Convierte texto a ASCII puro para metadatos S3 (no acepta no-ASCII)."""
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
        "ü": "u",
        "Ü": "U",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("ascii", errors="ignore").decode("ascii")


# ---------------------------------------------------------------------------
# Operaciones síncronas (llamadas internamente por los wrappers async)
# ---------------------------------------------------------------------------


def _sync_upload(
    file_bytes: bytes,
    s3_key: str,
    content_type: str,
    metadata: dict[str, str],
    bucket: str,
) -> str:
    """Sube bytes a S3. Lanza excepción en caso de error."""
    client = _get_client()
    safe_meta = {k: _sanitize_metadata(v) for k, v in (metadata or {}).items()}
    client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
        Metadata=safe_meta,
    )
    return s3_key


def _sync_download(s3_key: str, bucket: str) -> bytes | None:
    """Descarga objeto de S3 y devuelve sus bytes."""
    client = _get_client()
    response = client.get_object(Bucket=bucket, Key=s3_key)
    return response["Body"].read()


def _sync_delete(s3_key: str, bucket: str) -> None:
    """Elimina objeto de S3."""
    client = _get_client()
    client.delete_object(Bucket=bucket, Key=s3_key)


def _sync_presigned_url(s3_key: str, bucket: str, expiration: int) -> str:
    """Genera URL prefirmada para lectura temporal."""
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expiration,
    )


# ---------------------------------------------------------------------------
# API pública async
# ---------------------------------------------------------------------------


async def upload_file(
    file_bytes: bytes,
    s3_key: str,
    content_type: str = "application/octet-stream",
    metadata: dict[str, str] | None = None,
    bucket: str | None = None,
) -> str:
    """
    Sube un archivo a S3 de forma asíncrona.

    Args:
        file_bytes: Contenido del archivo.
        s3_key: Clave destino en el bucket (usar _build_key() para generarla).
        content_type: MIME type del archivo (e.g. "image/jpeg", "audio/mpeg").
        metadata: Metadatos adicionales (solo ASCII; se sanitizan automáticamente).
        bucket: Bucket S3. Si no se especifica, usa settings.AWS_S3_BUCKET.

    Returns:
        La clave S3 donde fue guardado el archivo.

    Raises:
        RuntimeError: Si la subida falla.
    """
    _bucket = bucket or settings.AWS_S3_BUCKET
    loop = asyncio.get_event_loop()
    try:
        key = await loop.run_in_executor(
            None,
            partial(_sync_upload, file_bytes, s3_key, content_type, metadata or {}, _bucket),
        )
        logger.info("S3 upload OK: %s/%s (%d bytes)", _bucket, key, len(file_bytes))
        return key
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 upload FAILED: %s/%s — %s", _bucket, s3_key, exc)
        raise RuntimeError(f"Error subiendo archivo a S3: {exc}") from exc


async def download_file(
    s3_key: str,
    bucket: str | None = None,
) -> bytes | None:
    """
    Descarga un archivo de S3.

    Returns:
        Bytes del archivo, o None si no existe / error.
    """
    _bucket = bucket or settings.AWS_S3_BUCKET
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, partial(_sync_download, s3_key, _bucket))
        logger.info("S3 download OK: %s/%s (%d bytes)", _bucket, s3_key, len(data))
        return data
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 download FAILED: %s/%s — %s", _bucket, s3_key, exc)
        return None


async def delete_file(
    s3_key: str,
    bucket: str | None = None,
) -> bool:
    """
    Elimina un archivo de S3.

    Returns:
        True si se eliminó correctamente, False si hubo error.
    """
    _bucket = bucket or settings.AWS_S3_BUCKET
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, partial(_sync_delete, s3_key, _bucket))
        logger.info("S3 delete OK: %s/%s", _bucket, s3_key)
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 delete FAILED: %s/%s — %s", _bucket, s3_key, exc)
        return False


async def generate_presigned_url(
    s3_key: str,
    expiration: int = 3600,
    bucket: str | None = None,
) -> str | None:
    """
    Genera una URL prefirmada para acceso temporal de lectura.

    Args:
        s3_key: Clave del objeto en S3.
        expiration: Segundos de validez (default: 1 hora).
        bucket: Bucket S3. Si no se especifica, usa settings.AWS_S3_BUCKET.

    Returns:
        URL prefirmada como string, o None si falla.
    """
    _bucket = bucket or settings.AWS_S3_BUCKET
    loop = asyncio.get_event_loop()
    try:
        url = await loop.run_in_executor(
            None,
            partial(_sync_presigned_url, s3_key, _bucket, expiration),
        )
        return url
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 presigned URL FAILED: %s/%s — %s", _bucket, s3_key, exc)
        return None


# ---------------------------------------------------------------------------
# Utilidad de conveniencia para construir la key antes de subir
# ---------------------------------------------------------------------------


def build_evidence_key(incidente_id: int, filename: str) -> str:
    """
    Genera la key S3 para una evidencia de incidente.

    Ejemplo: evidencias/42/2026-04-29T15-02-33Z_8f2c0c7a_foto.jpg
    """
    return _build_key(f"evidencias/{incidente_id}", filename)
