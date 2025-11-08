from pydantic_settings import BaseSettings


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
        env_file = ".env"
        case_sensitive = False


settings = Settings()

