"""Application configuration"""

import os
from datetime import timedelta
from urllib.parse import quote_plus


def _load_dotenv():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            os.environ.setdefault(key, value)


_load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Remote Metrics Central API configuration
METRICS_CENTRAL_BASE_URL = os.getenv("METRICS_CENTRAL_BASE_URL", "http://localhost:9000")
METRICS_CENTRAL_TOKEN = os.getenv("METRICS_CENTRAL_TOKEN", "demo-secret-token")
METRICS_CENTRAL_ADMIN_TOKEN = os.getenv("METRICS_CENTRAL_ADMIN_TOKEN", "admin-demo-token")


def get_database_url() -> str:
    """Build Azure SQL database URL from discrete DB_* environment variables."""
    db_server = os.getenv("DB_SERVER")
    db_database = os.getenv("DB_DATABASE")
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_server, db_database, db_username, db_password]):
        raise RuntimeError(
            "Missing Azure SQL settings. Required: DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD."
        )

    db_port = os.getenv("DB_PORT", "1433")
    db_driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    db_encrypt = os.getenv("DB_ENCRYPT", "yes")
    db_trust_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "no")
    db_timeout = os.getenv("DB_CONNECTION_TIMEOUT", "30")

    username_enc = quote_plus(db_username)
    password_enc = quote_plus(db_password)
    driver_enc = quote_plus(db_driver)

    return (
        f"mssql+pyodbc://{username_enc}:{password_enc}@{db_server}:{db_port}/{db_database}"
        f"?driver={driver_enc}"
        f"&Encrypt={db_encrypt}"
        f"&TrustServerCertificate={db_trust_cert}"
        f"&Connection+Timeout={db_timeout}"
    )
