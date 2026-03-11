# Sample API Outputs

All examples are actual responses from the running API after ingesting `corporates_A_1.xlsm`, `corporates_A_2.xlsm`, `corporates_B_1.xlsm`, `corporates_B_2.xlsm`, `corporates_B_3.xlsm`.

---

## 1. GET /companies

```bash
curl localhost:8000/companies
```

```json
[
  {
    "entity_key": 1,
    "entity_name": "Company A",
    "corporate_sector": "Personal & Household Goods",
    "country": "Federal Republic of Germany",
    "currency": "EUR",
    "accounting_principles": "IFRS",
    "fiscal_year_end_month": "December",
    "valid_from": "2026-03-09T14:36:17.602756"
  },
  {
    "entity_key": 3,
    "entity_name": "Company B",
    "corporate_sector": "Automobiles & Parts",
    "country": "Swiss Confederation",
    "currency": "CHF",
    "accounting_principles": "IFRS",
    "fiscal_year_end_month": "May",
    "valid_from": "2026-03-10T15:20:09.778332"
  }
]
```

## 2. GET /companies/{id}

```bash
curl localhost:8000/companies/1
```

```json
{
  "entity_key": 1,
  "entity_name": "Company A",
  "corporate_sector": "Personal & Household Goods",
  "country": "Federal Republic of Germany",
  "currency": "EUR",
  "accounting_principles": "IFRS",
  "fiscal_year_end_month": "December",
  "valid_from": "2026-03-09T14:36:17.602756",
  "valid_to": null,
  "is_current": true
}
```

## 3. GET /companies/{id}/versions

```bash
curl localhost:8000/companies/1/versions
```

```json
[
  {
    "snapshot_id": 1,
    "entity_key": 1,
    "entity_name": "Company A",
    "file_id": 1,
    "snapshot_date": "2026-03-09T14:36:17.602756",
    "version_number": 1,
    "business_risk_profile": "B",
    "blended_industry_risk_profile": "A",
    "competitive_positioning": "B+",
    "market_share": "B+",
    "diversification": "B+",
    "operating_profitability": "B",
    "sector_factor_1": "B-",
    "sector_factor_2": null,
    "financial_risk_profile": "CC",
    "leverage": "CCC",
    "interest_cover": "B-",
    "cash_flow_cover": "CCC",
    "liquidity_adjustment": "-2 notches",
    "segmentation_criteria": "EBITDA contribution",
    "rating_methodologies_applied": [
      "General Corporate Rating Methodology"
    ],
    "industry_risks": [
      {
        "industry_name": "Consumer Products: Non-Discretionary",
        "risk_score": "BBB",
        "weight": 1
      }
    ]
  },
  {
    "snapshot_id": 2,
    "entity_key": 1,
    "entity_name": "Company A",
    "file_id": 3,
    "snapshot_date": "2026-03-09T20:20:08.429438",
    "version_number": 2,
    "business_risk_profile": "B+",
    "blended_industry_risk_profile": "A",
    "competitive_positioning": "B+",
    "market_share": "BB-",
    "diversification": "B+",
    "operating_profitability": "BB-",
    "sector_factor_1": "B-",
    "sector_factor_2": null,
    "financial_risk_profile": "C",
    "leverage": "CCC",
    "interest_cover": "B-",
    "cash_flow_cover": "CCC",
    "liquidity_adjustment": "-2 notches",
    "segmentation_criteria": "EBITDA contribution",
    "rating_methodologies_applied": [
      "General Corporate Rating Methodology",
      "Consumer Products Rating Methodology"
    ],
    "industry_risks": [
      {
        "industry_name": "Consumer Products: Non-Discretionary",
        "risk_score": "A",
        "weight": 1
      }
    ]
  }
]
```

## 4. GET /companies/{id}/history

Returns time-series data grouped by snapshot version. Truncated for brevity (full response has 60 points per version across 6 metrics x 10 years).

```bash
curl localhost:8000/companies/1/history
```

