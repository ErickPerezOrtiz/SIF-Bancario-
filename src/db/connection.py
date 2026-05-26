"""Conexión a MySQL usando SQLAlchemy."""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        cfg = DB_CONFIG
        url = (
            f"mysql+mysqlconnector://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}?charset=utf8mb4"
        )
        _engine = create_engine(url, echo=False, pool_pre_ping=True, pool_size=5)
        logger.info("Motor MySQL conectado a %s:%s/%s", cfg['host'], cfg['port'], cfg['database'])
    return _engine


def get_connection():
    return get_engine().connect()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=None)


def get_session():
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    return SessionLocal()


def create_database_if_not_exists():
    """Crea la base de datos si no existe."""
    cfg = DB_CONFIG
    url_no_db = (
        f"mysql+mysqlconnector://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}?charset=utf8mb4"
    )
    tmp = create_engine(url_no_db)
    with tmp.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    tmp.dispose()
    logger.info("Base de datos '%s' lista.", cfg['database'])
