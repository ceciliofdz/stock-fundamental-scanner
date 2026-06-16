from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # API Keys
    marketaux_api_key: str = Field(alias="MARKETAUX_API_KEY")
    finnhub_api_key: str = Field(alias="FINNHUB_API_KEY")
    alpha_vantage_api_key: str = Field(default="", alias="ALPHA_VANTAGE_API_KEY")
    
    # SEC EDGAR Requirements
    sec_user_agent: str = Field(alias="SEC_USER_AGENT")

    
    # Scanner Settings
    output_dir: Path = Field(default=Path("output"), alias="OUTPUT_DIR")
    timezone: str = Field(default="Europe/Madrid", alias="TIMEZONE")
    lookback_hours_news: int = Field(default=36, alias="LOOKBACK_HOURS_NEWS")
    lookback_hours_filings: int = Field(default=48, alias="LOOKBACK_HOURS_FILINGS")
    watchlist_path: Path = Field(default=Path("config/watchlist.yaml"), alias="WATCHLIST_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    return Settings()