```json
[
    {
        "snapshot_id": 1,
        "version_number": 1,
        "snapshot_date": "2026-03-09T14:36:17.602756",
        "points": [
            {
                "metric_name": "Liquidity",
                "year": 2018,
                "is_estimate": false,
                "value": 4.862
            },
            {
                "metric_name": "Liquidity",
                "year": 2019,
                "is_estimate": false,
                "value": 4.862
            },
            {
                "metric_name": "Liquidity",
                "year": 2025,
                "is_estimate": true,
                "value": 21.53185742374875
            },
            {
                "metric_name": "Scope-adjusted debt/EBITDA",
                "year": 2024,
                "is_estimate": false,
                "value": 36.79999999999997
            },
            {
                "metric_name": "Scope-adjusted FFO/debt",
                "year": 2023,
                "is_estimate": false,
                "value": 27.32900000000001
            },
            {
                "metric_name": "Scope-adjusted loan/value",
                "year": 2023,
                "is_estimate": false,
                "value": null
            }
        ]
    },
    {
        "snapshot_id": 2,
        "version_number": 2,
        "snapshot_date": "2026-03-09T20:20:08.429438",
        "points": [
            {
                "metric_name": "Liquidity",
                "year": 2027,
                "is_estimate": true,
                "value": 21.53185742374875
            },
            {
                "metric_name": "Scope-adjusted FOCF/debt",
                "year": 2027,
                "is_estimate": true,
                "value": 4.862
            },
            {
                "metric_name": "Scope-adjusted loan/value",
                "year": 2027,
                "is_estimate": true,
                "value": 4.862
            }
        ]
    }
]
```

## 5. GET /companies/compare

Point-in-time comparison of multiple companies.

```bash
curl "localhost:8000/companies/compare?company_ids=1,2&as_of_date=2026-03-10"
```

```json
[
    {
        "snapshot_id": 2,
        "entity_key": 1,
        "entity_name": "Company A",
        "file_id": 3,
        "snapshot_date": "2026-03-09T20:20:08.429438",
        "version_number": 2,
        "business_risk_profile": "B+",
        "blended_industry_risk_profile": "A",
        "competitive_positioning": "B+",
        "market_share": "BB-",
        "diversification": "B+",
        "operating_profitability": "BB-",
        "sector_factor_1": "B-",
        "sector_factor_2": null,
        "financial_risk_profile": "C",
        "leverage": "CCC",
        "interest_cover": "B-",
        "cash_flow_cover": "CCC",
        "liquidity_adjustment": "-2 notches",
        "segmentation_criteria": "EBITDA contribution",
        "rating_methodologies_applied": [
            "General Corporate Rating Methodology",
            "Consumer Products Rating Methodology"
        ],
        "industry_risks": [
            {
                "industry_name": "Consumer Products: Non-Discretionary",
                "risk_score": "A",
                "weight": 1.0
            }
        ]
    },
    {
        "snapshot_id": 5,
        "entity_key": 3,
        "entity_name": "Company B",
        "file_id": 4,
        "snapshot_date": "2026-03-10T15:20:09.778332",
        "version_number": 1,
        "business_risk_profile": "BBB-",
        "blended_industry_risk_profile": "A",
        "competitive_positioning": "A+",
        "market_share": "BBB+",
        "diversification": "A-",
        "operating_profitability": "BB+",
        "sector_factor_1": "BBB+",
        "sector_factor_2": null,
        "financial_risk_profile": "BB",
        "leverage": "BB+",
        "interest_cover": "BBB+",
        "cash_flow_cover": "A-",
        "liquidity_adjustment": "+1 notch",
        "segmentation_criteria": "EBITDA contribution",
        "rating_methodologies_applied": [
            "Automotive and Commercial Vehicle Manufacturers Rating Methodology"
        ],
        "industry_risks": [
            {
                "industry_name": "Automotive Suppliers",
                "risk_score": "BBB",
                "weight": 0.25
            },
            {
                "industry_name": "Automotive and Commercial Vehicle Manufacturers",
                "risk_score": "BB",
                "weight": 0.75
            }
        ]
    }
]
```

## 6. GET /snapshots (with filters)

```bash
curl "localhost:8000/snapshots?country=Federal%20Republic%20of%20Germany"
```

```json
[
    {
        "snapshot_id": 2,
        "entity_key": 1,
        "entity_name": "Company A",
        "file_id": 3,
        "snapshot_date": "2026-03-09T20:20:08.429438",
        "version_number": 2,
        "business_risk_profile": "B+",
        "financial_risk_profile": "C"
    },
    {
        "snapshot_id": 1,
        "entity_key": 1,
        "entity_name": "Company A",
        "file_id": 1,
        "snapshot_date": "2026-03-09T14:36:17.602756",
        "version_number": 1,
        "business_risk_profile": "B",
        "financial_risk_profile": "CC"
    }
]
```

