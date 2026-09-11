#!/usr/bin/env python3
"""Compare explicitly compatible EPS forecasts with initial issuer releases.

Public report dates remain an availability assumption. No analyst rank or
cross-basis pooling follows from this selected sample.
"""
import argparse
from collections import Counter
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = date(2026, 9, 10)
BASES = {"reported_diluted"}  # Adjusted broker EPS needs an explicit definition match.


def split_factor(company, basis_date, splits, as_of=CUTOFF):
    return math.prod(float(row["ratio"]) for row in splits if row["company_id"] == company and basis_date < row["effective_date"] <= as_of.isoformat())


def compare(forecasts, outcomes, splits, max_age=90, as_of=CUTOFF):
    pairs, blocked = [], []
    for actual in outcomes:
        release = date.fromisoformat(actual["initial_release_date"])
        if release > as_of:
            continue
        for horizon in (90, 180, 365):
            cutoff = release - timedelta(days=horizon)
            candidates = [f for f in forecasts if f["company_id"] == actual["company_id"] and f["fiscal_period"] == actual["fiscal_period"] and f["currency"] == actual["currency"] and f["series_type"] == "individual_analyst_forecast"]
            compatible = [f for f in candidates if f["accounting_basis"] == actual["accounting_basis"] and f["accounting_basis"] in BASES and f["fiscal_period_end"] == actual["fiscal_period_end"]]
            eligible = [f for f in compatible if f["report_date"] < cutoff.isoformat() and f["available_date"] <= cutoff.isoformat() and 0 <= (cutoff - date.fromisoformat(f["model_date"] or f["report_date"])).days <= max_age]
            selected = {}
            for forecast in sorted(eligible, key=lambda f: (f["model_date"] or f["report_date"], f["available_date"], f["report_date"])):
                previous = selected.get(forecast["series_id"])
                if previous and (previous["model_date"] or previous["report_date"], previous["available_date"]) == (forecast["model_date"] or forecast["report_date"], forecast["available_date"]) and float(previous["eps"]) != float(forecast["eps"]):
                    raise ValueError("Conflicting forecast values at the same evaluation cutoff")
                selected[forecast["series_id"]] = forecast
            if not selected:
                reason = "No compatible EPS definition" if not compatible else "No sufficiently fresh forecast published before the fixed cutoff"
                blocked.append({"company_id":actual["company_id"],"fiscal_period":actual["fiscal_period"],"accounting_basis":actual["accounting_basis"],"horizon_days":horizon,"cutoff_date":cutoff.isoformat(),"reason":reason})
            for forecast in selected.values():
                estimated = float(forecast["eps"]) / split_factor(actual["company_id"], forecast["share_basis_date"], splits, as_of)
                realized = float(actual["value"]) / split_factor(actual["company_id"], actual["share_basis_date"], splits, as_of)
                error = estimated - realized
                if not all(math.isfinite(v) for v in (estimated, realized, error)):
                    raise ValueError("Non-finite normalized EPS")
                pairs.append({"company_id":actual["company_id"],"fiscal_period":actual["fiscal_period"],"fiscal_period_end":actual["fiscal_period_end"],"analyst":forecast["analyst"],"firm":forecast["firm"],"series_id":forecast["series_id"],"accounting_basis":forecast["accounting_basis"],"currency":actual["currency"],"horizon_days":horizon,"cutoff_date":cutoff.isoformat(),"report_date":forecast["report_date"],"model_date":forecast["model_date"],"initial_release_date":actual["initial_release_date"],"forecast_eps":estimated,"actual_eps":realized,"signed_error_eps":error,"absolute_error_eps":abs(error),"absolute_error_pct":100*abs(error)/abs(realized) if abs(realized)>0.01 else None,"observation_id":forecast["observation_id"],"outcome_id":actual["outcome_id"],"forecast_source_url":forecast["source_url"],"actual_source_url":actual["source_url"],"actual_definition":actual["definition"],"consensus_benchmark":None,"availability_basis":"printed_report_date_assumption","status":"illustrative_comparable_reported_eps_not_an_analyst_rank"})
    return pairs, blocked


def main(as_of=CUTOFF):
    outcomes=[]
    for path in sorted((ROOT/'data/collection').glob('*/issuer_eps_outcomes.csv')):
        with path.open() as handle:
            for row in csv.DictReader(handle):
                if any(token in row["validation_status"].lower() for token in ("quarantin", "unresolved", "conflict")):
                    continue
                artifact=ROOT/row["source_file"]
                if hashlib.sha256(artifact.read_bytes()).hexdigest()!=row["source_sha256"]:
                    raise ValueError(f"Issuer source hash mismatch: {artifact}")
                assert row["accounting_basis"] in {"reported_diluted","non_gaap_diluted"}, row
                assert row["unit"]==row["currency"]+"_per_share", row
                assert row["fiscal_period_end"] <= row["initial_release_date"], row
                assert row["share_basis_date"] <= row["initial_release_date"], row
                if row["initial_release_date"] > as_of.isoformat():
                    continue
                outcomes.append(row)
    keys=[(r['company_id'],r['fiscal_period'],r['accounting_basis']) for r in outcomes]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate initial issuer outcomes')
    with (ROOT/'data/market/forecast_panel.csv').open() as handle: forecasts=list(csv.DictReader(handle))
    with (ROOT/'data/market/splits.csv').open() as handle: splits=list(csv.DictReader(handle))
    pairs,blocked=compare(forecasts,outcomes,splits,as_of=as_of)
    result={"as_of":as_of.isoformat(),"horizons_days":[90,180,365],"horizon_definition":"Calendar days before the initial annual earnings release", "max_model_age_at_cutoff_days":90,"share_basis":"Both forecast and actual EPS normalized for subsequent stock splits through dataset cutoff", "eligible_basis":"Explicit reported diluted EPS, same issuer fiscal year and currency", "ranking_status":"Insufficient comparable coverage and contemporaneous consensus benchmarks; no ranks assigned", "outcomes":outcomes,"pairs":pairs,"blocked":blocked,"blocked_reason_counts":dict(Counter(r['reason'] for r in blocked))}
    (ROOT/'data/eps_pilot.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if pairs:
        with (ROOT/'data/eps_pilot.csv').open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=pairs[0]);writer.writeheader();writer.writerows(pairs)
    else:
        (ROOT/'data/eps_pilot.csv').unlink(missing_ok=True)
    print(json.dumps({"issuer_eps_outcomes":len(outcomes),"comparable_pairs":len(pairs),"blocked_company_year_horizons":len(blocked)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of',type=date.fromisoformat,default=CUTOFF)
    main(parser.parse_args().as_of)
