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

settings=Settings()
