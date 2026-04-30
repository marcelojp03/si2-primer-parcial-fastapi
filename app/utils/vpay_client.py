import logging
from datetime import date

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

_PAYMENT_URL = "api/transactions/doPayment"
_STATUS_URL = "api/operations/statusQr"


def _headers() -> dict[str, str]:
    return {
        "Authorization": settings.VPAY_TOKEN,
        "Content-Type": "application/json",
    }


async def generate_qr(
    amount: float,
    gloss: str,
    expiration_date: date,
    additional_data: str,
) -> tuple[str, str]:
    """Llama a VPAY doPayment y retorna (id_qr, qr_base64)."""
    if not settings.VPAY_TOKEN:
        import base64
        import time

        demo_id = f"DEMO-{int(time.time())}"
        demo_text = f"PAGO DEMO\n{gloss}\nBs. {amount:.2f}\n{additional_data}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.qrserver.com/v1/create-qr-code/",
                params={"size": "300x300", "data": demo_text},
            )
            resp.raise_for_status()
            qr_base64 = base64.b64encode(resp.content).decode()
        logger.warning("VPAY_TOKEN no configurado — usando modo DEMO para QR")
        return demo_id, qr_base64

    payload = {
        "operation": "VTO041",
        "header": [
            {"attribute": "currency", "value": "BOB"},
            {"attribute": "gloss", "value": gloss},
            {"attribute": "amount", "value": f"{amount:.2f}"},
            {"attribute": "singleUse", "value": "true"},
            {"attribute": "expirationDate", "value": expiration_date.strftime("%Y-%m-%d")},
            {"attribute": "additionalData", "value": additional_data},
            {"attribute": "destinationAccountId", "value": settings.VPAY_DESTINATION_ACCOUNT},
            {"attribute": "bank", "value": settings.VPAY_BANK},
            {"attribute": "user", "value": settings.VPAY_USER},
            {"attribute": "company", "value": settings.VPAY_COMPANY},
        ],
        "detail": [{"items": []}],
    }

    async with httpx.AsyncClient(
        base_url=settings.VPAY_BASE_URL.rstrip('/') + '/',
        verify=settings.VPAY_VERIFY_SSL,
        timeout=30.0,
    ) as client:
        response = await client.put(_PAYMENT_URL, json=payload, headers=_headers())

    logger.info("VPAY doPayment status=%s body=%s", response.status_code, response.text[:300])
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con VPAY ({exc.response.status_code}): {exc.response.text[:200]}",
        ) from exc

    data = response.json()
    if data.get("status") != "OK":
        raise HTTPException(
            status_code=502,
            detail=f"VPAY doPayment error: {data.get('message') or data.get('menssage')}",
        )

    items = data["responseList"][0]["response"]
    id_qr = next(r["identificator"] for r in items if r["code"] == "idQr")
    qr_base64 = next(r["identificator"] for r in items if r["code"] == "QR")
    return id_qr, qr_base64


async def check_qr_status(id_qr: str) -> str:
    """Llama a VPAY statusQr. Retorna 'PEN' o 'PAG'."""
    if not settings.VPAY_TOKEN or id_qr.startswith("DEMO-"):
        return "PEN"  # modo demo: siempre pendiente

    payload = {"operation": id_qr}

    async with httpx.AsyncClient(
        base_url=settings.VPAY_BASE_URL.rstrip('/') + '/',
        verify=settings.VPAY_VERIFY_SSL,
        timeout=30.0,
    ) as client:
        response = await client.post(_STATUS_URL, json=payload, headers=_headers())

    logger.info("VPAY statusQr id_qr=%s status=%s body=%s", id_qr, response.status_code, response.text[:300])
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al comunicarse con VPAY ({exc.response.status_code}): {exc.response.text[:200]}",
        ) from exc

    data = response.json()
    if data.get("status") != "OK":
        raise HTTPException(
            status_code=502,
            detail=f"VPAY statusQr error: {data.get('message') or data.get('menssage')}",
        )

    items = data["responseList"][0]["response"]
    return next(r["identificator"] for r in items if r["code"] == "statusQr")
