from __future__ import annotations

import csv
import math
import random
import sqlite3
from pathlib import Path
from statistics import mean

BASE_RATE = 0.0425
RANDOM_SEED = 42
SIMULATIONS = 10_000

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
SQL_SCHEMA = ROOT / "sql" / "schema.sql"
DATA_FILE = DATA_DIR / "loan_applications.csv"
DB_FILE = OUTPUT_DIR / "loan_underwriting.db"
RESULTS_FILE = OUTPUT_DIR / "underwriting_results.csv"
DECISION_SUMMARY_FILE = OUTPUT_DIR / "decision_summary.csv"
RISK_CLASS_SUMMARY_FILE = OUTPUT_DIR / "risk_class_summary.csv"
MODEL_REPORT_FILE = OUTPUT_DIR / "model_report.md"

FIELDS = [
    "application_id",
    "customer_id",
    "loan_type",
    "loan_purpose",
    "loan_amount",
    "term_years",
    "annual_income",
    "monthly_fixed_expenses",
    "existing_debt",
    "existing_debt_monthly_payment",
    "employment_years",
    "credit_score",
    "credit_utilization",
    "active_credit_lines",
    "payment_remarks",
    "previous_defaults",
    "savings",
    "investments",
    "other_assets",
    "collateral_value",
    "collateral_type",
]


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def band_score(value: float, bands: list[tuple[float, float]], default: float) -> float:
    for threshold, score in bands:
        if value <= threshold:
            return score
    return default


def annuity_payment(principal: float, annual_rate: float, years: int) -> float:
    months = max(years * 12, 1)
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / months
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)


