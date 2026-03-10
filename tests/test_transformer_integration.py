"""End-to-end transformer: raw sheet -> dim_entity + fact_snapshot + fact_timeseries.

Validates Pydantic validation, SCD Type 2 entity management, version numbering,
and timeseries persistence in one integrated flow.
"""

from datetime import datetime

from src.db.models.raw_layer import FileMetadataTbl, RawSheetTbl
from src.db.models.warehouse_layer import DimEntity, FactSnapshot, FactTimeseries
from src.pipeline.transform import RawToWarehouseTransformer


def _raw_assessment():
    """Minimal valid assessment JSON matching what raw.sheet.assessment stores."""
    return {
        "Rated entity": ["Acme Corp"],
        "CorporateSector": ["Corporates"],
        "Country of origin": ["Germany"],
        "Reporting Currency/Units": ["EUR"],
        "Accounting principles": ["IFRS"],
        "End of business year": ["December"],
        "Business risk profile": ["BBB+"],
        "Financial risk profile": ["BB"],
        "Leverage": ["BB+"],
        "Interest cover": ["BBB"],
        "Cash flow cover": ["BBB-"],
        "Liquidity": ["+1 notch"],
        "Segmentation criteria": ["Corporate"],
        "Rating methodologies applied": ["General Corporate Rating Methodology"],
        "Industry risk": [
            {"Steel": {"Industry risk score": "BBB", "Industry weight": "1.0"}}
        ],
    }


def _raw_timeseries():
    return {"Revenue": {"2022": 100.0, "2023": 200.0, "2024E": 300.0}}


class TestFullTransformPipeline:
    """A single raw sheet is transformed into warehouse dimension and fact tables."""

    def test_creates_entity_snapshot_and_timeseries(self, db_session, sample_file_meta):
        """A valid raw sheet produces a dim_entity, fact_snapshot,
        and timeseries rows."""
        raw = RawSheetTbl(
            file_id=sample_file_meta.id,
            assessment=_raw_assessment(),
            timeseries=_raw_timeseries(),
            was_processed=False,
        )
        db_session.add(raw)
        db_session.flush()

        result = RawToWarehouseTransformer(db_session).transform(raw, sample_file_meta)

        assert result.success is True
        assert raw.was_processed is True

        entity = db_session.query(DimEntity).filter_by(entity_name="Acme Corp").first()
        assert entity is not None
        assert entity.is_current is True
        assert entity.corporate_sector == "Corporates"

        snap = (
            db_session.query(FactSnapshot)
            .filter_by(file_id=sample_file_meta.id)
            .first()
        )
        assert snap.version_number == 1
        assert snap.business_risk_profile == "BBB+"

        ts = (
            db_session.query(FactTimeseries)
            .filter_by(snapshot_id=snap.snapshot_id)
            .all()
        )
        assert len(ts) == 3
        estimates = [t for t in ts if t.is_estimate]
        assert len(estimates) == 1
        assert estimates[0].year == 2024

    def test_validation_failure_returns_errors(self, db_session, sample_file_meta):
        """Invalid data (e.g. empty entity name) is rejected with error details."""
        raw = RawSheetTbl(
            file_id=sample_file_meta.id,
            assessment={"Rated entity": [""]},
            timeseries={},
            was_processed=False,
        )
        db_session.add(raw)
        db_session.flush()

        result = RawToWarehouseTransformer(db_session).transform(raw, sample_file_meta)

        assert result.success is False
        assert len(result.errors) > 0


class TestSCDType2EntityVersioning:
    """Company metadata changes trigger SCD Type 2: old row is closed, new row opens."""

    def test_metadata_change_creates_new_entity_version(self, db_session):
        """When a company's country changes, a new dim_entity row is created."""
        meta1 = FileMetadataTbl(
            fname="f1.xlsm", ctime=datetime(2024, 1, 1), sha3_256="a" * 64
        )
        meta2 = FileMetadataTbl(
            fname="f2.xlsm", ctime=datetime(2024, 6, 1), sha3_256="b" * 64
        )
        db_session.add_all([meta1, meta2])
        db_session.flush()

        raw1 = RawSheetTbl(
            file_id=meta1.id,
            assessment=_raw_assessment(),
            timeseries=_raw_timeseries(),
            was_processed=False,
        )
        db_session.add(raw1)
        db_session.flush()

        transformer = RawToWarehouseTransformer(db_session)
        transformer.transform(raw1, meta1)

        assessment2 = _raw_assessment()
        assessment2["Country of origin"] = ["France"]
        raw2 = RawSheetTbl(
            file_id=meta2.id,
            assessment=assessment2,
            timeseries=_raw_timeseries(),
            was_processed=False,
        )
        db_session.add(raw2)
        db_session.flush()

        result = transformer.transform(raw2, meta2)
        assert result.success is True

        entities = db_session.query(DimEntity).filter_by(entity_name="Acme Corp").all()
        assert len(entities) == 2
        old = [e for e in entities if not e.is_current][0]
        new = [e for e in entities if e.is_current][0]
        assert old.country == "Germany"
        assert old.valid_to == datetime(2024, 6, 1)
        assert new.country == "France"

    def test_unchanged_metadata_reuses_entity(self, db_session):
        """Identical metadata across files keeps one dim_entity;
        snapshots are versioned."""
        meta1 = FileMetadataTbl(
            fname="f1.xlsm", ctime=datetime(2024, 1, 1), sha3_256="c" * 64
        )
        meta2 = FileMetadataTbl(
            fname="f2.xlsm", ctime=datetime(2024, 6, 1), sha3_256="d" * 64
        )
        db_session.add_all([meta1, meta2])
        db_session.flush()

        raw1 = RawSheetTbl(
            file_id=meta1.id,
            assessment=_raw_assessment(),
            timeseries=_raw_timeseries(),
            was_processed=False,
        )
        raw2 = RawSheetTbl(
            file_id=meta2.id,
            assessment=_raw_assessment(),
            timeseries=_raw_timeseries(),
            was_processed=False,
        )
        db_session.add_all([raw1, raw2])
        db_session.flush()

        transformer = RawToWarehouseTransformer(db_session)
        transformer.transform(raw1, meta1)
        transformer.transform(raw2, meta2)

        entities = db_session.query(DimEntity).filter_by(entity_name="Acme Corp").all()
        assert len(entities) == 1

        snaps = db_session.query(FactSnapshot).all()
        assert len(snaps) == 2
        assert snaps[1].version_number == 2
