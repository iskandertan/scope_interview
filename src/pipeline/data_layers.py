from dataclasses import dataclass, field
import datetime

from sqlalchemy.orm import Session

from src.db.models.bronze_layer import FileMetadata, RawExcel

# TODO: tests for the presence of mandatory fields and their types
# TODO: do the data documentation here
# TODO: file name is confusing

# ---------------------------------------------------------------------------
# Source data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SrcFileMetadata:
    fname: str
    ctime: datetime.datetime
    sha3_256: str

    def to_orm(self) -> FileMetadata:
        return FileMetadata(fname=self.fname, ctime=self.ctime, sha3_256=self.sha3_256)

    def existing(self, session: Session) -> FileMetadata | None:
        # TODO: tests here
        """Check whether a record with the same sha3_256 already exists in the database."""
        return session.query(FileMetadata).filter_by(sha3_256=self.sha3_256).first()


@dataclass(frozen=True)
class SrcRawExcel:
    key_values: dict
    timeseries: dict
    was_processed: bool = field(default=False)

    def to_orm(self, file_id) -> RawExcel:
        return RawExcel(
            file_id=file_id,
            key_values=self.key_values,
            timeseries=self.timeseries,
            was_processed=self.was_processed,
        )


# ---------------------------------------------------------------------------
# Layer transformers
# ---------------------------------------------------------------------------


class RawToSilverTransformer:
    pass


class SilverToGoldTransformer:
    pass


