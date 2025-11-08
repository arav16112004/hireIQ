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
    oa_threshold: float = 0.90
    oa_base_url: str = "https://teamsero.tech/oa"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

