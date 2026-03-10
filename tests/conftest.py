"""Shared test fixtures.

Uses an in-memory SQLite database with schema names stripped from the ORM
models so that PostgreSQL-specific ``CREATE SCHEMA`` is not needed.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models.base import Base

# Import all models so they register with Base.metadata
from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl  # noqa: F401
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries  # noqa: F401

_schemas_stripped = False


def _strip_schemas(base):
    """Remove schema qualifiers from all tables (for SQLite compat). Idempotent."""
    global _schemas_stripped
    if _schemas_stripped:
        return
    for table in base.metadata.tables.values():
        table.schema = None
    _schemas_stripped = True


@pytest.fixture()
def db_engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    _strip_schemas(Base)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """Yield a session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def sample_entity(db_session) -> DimEntity:
    """Insert and return a single DimEntity row."""
    entity = DimEntity(
        entity_name="Acme Corp",
        corporate_sector="Corporates",
        country="Germany",
        currency="EUR",
        accounting_principles="IFRS",
        fiscal_year_end_month="December",
        valid_from=datetime(2024, 1, 1),
        is_current=True,
    )
    db_session.add(entity)
    db_session.flush()
    return entity


@pytest.fixture()
def sample_file_meta(db_session) -> FileMetadataTbl:
    """Insert and return a FileMetadataTbl row."""
    meta = FileMetadataTbl(
        fname="test_file.xlsm",
        ctime=datetime(2024, 6, 15, 10, 0, 0),
        sha3_256="a" * 64,
    )
    db_session.add(meta)
    db_session.flush()
    return meta


@pytest.fixture()
def sample_snapshot(db_session, sample_entity, sample_file_meta) -> FactSnapshot:
    """Insert and return a FactSnapshot linked to sample entity and file."""
    snap = FactSnapshot(
        entity_key=sample_entity.entity_key,
        file_id=sample_file_meta.id,
        snapshot_date=datetime(2024, 6, 15),
        version_number=1,
        business_risk_profile="BBB+",
        financial_risk_profile="BB",
        leverage="BB+",
        interest_cover="BBB",
        cash_flow_cover="BBB-",
        liquidity_adjustment="+1 notch",
        segmentation_criteria="Corporate",
        rating_methodologies_applied=["General Corporate Rating Methodology"],
        industry_risks=[{"industry_name": "Steel", "risk_score": "BBB", "weight": 1.0}],
    )
    db_session.add(snap)
    db_session.flush()
    return snap


# ---------------------------------------------------------------------------
# FastAPI test client — no lifespan (no scheduler, no real DB init)
# ---------------------------------------------------------------------------


def _build_test_app() -> FastAPI:
    """Build a FastAPI app identical to the real one but without the lifespan."""
    from src.api.routes import companies, snapshots, uploads

    @asynccontextmanager
    async def _noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=_noop_lifespan)
    test_app.include_router(companies.router)
    test_app.include_router(snapshots.router)
    test_app.include_router(uploads.router)

    return test_app


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden."""
    from src.api.dependencies import get_db

    app = _build_test_app()

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
