from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str
    model: str = "claude-opus-4-5"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
