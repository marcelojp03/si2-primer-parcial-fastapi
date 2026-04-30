from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "auxilio-mecanico-backend"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auxilio_mecanico"
    DB_SCHEMA: str = "auxilio_mecanico"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # AWS / S3
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "auxilio-mecanico-evidences"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.4-mini"

    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_FILE: str = "auxilio-mecanico-firebase.json"

    # VPAY
    VPAY_BASE_URL: str = "https://vpay.com.bo:7778/pro"
    VPAY_TOKEN: str = ""
    VPAY_DESTINATION_ACCOUNT: str = "selvi.lecaro"
    VPAY_BANK: str = "BMSC"
    VPAY_USER: str = "marcelojunior"
    VPAY_COMPANY: str = "1"
    VPAY_VERIFY_SSL: bool = True


settings = Settings()
