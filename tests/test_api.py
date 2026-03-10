"""API: browse companies, query snapshots, and track uploads."""

from src.db.models.warehouse_layer import FactTimeseries

# -- /companies ---------------------------------------------------------------


class TestCompaniesAPI:
    """Analysts can browse all rated companies, look up a specific one by ID,
    view the full rating history across versions, and compare companies side-by-side."""

    def test_no_companies_yet(self, client):
        assert client.get("/companies/").json() == []

    def test_rated_companies_are_listed(self, client, sample_entity):
        data = client.get("/companies/").json()
        assert len(data) == 1
        assert data[0]["entity_name"] == "Acme Corp"

    def test_company_can_be_looked_up_by_id(self, client, sample_entity):
        resp = client.get(f"/companies/{sample_entity.entity_key}")
        assert resp.status_code == 200
        assert resp.json()["entity_name"] == "Acme Corp"

    def test_unknown_company_id_returns_404(self, client):
        assert client.get("/companies/999").status_code == 404

    def test_all_rating_versions_for_a_company_are_accessible(
        self, client, sample_snapshot
    ):
        data = client.get(f"/companies/{sample_snapshot.entity_key}/versions").json()
        assert len(data) == 1
        assert data[0]["version_number"] == 1

    def test_financial_history_for_a_company_is_accessible(
        self, client, sample_snapshot, db_session
    ):
        db_session.add(
            FactTimeseries(
                snapshot_id=sample_snapshot.snapshot_id,
                entity_key=sample_snapshot.entity_key,
                metric_name="Revenue",
                year=2022,
                value=100.0,
            )
        )
        db_session.flush()

        data = client.get(f"/companies/{sample_snapshot.entity_key}/history").json()
        assert len(data) == 1
        assert data[0]["points"][0]["metric_name"] == "Revenue"

    def test_multiple_companies_can_be_compared_side_by_side(
        self, client, sample_snapshot
    ):
        """The compare endpoint returns the latest snapshot
        for each requested company."""
        data = client.get(
            "/companies/compare",
            params={"company_ids": str(sample_snapshot.entity_key)},
        ).json()
        assert len(data) == 1
        assert data[0]["entity_name"] == "Acme Corp"

    def test_comparison_can_be_scoped_to_a_specific_date(self, client, sample_snapshot):
        resp = client.get(
            "/companies/compare",
            params={
                "company_ids": str(sample_snapshot.entity_key),
                "as_of_date": "2024-12-31",
            },
        )
        assert resp.status_code == 200

    def test_compare_rejects_non_numeric_company_ids(self, client):
        assert (
            client.get("/companies/compare", params={"company_ids": "abc"}).status_code
            == 400
        )


# -- /snapshots ---------------------------------------------------------------


class TestSnapshotsAPI:
    """A snapshot is a full credit assessment at a point in time.
    Analysts can filter snapshots by industry sector or date range."""

    def test_snapshots_can_be_listed(self, client, sample_snapshot):
        assert len(client.get("/snapshots/").json()) == 1

    def test_snapshot_detail_shows_full_assessment(self, client, sample_snapshot):
        data = client.get(f"/snapshots/{sample_snapshot.snapshot_id}").json()
        assert data["business_risk_profile"] == "BBB+"

    def test_unknown_snapshot_id_returns_404(self, client):
        assert client.get("/snapshots/999").status_code == 404

    def test_latest_snapshot_per_company_is_accessible(self, client, sample_snapshot):
        data = client.get("/snapshots/latest").json()
        assert len(data) == 1
        assert data[0]["version_number"] == 1

    def test_snapshots_can_be_filtered_by_sector(self, client, sample_snapshot):
        assert (
            len(client.get("/snapshots/", params={"sector": "Corporates"}).json()) == 1
        )
        assert (
            len(client.get("/snapshots/", params={"sector": "NonExistent"}).json()) == 0
        )

    def test_snapshots_can_be_filtered_by_date_range(self, client, sample_snapshot):
        data = client.get(
            "/snapshots/", params={"from_date": "2024-01-01", "to_date": "2024-12-31"}
        ).json()
        assert len(data) == 1

    def test_malformed_date_filter_returns_400(self, client):
        assert (
            client.get("/snapshots/", params={"from_date": "not-a-date"}).status_code
            == 400
        )


# -- /uploads -----------------------------------------------------------------


class TestUploadsAPI:
    """Every uploaded file is tracked. Once processed, it is linked to the resulting
    company assessment so analysts can trace ratings back to the source file."""

    def test_uploaded_files_are_listed(self, client, sample_file_meta):
        assert len(client.get("/uploads/").json()) == 1

    def test_uploaded_file_can_be_retrieved_by_id(self, client, sample_file_meta):
        data = client.get(f"/uploads/{sample_file_meta.id}").json()
        assert data["fname"] == "test_file.xlsm"

    def test_unknown_file_id_returns_404(self, client):
        assert client.get("/uploads/999").status_code == 404

    def test_upload_count_is_tracked(self, client, sample_file_meta):
        assert client.get("/uploads/stats").json()["total_uploads"] == 1

    def test_processed_file_shows_assessment_and_version(self, client, sample_snapshot):
        """After processing, the file record links to the
        company and the assigned version number."""
        data = client.get(f"/uploads/{sample_snapshot.file_id}/details").json()
        assert data["entity_name"] == "Acme Corp"
        assert data["version_number"] == 1

    def test_unprocessed_file_has_no_assessment_yet(self, client, sample_file_meta):
        """A file that hasn't been processed yet shows no linked rating snapshot."""
        data = client.get(f"/uploads/{sample_file_meta.id}/details").json()
        assert data["snapshot_id"] is None