def generate_synthetic_applications() -> list[dict[str, object]]:
    rng = random.Random(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    purposes = {
        "mortgage": ["home_purchase", "home_refinance", "home_improvement"],
        "car": ["car_commute", "car_family", "car_luxury"],
        "consumer": ["debt_consolidation", "consumer_spending", "education", "emergency_expense"],
    }

    application_id = 1
    for loan_type in ["mortgage", "car", "consumer"]:
        for _ in range(40):
            if loan_type == "mortgage":
                annual_income = rng.randint(480_000, 1_650_000)
                loan_amount = rng.randint(1_500_000, 6_200_000)
                term_years = rng.randint(18, 30)
                ltv = rng.uniform(0.55, 1.03)
                collateral_value = loan_amount / ltv
                collateral_type = "residential_property"
                savings = rng.randint(80_000, 1_200_000)
                investments = rng.randint(0, 800_000)
                other_assets = rng.randint(0, 450_000)
                credit_score = int(clamp(rng.gauss(710, 70), 420, 850))
            elif loan_type == "car":
                annual_income = rng.randint(380_000, 1_150_000)
                loan_amount = rng.randint(90_000, 680_000)
                term_years = rng.randint(3, 8)
                ltv = rng.uniform(0.60, 1.20)
                collateral_value = loan_amount / ltv
                collateral_type = "vehicle"
                savings = rng.randint(15_000, 350_000)
                investments = rng.randint(0, 300_000)
                other_assets = rng.randint(0, 250_000)
                credit_score = int(clamp(rng.gauss(670, 85), 390, 840))
            else:
                annual_income = rng.randint(290_000, 980_000)
                loan_amount = rng.randint(20_000, 430_000)
                term_years = rng.randint(1, 7)
                collateral_value = 0
                collateral_type = "none"
                savings = rng.randint(0, 180_000)
                investments = rng.randint(0, 180_000)
                other_assets = rng.randint(0, 150_000)
                credit_score = int(clamp(rng.gauss(625, 95), 330, 820))

            existing_debt = rng.randint(0, int(annual_income * rng.uniform(0.2, 3.8)))
            existing_payment = existing_debt * rng.uniform(0.004, 0.012)
            monthly_income = annual_income / 12
            fixed_expenses = monthly_income * rng.uniform(0.28, 0.58)
            payment_remarks = int(rng.random() < (0.08 if loan_type != "consumer" else 0.15))
            previous_defaults = int(rng.random() < (0.04 if loan_type != "consumer" else 0.09))

            rows.append(
                {
                    "application_id": application_id,
                    "customer_id": f"C{application_id:04d}",
                    "loan_type": loan_type,
                    "loan_purpose": rng.choice(purposes[loan_type]),
                    "loan_amount": round(loan_amount, 2),
                    "term_years": term_years,
                    "annual_income": round(annual_income, 2),
                    "monthly_fixed_expenses": round(fixed_expenses, 2),
                    "existing_debt": round(existing_debt, 2),
                    "existing_debt_monthly_payment": round(existing_payment, 2),
                    "employment_years": round(rng.uniform(0.2, 14.0), 1),
                    "credit_score": credit_score,
                    "credit_utilization": round(rng.uniform(0.05, 0.98), 3),
                    "active_credit_lines": rng.randint(1, 9),
                    "payment_remarks": payment_remarks,
                    "previous_defaults": previous_defaults,
                    "savings": round(savings, 2),
                    "investments": round(investments, 2),
                    "other_assets": round(other_assets, 2),
                    "collateral_value": round(collateral_value, 2),
                    "collateral_type": collateral_type,
                }
            )
            application_id += 1

    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_database(rows: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if DB_FILE.exists():
        DB_FILE.unlink()
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript(SQL_SCHEMA.read_text(encoding="utf-8"))
        placeholders = ", ".join(["?"] * len(FIELDS))
        conn.executemany(
            f"INSERT INTO loan_applications ({', '.join(FIELDS)}) VALUES ({placeholders})",
            [[row[field] for field in FIELDS] for row in rows],
        )


def fetch_rows() -> list[dict[str, object]]:
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM regulatory_check ORDER BY application_id")]


def score_credit_history(row: dict[str, object]) -> float:
    credit_score = (float(row["credit_score"]) - 300) / 550 * 100
    utilization = band_score(float(row["credit_utilization"]), [(0.30, 100), (0.50, 80), (0.75, 55), (0.90, 30)], 10)
    clean_record = 100 - 35 * int(row["payment_remarks"]) - 50 * int(row["previous_defaults"])
    return clamp(0.65 * credit_score + 0.20 * utilization + 0.15 * clean_record)


def score_capacity(row: dict[str, object]) -> float:
    dti = float(row["dti_after_loan"])
    dti_score = band_score(dti, [(2.5, 100), (3.5, 80), (4.5, 60), (5.0, 40)], 10)

    employment_years = float(row["employment_years"])
    if employment_years >= 5:
        employment_score = 100
    elif employment_years >= 2:
        employment_score = 75
    elif employment_years >= 1:
        employment_score = 50
    else:
        employment_score = 25

    stress_rate = max(BASE_RATE + 0.03, 0.07)
    stressed_payment = annuity_payment(float(row["loan_amount"]), stress_rate, int(row["term_years"]))
    surplus = float(row["monthly_income"]) - float(row["monthly_fixed_expenses"]) - float(row["existing_debt_monthly_payment"]) - stressed_payment
    surplus_ratio = surplus / float(row["monthly_income"])
    surplus_score = band_score(surplus_ratio, [(0.0, 25), (0.05, 45), (0.15, 70), (0.25, 85)], 100)

    return clamp(0.45 * dti_score + 0.25 * employment_score + 0.30 * surplus_score)


def score_collateral(row: dict[str, object]) -> float:
    loan_type = str(row["loan_type"])
    if loan_type == "consumer" or row["ltv"] is None:
        return 15
    ltv = float(row["ltv"])
    if loan_type == "mortgage":
        return band_score(ltv, [(0.60, 100), (0.75, 85), (0.90, 60), (1.00, 25)], 0)
    return band_score(ltv, [(0.70, 90), (0.90, 70), (1.10, 45), (1.25, 15)], 0)


def score_capital(row: dict[str, object]) -> float:
    capital_to_loan = float(row["capital_to_loan"])
    liquidity_months = float(row["liquidity_months_before_loan"])
    capital_score = band_score(capital_to_loan, [(0.05, 20), (0.10, 45), (0.20, 70), (0.35, 90)], 100)
    liquidity_score = band_score(liquidity_months, [(1, 20), (3, 45), (6, 70), (12, 90)], 100)
    return clamp(0.70 * capital_score + 0.30 * liquidity_score)


def score_conditions(row: dict[str, object]) -> float:
    purpose_scores = {
        "home_purchase": 85,
        "home_refinance": 75,
        "home_improvement": 70,
        "car_commute": 75,
        "car_family": 70,
        "car_luxury": 45,
        "debt_consolidation": 60,
        "education": 65,
        "emergency_expense": 45,
        "consumer_spending": 30,
    }
    score = purpose_scores.get(str(row["loan_purpose"]), 50)
    score += {"mortgage": 10, "car": 0, "consumer": -15}[str(row["loan_type"])]
    if row["loan_type"] == "consumer" and int(row["term_years"]) > 5:
        score -= 25
    if row["loan_type"] == "car" and int(row["term_years"]) > 6:
        score -= 10
    return clamp(score)


def risk_class(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    if score >= 55:
        return "D"
    return "E"


def estimate_pd(final_score: float, loan_type: str) -> float:
    base_pd = 0.002 + 0.22 / (1 + math.exp((final_score - 55) / 7.5))
    multiplier = {"mortgage": 0.50, "car": 0.85, "consumer": 1.35}[loan_type]
    return min(base_pd * multiplier, 0.35)


def estimate_lgd(row: dict[str, object]) -> float:
    loan_type = str(row["loan_type"])
    if loan_type == "consumer":
        return 0.90
    haircut = 0.15 if loan_type == "mortgage" else 0.35
    recovery = float(row["collateral_value"]) * (1 - haircut)
    raw_lgd = (float(row["loan_amount"]) - recovery) / float(row["loan_amount"])
    minimum = 0.10 if loan_type == "mortgage" else 0.25
    return clamp(raw_lgd, minimum, 0.95)


def simulate_pricing(row: dict[str, object], final_score: float) -> dict[str, float]:
    loan_type = str(row["loan_type"])
    pd = estimate_pd(final_score, loan_type)
    lgd = estimate_lgd(row)
    rng = random.Random(RANDOM_SEED + int(row["application_id"]) * 17)

    losses = []
    for _ in range(SIMULATIONS):
        if rng.random() < pd:
            severity = clamp(rng.gauss(lgd, 0.18 * lgd + 0.04), 0.0, 1.0)
            exposure = rng.uniform(0.65, 1.00)
            losses.append(exposure * severity)
        else:
            losses.append(0.0)

    losses.sort()
    expected_loss = mean(losses)
    tail_loss = mean(losses[-max(1, SIMULATIONS // 100):])
    risk_margin = expected_loss + 0.12 * max(0.0, tail_loss - expected_loss)
    risk_margin = min(max(risk_margin, 0.0015), 0.25)
    product_margin = {"mortgage": 0.006, "car": 0.018, "consumer": 0.045}[loan_type]
    offered_rate = min(BASE_RATE + product_margin + risk_margin, 0.35)

    return {
        "estimated_pd": pd,
        "estimated_lgd": lgd,
        "expected_loss_rate": expected_loss,
        "tail_loss_rate": tail_loss,
        "risk_margin": risk_margin,
        "product_margin": product_margin,
        "offered_rate": offered_rate,
    }


def stress_test(row: dict[str, object], offered_rate: float) -> tuple[bool, float, float]:
    stressed_rate = max(offered_rate + 0.03, 0.07)
    stressed_payment = annuity_payment(float(row["loan_amount"]), stressed_rate, int(row["term_years"]))
    surplus = float(row["monthly_income"]) - float(row["monthly_fixed_expenses"]) - float(row["existing_debt_monthly_payment"]) - stressed_payment
    required_buffer = 0.05 * float(row["monthly_income"])
    return surplus >= required_buffer, stressed_rate, surplus


def make_decision(row: dict[str, object], final_score: float, passes_stress: bool) -> tuple[str, str]:
    if int(row["passes_debt_to_income_rule"]) == 0:
        return "Reject", "Debt above 5x income"
    if int(row["passes_mortgage_ltv_rule"]) == 0:
        return "Reject", "Mortgage LTV above 90%"
    if int(row["passes_consumer_term_rule"]) == 0:
        return "Reject", "Consumer loan term above 5 years"
    if not passes_stress:
        return "Reject", "Fails interest stress test"
    if final_score >= 70:
        return "Approve", "Strong enough 5C score and passes hard rules"
    if final_score >= 55:
        return "Manual review", "Borderline 5C score"
    return "Reject", "Weak 5C score"


def enrich(row: dict[str, object]) -> dict[str, object]:
    scores = {
        "credit_history": score_credit_history(row),
        "capacity": score_capacity(row),
        "collateral": score_collateral(row),
        "capital": score_capital(row),
        "conditions": score_conditions(row),
    }
    final_score = (
        scores["credit_history"] * 0.25
        + scores["capacity"] * 0.35
        + scores["collateral"] * 0.15
        + scores["capital"] * 0.15
        + scores["conditions"] * 0.10
    )
    pricing = simulate_pricing(row, final_score)
    passes_stress, stressed_rate, stress_surplus = stress_test(row, pricing["offered_rate"])
    decision, reason = make_decision(row, final_score, passes_stress)
    weakest = sorted(scores.items(), key=lambda item: item[1])[:2]

    output = dict(row)
    output.update({f"score_{name}": round(value, 2) for name, value in scores.items()})
    output.update({
        "final_score": round(final_score, 2),
        "risk_class": risk_class(final_score),
        "base_rate": BASE_RATE,
        "stressed_rate": round(stressed_rate, 5),
        "stress_surplus_monthly": round(stress_surplus, 2),
        "passes_interest_stress_test": int(passes_stress),
        "decision": decision,
        "decision_reason": reason,
        "weakest_components": "; ".join(f"{name}={score:.1f}" for name, score in weakest),
    })
    output.update({name: round(value, 5) for name, value in pricing.items()})
    return output


def summarize(rows: list[dict[str, object]], group_field: str) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault(str(row[group_field]), []).append(row)

    summary = []
    for group, items in sorted(groups.items()):
        priced = [float(row["offered_rate"]) for row in items if row["decision"] != "Reject"]
        summary.append({
            group_field: group,
            "applications": len(items),
            "approved": sum(row["decision"] == "Approve" for row in items),
            "manual_review": sum(row["decision"] == "Manual review" for row in items),
            "rejected": sum(row["decision"] == "Reject" for row in items),
            "avg_score": round(mean(float(row["final_score"]) for row in items), 2),
            "avg_offered_rate_non_rejected": round(mean(priced), 5) if priced else "",
        })
    return summary


def write_report(rows: list[dict[str, object]]) -> None:
    by_type = summarize(rows, "loan_type")
    by_decision = summarize(rows, "decision")
    non_rejected = [row for row in rows if row["decision"] != "Reject"]
    rates = [float(row["offered_rate"]) for row in non_rejected]

    def table(summary: list[dict[str, object]]) -> str:
        columns = list(summary[0].keys())
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        for row in summary:
            lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
        return "\n".join(lines)

    report = f"""# Model Report

Generated by `src/loan_underwriting.py`.

## Purpose

This model combines the 5 Cs of credit with simplified Norwegian lending rules to produce approval decisions, risk classes, and risk-based offered rates.

## Pricing Formula

```text
offered rate = 4.25% base rate + product margin + Monte Carlo risk margin
```

## Results by Loan Type

{table(by_type)}

## Results by Decision

{table(by_decision)}

## Offered Rate Range

Non-rejected applications: {min(rates):.2%} to {max(rates):.2%}, average {mean(rates):.2%}.
"""
    MODEL_REPORT_FILE.write_text(report, encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows = generate_synthetic_applications()
    write_csv(DATA_FILE, raw_rows)
    build_database(raw_rows)

    result_rows = [enrich(row) for row in fetch_rows()]
    write_csv(RESULTS_FILE, result_rows)
    write_csv(DECISION_SUMMARY_FILE, summarize(result_rows, "decision"))
    write_csv(RISK_CLASS_SUMMARY_FILE, summarize(result_rows, "risk_class"))
    write_report(result_rows)

    print(f"Applications: {len(result_rows)}")
    print(f"Base rate: {BASE_RATE:.2%}")
    print(f"Wrote: {DATA_FILE.relative_to(ROOT)}")
    print(f"Wrote: {DB_FILE.relative_to(ROOT)}")
    print(f"Wrote: {RESULTS_FILE.relative_to(ROOT)}")
    print(f"Wrote: {MODEL_REPORT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