## 7. GET /snapshots/latest

```bash
curl localhost:8000/snapshots/latest
```

```json
[
    {
        "snapshot_id": 2,
        "entity_key": 1,
        "entity_name": "Company A",
        "file_id": 3,
        "snapshot_date": "2026-03-09T20:20:08.429438",
        "version_number": 2,
        "business_risk_profile": "B+",
        "blended_industry_risk_profile": "A",
        "competitive_positioning": "B+",
        "market_share": "BB-",
        "diversification": "B+",
        "operating_profitability": "BB-",
        "sector_factor_1": "B-",
        "sector_factor_2": null,
        "financial_risk_profile": "C",
        "leverage": "CCC",
        "interest_cover": "B-",
        "cash_flow_cover": "CCC",
        "liquidity_adjustment": "-2 notches",
        "segmentation_criteria": "EBITDA contribution",
        "rating_methodologies_applied": [
            "General Corporate Rating Methodology",
            "Consumer Products Rating Methodology"
        ],
        "industry_risks": [
            {
                "industry_name": "Consumer Products: Non-Discretionary",
                "risk_score": "A",
                "weight": 1.0
            }
        ]
    },
    {
        "snapshot_id": 4,
        "entity_key": 2,
        "entity_name": "Company B",
        "file_id": 5,
        "snapshot_date": "2026-03-09T20:26:35.370633",
        "version_number": 2,
        "business_risk_profile": "BBB-",
        "blended_industry_risk_profile": "A",
        "competitive_positioning": "A+",
        "market_share": "BBB+",
        "diversification": "A-",
        "operating_profitability": "BB+",
        "sector_factor_1": "BBB+",
        "sector_factor_2": null,
        "financial_risk_profile": "BB",
        "leverage": "BB+",
        "interest_cover": "BBB+",
        "cash_flow_cover": "A-",
        "liquidity_adjustment": "+1 notch",
        "segmentation_criteria": "EBITDA contribution",
        "rating_methodologies_applied": [
            "Automotive and Commercial Vehicle Manufacturers Rating Methodology"
        ],
        "industry_risks": [
            {
                "industry_name": "Automotive Suppliers",
                "risk_score": "BBB",
                "weight": 0.25
            },
            {
                "industry_name": "Automotive and Commercial Vehicle Manufacturers",
                "risk_score": "BB",
                "weight": 0.75
            }
        ]
    },
    {
        "snapshot_id": 5,
        "entity_key": 3,
        "entity_name": "Company B",
        "file_id": 4,
        "snapshot_date": "2026-03-10T15:20:09.778332",
        "version_number": 1,
        "business_risk_profile": "BBB-",
        "blended_industry_risk_profile": "A",
        "competitive_positioning": "A+",
        "market_share": "BBB+",
        "diversification": "A-",
        "operating_profitability": "BB+",
        "sector_factor_1": "BBB+",
        "sector_factor_2": null,
        "financial_risk_profile": "BB",
        "leverage": "BB+",
        "interest_cover": "BBB+",
        "cash_flow_cover": "A-",
        "liquidity_adjustment": "+1 notch",
        "segmentation_criteria": "EBITDA contribution",
        "rating_methodologies_applied": [
            "Automotive and Commercial Vehicle Manufacturers Rating Methodology"
        ],
        "industry_risks": [
            {
                "industry_name": "Automotive Suppliers",
                "risk_score": "BBB",
                "weight": 0.25
            },
            {
                "industry_name": "Automotive and Commercial Vehicle Manufacturers",
                "risk_score": "BB",
                "weight": 0.75
            }
        ]
    }
]
```

## 8. GET /snapshots/{id}

```bash
curl localhost:8000/snapshots/1
```

