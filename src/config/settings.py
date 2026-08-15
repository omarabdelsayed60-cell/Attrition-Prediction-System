import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Determine project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Application Settings class powered by Pydantic.
    Loads and validates environment variables from .env file.
    """
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Config
    APP_NAME: str = "Enterprise Employee Attrition Prediction System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # SQL Server / Database Configuration
    DB_ENGINE: str = "sqlserver"  # "sqlserver" or "sqlite"
    DB_SERVER: str = "localhost"
    DB_NAME: str = "EmployeeAttritionDB"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "YourStrongPassword123!"
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_TRUST_SERVER_CERTIFICATE: bool = True
    DB_USE_WINDOWS_AUTH: bool = True  # Set True for Windows Authentication (default for local SSMS)
    SQLITE_DB_PATH: str = "data/attrition_system.db"

    # ML & Artifact Directories
    ARTIFACTS_DIR: str = "artifacts"
    MODEL_FILE_NAME: str = "model.joblib"
    PREPROCESSOR_FILE_NAME: str = "preprocessor.joblib"
    METRICS_FILE_NAME: str = "metrics.json"

    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 0.30
    RISK_THRESHOLD_HIGH: float = 0.60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"

    @property
    def BASE_DIR(self) -> Path:
        """Returns project root base directory path."""
        return BASE_DIR

    @property
    def database_url(self) -> str:
        """
        Constructs the SQLAlchemy connection URL dynamically based on DB_ENGINE setting.
        Supports Microsoft SQL Server (pyodbc) with automatic SQLite fallback.
        """
        if self.DB_ENGINE.lower() == "sqlserver":
            driver_encoded = self.DB_DRIVER.replace(" ", "+")
            trust_cert = "Yes" if self.DB_TRUST_SERVER_CERTIFICATE else "No"
            if self.DB_USE_WINDOWS_AUTH:
                return (
                    f"mssql+pyodbc://@{self.DB_SERVER}/{self.DB_NAME}"
                    f"?driver={driver_encoded}&trusted_connection=yes&TrustServerCertificate={trust_cert}"
                )
            else:
                return (
                    f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_NAME}"
                    f"?driver={driver_encoded}&TrustServerCertificate={trust_cert}"
                )
        else:
            # Fallback to local SQLite file
            sqlite_path = BASE_DIR / self.SQLITE_DB_PATH
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{sqlite_path}"

    @property
    def model_path(self) -> Path:
        """Returns resolved absolute path to trained model artifact."""
        return BASE_DIR / self.ARTIFACTS_DIR / self.MODEL_FILE_NAME

    @property
    def preprocessor_path(self) -> Path:
        """Returns resolved absolute path to preprocessor artifact."""
        return BASE_DIR / self.ARTIFACTS_DIR / self.PREPROCESSOR_FILE_NAME

    @property
    def metrics_path(self) -> Path:
        """Returns resolved absolute path to metrics report file."""
        return BASE_DIR / self.ARTIFACTS_DIR / self.METRICS_FILE_NAME

# Instantiate global settings object singleton
settings = Settings()
