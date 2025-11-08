import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Get the project root directory (where .env is located)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    # Snowflake
    snowflake_user: str
    snowflake_password: str
    snowflake_account: str
    snowflake_database: str = "TEAM_SERO"
    snowflake_schema: str = "PUBLIC"
    snowflake_warehouse: str
    
    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@teamsero.tech"

    # Gemini API
    GEMINI_API_KEY: str = None  # Allow it to be optional for development

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(f"[DEBUG] Loaded GEMINI_API_KEY: {'[SET]' if self.GEMINI_API_KEY else '[NOT SET]'}")
    
    # OA Configuration
    oa_threshold: float = 0.85
    oa_base_url: str = "https://teamsero.tech/oa"
    
    # Judge0 Configuration
    judge0_url: str = "https://judge0-ce.p.rapidapi.com"
    judge0_api_key: str = ""
    judge0_rapidapi_host: str = "judge0-ce.p.rapidapi.com"
    
    # JWT Authentication
    jwt_secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    class Config:
        env_file = str(PROJECT_ROOT / ".env")  # Construct path to .env file
        case_sensitive = False


# Debug the env file path
env_path = str(PROJECT_ROOT / ".env")
print(f"[DEBUG] Loading .env from: {env_path}")
print(f"[DEBUG] File exists: {os.path.exists(env_path)}")

settings = Settings(_env_file=env_path)