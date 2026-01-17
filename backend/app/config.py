from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    database_name: str = "adaptive_tutor"

    # Auth0 (optional - set skip_auth=true for development)
    auth0_domain: str = ""
    auth0_api_audience: str = ""
    auth0_algorithms: str = "RS256"
    skip_auth: bool = True  # Set to False in production

    # Google Gemini AI (Vertex AI)
    gemini_api_key: str = ""  # Deprecated - using Vertex AI now
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
