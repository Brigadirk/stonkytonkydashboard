#!/usr/bin/env python3
"""Illustrative revenue errors at fixed cutoffs, without an analyst leaderboard."""
import csv
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select_at_cutoff(forecasts, outcome, horizon, maximum_age=90):
    cutoff = date.fromisoformat(outcome["earnings_release_date"]) - timedelta(days=horizon)
    selected = {}
    for row in forecasts:
        if row["company_id"] != outcome["company_id"] or row["fiscal_period"] != outcome["fiscal_period"] or row["metric"] != "revenue":
            continue
        if row["observation_type"] != "individual_analyst_forecast" or row["ranking_status"] != "unscored_availability_and_actuals_unreconciled" or not row["forecaster"]:
            continue
        if row["currency"] != outcome["currency"] or row["unit"] != outcome["unit"] or not row["report_date"]:
            continue
        report_date = date.fromisoformat(row["report_date"])
        # Exact publication times are unverified: same-day reports are excluded.
        if not cutoff - timedelta(days=maximum_age) <= report_date < cutoff:
            continue
        key = row["forecaster"], row["firm"]
        previous = selected.get(key)
        if previous is None or row["report_date"] > previous["report_date"]:
            selected[key] = row
        elif row["report_date"] == previous["report_date"] and row["value"] != previous["value"]:
            raise ValueError(f"Conflicting same-date forecasts for {key}; manual review needed")
    return cutoff, list(selected.values())


def main():
    with (ROOT / "data/collected_forecasts.csv").open(newline="") as f:
        forecasts = list(csv.DictReader(f))
    with (ROOT / "data/issuer_outcomes.csv").open(newline="") as f:
        outcomes = [row for row in csv.DictReader(f) if row["metric"] == "revenue"]
    rows = []
    for outcome in outcomes:
        for horizon in (180, 365):
            cutoff, chosen = select_at_cutoff(forecasts, outcome, horizon)
            for forecast in chosen:
                predicted, actual = Decimal(forecast["value"]), Decimal(outcome["value"])
                error = predicted - actual
                rows.append(dict(company_id=outcome["company_id"], fiscal_period=outcome["fiscal_period"], forecaster=forecast["forecaster"], firm=forecast["firm"],
                                 horizon_days=horizon, cutoff_date=cutoff.isoformat(), report_date=forecast["report_date"], report_age_at_cutoff_days=(cutoff - date.fromisoformat(forecast["report_date"])).days,
                                 forecast_revenue_KRW=str(predicted), actual_revenue_KRW=str(actual), signed_error_KRW=str(error), absolute_error_pct=str((abs(error) / actual * 100).quantize(Decimal("0.0001"))),
                                 observation_id=forecast["observation_id"], outcome_id=outcome["outcome_id"], forecast_source_url=forecast["source_url"], actual_source_url=outcome["source_url"],
                                 actual_result_version=outcome["result_version"], consensus_available="false", comparison_status="illustrative_printed_date_assumption_not_an_accuracy_ranking"))
    if not rows:
        raise ValueError("No comparable revenue pairs found under the pilot filters")
    with (ROOT / "data/revenue_pilot.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} illustrative pairs across {len({(r['company_id'],r['fiscal_period']) for r in rows})} company-years. No ranks assigned.")


if __name__ == "__main__":
    main()
