"""Optional SQLAlchemy session factory."""
import os
APP_DB_DSN = os.environ.get("APP_DB_DSN", "postgresql://user:pass@localhost:5432/referrals")
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _engine = create_engine(APP_DB_DSN, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
except Exception:
    _engine, _SessionLocal = None, None
def get_sqlalchemy_session():
    if _SessionLocal is None:
        raise ImportError("SQLAlchemy not installed.")
    return _SessionLocal()
