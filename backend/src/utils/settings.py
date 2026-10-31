from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")

    DB_CONNECTION:str
    SECRET_KEY:str
    ALGORITHM:str
    EXP_TIME:int
    REFRESH_EXP_TIME:int
    APP_ENV: str = "production"
    MOCK_PAYMENT_WEBHOOK_SECRET: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

settings=Settings()
