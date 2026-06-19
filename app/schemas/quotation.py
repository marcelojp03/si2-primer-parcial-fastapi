from pydantic import BaseModel, Field


class QuotationCreate(BaseModel):
    estimated_cost: float = Field(..., ge=0, description="Costo estimado de la reparación")
    estimated_completion_minutes: int = Field(..., ge=1, description="Tiempo estimado de reparación en minutos")
    quotation_description: str = Field(..., min_length=10, description="Descripción del trabajo a realizar")


class QuotationRespond(BaseModel):
    status: str = Field(..., pattern=r"^(APROBADO|RECHAZADO)$")


class QuotationRead(BaseModel):
    estimated_cost: float | None = None
    estimated_completion_minutes: int | None = None
    quotation_description: str | None = None
    quotation_status: str | None = None

    model_config = {"from_attributes": True}