```json
{
    "snapshot_id": 1,
    "entity_key": 1,
    "entity_name": "Company A",
    "file_id": 1,
    "snapshot_date": "2026-03-09T14:36:17.602756",
    "version_number": 1,
    "business_risk_profile": "B",
    "blended_industry_risk_profile": "A",
    "competitive_positioning": "B+",
    "market_share": "B+",
    "diversification": "B+",
    "operating_profitability": "B",
    "sector_factor_1": "B-",
    "sector_factor_2": null,
    "financial_risk_profile": "CC",
    "leverage": "CCC",
    "interest_cover": "B-",
    "cash_flow_cover": "CCC",
    "liquidity_adjustment": "-2 notches",
    "segmentation_criteria": "EBITDA contribution",
    "rating_methodologies_applied": [
        "General Corporate Rating Methodology"
    ],
    "industry_risks": [
        {
            "industry_name": "Consumer Products: Non-Discretionary",
            "risk_score": "BBB",
            "weight": 1.0
        }
    ]
}
```

## 9. GET /uploads

```bash
curl localhost:8000/uploads
```

```json
[
    {
        "id": 4,
        "fname": "corporates_B_3.xlsm",
        "sha3_256": "2e9226b574853769be86b6e1c723334446636c2bc7aafcbd9571b2123cd476a2",
        "ctime": "2026-03-10T15:20:09.778332"
    },
    {
        "id": 5,
        "fname": "corporates_B_2.xlsm",
        "sha3_256": "fec33f0191c8321360fda434d48737a2b173c4751594082b5f5db85c5174f998",
        "ctime": "2026-03-09T20:26:35.370633"
    },
    {
        "id": 2,
        "fname": "corporates_B_1.xlsm",
        "sha3_256": "4770492ac213e0a3f3bfae441d09684e53c8d43271113545b74da1186160fff0",
        "ctime": "2026-03-09T20:26:35.364633"
    },
    {
        "id": 3,
        "fname": "corporates_A_1.xlsm",
        "sha3_256": "bf939b1e35867d4cdee397ae0e043acfc358f1307427a2d6b03a8af717c548d1",
        "ctime": "2026-03-09T20:20:08.429438"
    },
    {
        "id": 1,
        "fname": "corporates_A_2.xlsm",
        "sha3_256": "5ad8bc8de406d7c9a262d8bfe960b0a060cb25ba51ef7f827e3b823bd8ca05c3",
        "ctime": "2026-03-09T14:36:17.602756"
    }
]
```

## 10. GET /uploads/stats

```bash
curl localhost:8000/uploads/stats
```

```json
{
    "total_uploads": 5,
    "earliest_upload": "2026-03-09T14:36:17.602756",
    "latest_upload": "2026-03-10T15:20:09.778332"
}
```

## 11. GET /uploads/{id}/details

```bash
curl localhost:8000/uploads/1/details
```

```json
{
    "id": 1,
    "fname": "corporates_A_2.xlsm",
    "sha3_256": "5ad8bc8de406d7c9a262d8bfe960b0a060cb25ba51ef7f827e3b823bd8ca05c3",
    "ctime": "2026-03-09T14:36:17.602756",
    "snapshot_id": 1,
    "entity_name": "Company A",
    "version_number": 1
}
```

## 12. GET /uploads/{id}/file

```bash
curl -o downloaded.xlsm localhost:8000/uploads/1/file
```

Returns the original `.xlsm` file as a binary download (146,973 bytes) with headers:

```
content-type: text/plain; charset=utf-8
content-disposition: attachment; filename="corporates_A_2.xlsm"
content-length: 146973
```

## 13. GET /companies/{id} (404 example)

```bash
curl localhost:8000/companies/999
```

```json
{"detail": "Company 999 not found"}
```

## 14. GET /uploads/{id}

```bash
curl localhost:8000/uploads/3
```

```json
{
    "id": 3,
    "fname": "corporates_A_1.xlsm",
    "sha3_256": "bf939b1e35867d4cdee397ae0e043acfc358f1307427a2d6b03a8af717c548d1",
    "ctime": "2026-03-09T20:20:08.429438"
}
```

---

## Pipeline Execution Log Example

```
INFO:     src.pipeline.scheduler - Pipeline scheduler started (interval=10000s)
DEBUG:    src.pipeline.orchestrator - Skipping corporates_A_2.xlsm - already ingested
DEBUG:    src.pipeline.orchestrator - Skipping corporates_B_1.xlsm - already ingested
DEBUG:    src.pipeline.orchestrator - Skipping corporates_A_1.xlsm - already ingested
DEBUG:    src.pipeline.orchestrator - Skipping corporates_B_3.xlsm - already ingested
DEBUG:    src.pipeline.orchestrator - Skipping corporates_B_2.xlsm - already ingested
```
