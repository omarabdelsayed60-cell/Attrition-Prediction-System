from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import settings
from src.utils.logger import logger
from src.database.models import Base
from src.domain.exceptions import DatabaseConnectionError

def create_sqlserver_database_if_not_exists():
    """Attempts to create the target database on SQL Server if it does not exist yet."""
    driver_encoded = settings.DB_DRIVER.replace(" ", "+")
    trust_cert = "Yes" if settings.DB_TRUST_SERVER_CERTIFICATE else "No"
    
    if settings.DB_USE_WINDOWS_AUTH:
        master_url = f"mssql+pyodbc://@{settings.DB_SERVER}/master?driver={driver_encoded}&trusted_connection=yes&TrustServerCertificate={trust_cert}"
    else:
        master_url = f"mssql+pyodbc://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_SERVER}/master?driver={driver_encoded}&TrustServerCertificate={trust_cert}"
        
    master_engine = create_engine(master_url, isolation_level="AUTOCOMMIT")
    with master_engine.connect() as conn:
        conn.execute(text(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{settings.DB_NAME}') CREATE DATABASE [{settings.DB_NAME}]"))
    master_engine.dispose()
    logger.info(f"Database [{settings.DB_NAME}] verified/created on Microsoft SQL Server.")

def get_engine():
    """
    Creates and initializes the SQLAlchemy engine.
    Tries primary connection (SQL Server via Windows Auth or SA), auto-creates missing DB on SQL Server,
    and falls back gracefully to SQLite if SQL Server service is stopped.
    """
    try:
        url = settings.database_url
        logger.info(f"Connecting to primary database using engine strategy: {settings.DB_ENGINE}")
        
        if settings.DB_ENGINE.lower() == "sqlserver":
            # Auto-create database if it doesn't exist on SQL Server yet
            try:
                create_sqlserver_database_if_not_exists()
            except Exception as db_create_err:
                logger.warning(f"Note on SQL Server DB creation check: {str(db_create_err)}")

            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
            # Test connectivity
            with engine.connect() as conn:
                pass
            logger.info("Successfully connected to Microsoft SQL Server database.")
            return engine
        else:
            # SQLite configuration
            engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                echo=False
            )
            logger.info(f"Successfully connected to SQLite database at {settings.SQLITE_DB_PATH}")
            return engine
            
    except Exception as e:
        logger.warning(f"Failed to connect to primary database ({settings.DB_ENGINE}): {str(e)}")
        logger.info("Attempting automatic fallback to local SQLite database for development continuity...")
        
        try:
            fallback_path = settings.BASE_DIR / settings.SQLITE_DB_PATH
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            fallback_url = f"sqlite:///{fallback_path}"
            
            fallback_engine = create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
            logger.info(f"Fallback SQLite connection established at {fallback_path}")
            return fallback_engine
        except Exception as fallback_error:
            logger.error(f"Critical: SQLite fallback also failed: {str(fallback_error)}")
            raise DatabaseConnectionError(
                message="Unable to establish database connection to SQL Server or SQLite fallback.",
                details=str(fallback_error)
            )

# Create singleton engine instance
engine = get_engine()

# Create SessionLocal class factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Ensures all registered SQLAlchemy tables exist in the target database.
    Creates missing tables automatically.
    """
    try:
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during schema initialization: {str(e)}")
        raise DatabaseConnectionError("Failed to initialize database schema", details=str(e))

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency and context provider for database sessions.
    Yields an active database session and guarantees closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
