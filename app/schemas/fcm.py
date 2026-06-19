from pydantic import BaseModel, Field


class FCMTokenCreate(BaseModel):
    fcm_token: str = Field(..., min_length=10, description="Firebase Cloud Messaging device token")