# {
# "select * from raw.sheet s\ninner join file_uploads.file_metadata fm on s.file_id = fm.id\n": [
# 	{
# 		"file_id" : 1,
# 		"key_values" : "{\"Rated entity\": [\"Company A\"], \"CorporateSector\": [\"Personal & Household Goods\"], \"Rating methodologies applied\": [\"General Corporate Rating Methodology\"], \"Industry risk\": [{\"Consumer Products: Non-Discretionary\": {\"Industry risk score\": \"BBB\", \"Industry weight\": \"1\"}}], \"Segmentation criteria\": [\"EBITDA contribution\"], \"Reporting Currency\/Units\": [\"EUR\"], \"Country of origin\": [\"Federal Republic of Germany\"], \"Accounting principles\": [\"IFRS\"], \"End of business year\": [\"December\"], \"Business risk profile\": [\"B\"], \"(Blended) Industry risk profile\": [\"A\"], \"Competitive Positioning\": [\"B+\"], \"Market share\": [\"B+\"], \"Diversification\": [\"B+\"], \"Operating profitability\": [\"B\"], \"Sector\/company-specific factors (1)\": [\"B-\"], \"Sector\/company-specific factors (2)\": [], \"Financial risk profile\": [\"CC\"], \"Leverage\": [\"CCC\"], \"Interest cover\": [\"B-\"], \"Cash flow cover\": [\"CCC\"], \"Liquidity\": [\"-2 notches\"]}",
# 		"timeseries" : "{\"Scope-adjusted EBITDA interest cover\": {\"2018\": 27.32900000000001, \"2019\": 27.32900000000001, \"2020\": 27.32900000000001, \"2021\": 4.862, \"2022\": 4.862, \"2023\": 4.862, \"2024\": 36.79999999999997, \"2025E\": 36.79999999999997, \"2026E\": 18.4912526, \"2027E\": 18.4912526}, \"Scope-adjusted debt\/EBITDA\": {\"2018\": 18.4912526, \"2019\": 18.4912526, \"2020\": 18.4912526, \"2021\": 18.4912526, \"2022\": 18.4912526, \"2023\": 18.4912526, \"2024\": 36.79999999999997, \"2025E\": 36.79999999999997, \"2026E\": 18.4912526, \"2027E\": 18.4912526}, \"Scope-adjusted FFO\/debt\": {\"2018\": 22, \"2019\": 22, \"2020\": 22, \"2021\": 36.79999999999997, \"2022\": 36.79999999999997, \"2023\": 27.32900000000001, \"2024\": 29, \"2025E\": 29, \"2026E\": 29, \"2027E\": 8}, \"Scope-adjusted loan\/value\": {\"2018\": 27.32900000000001, \"2019\": 27.32900000000001, \"2020\": 27.32900000000001, \"2021\": 36.79999999999997, \"2022\": 36.79999999999997, \"2023\": \"No data\", \"2024\": 27.32900000000001, \"2025E\": 27.32900000000001, \"2026E\": 27.32900000000001, \"2027E\": 4.862}, \"Scope-adjusted FOCF\/debt\": {\"2018\": 21.53185742374875, \"2019\": 21.53185742374875, \"2020\": 21.53185742374875, \"2021\": 21.53185742374875, \"2022\": 4.862, \"2023\": 4.862, \"2024\": 4.862, \"2025E\": 4.862, \"2026E\": 4.862, \"2027E\": 4.862}, \"Liquidity\": {\"2018\": 4.862, \"2019\": 4.862, \"2020\": 4.862, \"2021\": 21.53185742374875, \"2022\": 21.53185742374875, \"2023\": 21.53185742374875, \"2024\": 21.53185742374875, \"2025E\": 21.53185742374875, \"2026E\": 21.53185742374875, \"2027E\": 23}}",
# 		"was_processed" : false,
# 		"id" : 1,
# 		"fname" : "corporates_A_2.xlsm",
# 		"ctime" : "2026-03-09T13:36:17.602Z",
# 		"sha3_256" : "5ad8bc8de406d7c9a262d8bfe960b0a060cb25ba51ef7f827e3b823bd8ca05c3"
# 	},
# 	{
# 		"file_id" : 2,
# 		"key_values" : "{\"Rated entity\": [\"Company B\"], \"CorporateSector\": [\"Automobiles & Parts\"], \"Rating methodologies applied\": [\"Automotive and Commercial Vehicle Manufacturers Rating Methodology\"], \"Industry risk\": [{\"Automotive Suppliers\": {\"Industry risk score\": \"BBB\", \"Industry weight\": \"0.15\"}}, {\"Automotive and Commercial Vehicle Manufacturers\": {\"Industry risk score\": \"BB\", \"Industry weight\": \"0.85\"}}], \"Segmentation criteria\": [\"EBITDA contribution\"], \"Reporting Currency\/Units\": [\"CHF\"], \"Country of origin\": [\"Swiss Confederation\"], \"Accounting principles\": [\"IFRS\"], \"End of business year\": [\"March\"], \"Business risk profile\": [\"BBB\"], \"(Blended) Industry risk profile\": [\"A+\"], \"Competitive Positioning\": [\"A+\"], \"Market share\": [\"BBB+\"], \"Diversification\": [\"A-\"], \"Operating profitability\": [\"BB+\"], \"Sector\/company-specific factors (1)\": [\"BBB+\"], \"Sector\/company-specific factors (2)\": [], \"Financial risk profile\": [\"BB+\"], \"Leverage\": [\"BB+\"], \"Interest cover\": [\"A-\"], \"Cash flow cover\": [\"A-\"], \"Liquidity\": [\"+1 notch\"]}",
# 		"timeseries" : "{\"Scope-adjusted EBITDA interest cover\": {\"2019\": 1, \"2020\": 2, \"2021\": 2, \"2022\": 2, \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted debt\/EBITDA\": {\"2019\": 1, \"2020\": 2, \"2021\": 2, \"2022\": 2, \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted FFO\/debt\": {\"2019\": 1, \"2020\": 2, \"2021\": 2, \"2022\": 2, \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted loan\/value\": {\"2019\": 1, \"2020\": 2, \"2021\": 2, \"2022\": 2, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted FOCF\/debt\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Liquidity\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}}",
# 		"was_processed" : false,
# 		"id" : 2,
# 		"fname" : "corporates_B_1.xlsm",
# 		"ctime" : "2026-03-09T19:26:35.364Z",
# 		"sha3_256" : "4770492ac213e0a3f3bfae441d09684e53c8d43271113545b74da1186160fff0"
# 	},
# 	{
# 		"file_id" : 3,
# 		"key_values" : "{\"Rated entity\": [\"Company A\"], \"CorporateSector\": [\"Personal & Household Goods\"], \"Rating methodologies applied\": [\"General Corporate Rating Methodology\", \"Consumer Products Rating Methodology\"], \"Industry risk\": [{\"Consumer Products: Non-Discretionary\": {\"Industry risk score\": \"A\", \"Industry weight\": \"1\"}}], \"Segmentation criteria\": [\"EBITDA contribution\"], \"Reporting Currency\/Units\": [\"EUR\"], \"Country of origin\": [\"Federal Republic of Germany\"], \"Accounting principles\": [\"IFRS\"], \"End of business year\": [\"December\"], \"Business risk profile\": [\"B+\"], \"(Blended) Industry risk profile\": [\"A\"], \"Competitive Positioning\": [\"B+\"], \"Market share\": [\"BB-\"], \"Diversification\": [\"B+\"], \"Operating profitability\": [\"BB-\"], \"Sector\/company-specific factors (1)\": [\"B-\"], \"Sector\/company-specific factors (2)\": [], \"Financial risk profile\": [\"C\"], \"Leverage\": [\"CCC\"], \"Interest cover\": [\"B-\"], \"Cash flow cover\": [\"CCC\"], \"Liquidity\": [\"-2 notches\"]}",
# 		"timeseries" : "{\"Scope-adjusted EBITDA interest cover\": {\"2018\": 27.32900000000001, \"2019\": 27.32900000000001, \"2020\": 27.32900000000001, \"2021\": 4.862, \"2022\": 4.862, \"2023\": 4.862, \"2024\": 36.79999999999997, \"2025E\": 36.79999999999997, \"2026E\": 18.4912526, \"2027E\": 18.4912526}, \"Scope-adjusted debt\/EBITDA\": {\"2018\": 18.4912526, \"2019\": 18.4912526, \"2020\": 18.4912526, \"2021\": 18.4912526, \"2022\": 18.4912526, \"2023\": 18.4912526, \"2024\": 36.79999999999997, \"2025E\": 36.79999999999997, \"2026E\": 18.4912526, \"2027E\": 18.4912526}, \"Scope-adjusted FFO\/debt\": {\"2018\": 27.32900000000001, \"2019\": 27.32900000000001, \"2020\": 27.32900000000001, \"2021\": 36.79999999999997, \"2022\": 36.79999999999997, \"2023\": 27.32900000000001, \"2024\": 27.32900000000001, \"2025E\": 27.32900000000001, \"2026E\": 27.32900000000001, \"2027E\": 4.862}, \"Scope-adjusted loan\/value\": {\"2018\": 27.32900000000001, \"2019\": 27.32900000000001, \"2020\": 27.32900000000001, \"2021\": 36.79999999999997, \"2022\": 36.79999999999997, \"2023\": \"No data\", \"2024\": 27.32900000000001, \"2025E\": 27.32900000000001, \"2026E\": 27.32900000000001, \"2027E\": 4.862}, \"Scope-adjusted FOCF\/debt\": {\"2018\": 21.53185742374875, \"2019\": 21.53185742374875, \"2020\": 21.53185742374875, \"2021\": 21.53185742374875, \"2022\": 4.862, \"2023\": 4.862, \"2024\": 4.862, \"2025E\": 4.862, \"2026E\": 4.862, \"2027E\": 4.862}, \"Liquidity\": {\"2018\": 4.862, \"2019\": 4.862, \"2020\": 4.862, \"2021\": 21.53185742374875, \"2022\": 21.53185742374875, \"2023\": 21.53185742374875, \"2024\": 21.53185742374875, \"2025E\": 21.53185742374875, \"2026E\": 21.53185742374875, \"2027E\": 21.53185742374875}}",
# 		"was_processed" : false,
# 		"id" : 3,
# 		"fname" : "corporates_A_1.xlsm",
# 		"ctime" : "2026-03-09T19:20:08.429Z",
# 		"sha3_256" : "bf939b1e35867d4cdee397ae0e043acfc358f1307427a2d6b03a8af717c548d1"
# 	},
# 	{
# 		"file_id" : 4,
# 		"key_values" : "{\"Rated entity\": [\"Company B\"], \"CorporateSector\": [\"Automobiles & Parts\"], \"Rating methodologies applied\": [\"Automotive and Commercial Vehicle Manufacturers Rating Methodology\"], \"Industry risk\": [{\"Automotive Suppliers\": {\"Industry risk score\": \"BBB\", \"Industry weight\": \"0.25\"}}, {\"Automotive and Commercial Vehicle Manufacturers\": {\"Industry risk score\": \"BB\", \"Industry weight\": \"0.75\"}}], \"Segmentation criteria\": [\"EBITDA contribution\"], \"Reporting Currency\/Units\": [\"CHF\"], \"Country of origin\": [\"Swiss Confederation\"], \"Accounting principles\": [\"IFRS\"], \"End of business year\": [\"March\"], \"Business risk profile\": [\"BBB-\"], \"(Blended) Industry risk profile\": [\"A\"], \"Competitive Positioning\": [\"A+\"], \"Market share\": [\"BBB+\"], \"Diversification\": [\"A-\"], \"Operating profitability\": [\"BB+\"], \"Sector\/company-specific factors (1)\": [\"BBB+\"], \"Sector\/company-specific factors (2)\": [], \"Financial risk profile\": [\"BB\"], \"Leverage\": [\"BB+\"], \"Interest cover\": [\"BBB+\"], \"Cash flow cover\": [\"A-\"], \"Liquidity\": [\"+1 notch\"]}",
# 		"timeseries" : "{\"Scope-adjusted EBITDA interest cover\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": \"No data\", \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted debt\/EBITDA\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted FFO\/debt\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 2, \"2024\": 2, \"2025\": 2, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted loan\/value\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Scope-adjusted FOCF\/debt\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}, \"Liquidity\": {\"2019\": 1, \"2020\": 1, \"2021\": 1, \"2022\": 1, \"2023\": 3, \"2024\": 3, \"2025\": 3, \"2026E\": 3, \"2027E\": 3, \"2028E\": 3}}",
# 		"was_processed" : false,
# 		"id" : 4,
# 		"fname" : "corporates_B_2.xlsm",
# 		"ctime" : "2026-03-09T19:26:35.370Z",
# 		"sha3_256" : "fec33f0191c8321360fda434d48737a2b173c4751594082b5f5db85c5174f998"
# 	}
# ]}
