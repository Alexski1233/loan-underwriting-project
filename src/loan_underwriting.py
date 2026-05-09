import os
import random
from pathlib import Path

import pandas as pd
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql:///loan_underwriting")

ROOT = Path(__file__).resolve().parents[1]
SQL_SCHEMA = ROOT / "sql" / "schema.sql"
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"

APPLICATION_FILE = DATA_DIR / "loan_applications.csv"
RESULT_FILE = OUTPUT_DIR / "underwriting_results.csv"
SUMMARY_FILE = OUTPUT_DIR / "customer_type_summary.csv"

APPLICATION_COLUMNS = [
    "application_id",
    "customer_id",
    "customer_type",
    "loan_type",
    "loan_amount",
    "annual_income",
    "existing_debt",
    "payment_remarks",
    "collateral_value",
]

RESULT_COLUMNS = [
    "application_id",
    "customer_id",
    "customer_type",
    "loan_type",
    "loan_amount",
    "annual_income",
    "existing_debt",
    "debt_to_income",
    "loan_to_value",
    "decision",
    "decision_reason",
]

SUMMARY_COLUMNS = [
    "customer_type",
    "applications",
    "approved",
    "manual_review",
    "rejected",
    "average_loan_amount",
]


def database_connection():
    return psycopg.connect(DATABASE_URL)


def create_database_tables():
    schema_sql = SQL_SCHEMA.read_text(encoding="utf-8")

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)


def make_sample_applications():
    random.seed(7)
    rows = []
    application_id = 1

    customer_types = {
        "strong": {
            "income": (850_000, 1_300_000),
            "debt": (300_000, 1_000_000),
            "remarks_chance": 0.00,
        },
        "regular": {
            "income": (520_000, 850_000),
            "debt": (700_000, 1_600_000),
            "remarks_chance": 0.08,
        },
        "risky": {
            "income": (330_000, 620_000),
            "debt": (900_000, 2_100_000),
            "remarks_chance": 0.35,
        },
    }

    loan_types = ["mortgage", "car", "consumer"]

    for customer_type, profile in customer_types.items():
        for number in range(12):
            loan_type = loan_types[number % len(loan_types)]
            annual_income = random.randint(*profile["income"])
            existing_debt = random.randint(*profile["debt"])
            if loan_type == "mortgage":
                loan_amount = random.randint(1_800_000, 4_500_000)
                collateral_value = int(loan_amount / random.uniform(0.72, 0.98))
            elif loan_type == "car":
                loan_amount = random.randint(120_000, 520_000)
                collateral_value = int(loan_amount / random.uniform(0.75, 1.10))
            else:
                loan_amount = random.randint(40_000, 260_000)
                collateral_value = 0

            rows.append(
                {
                    "application_id": application_id,
                    "customer_id": f"C{application_id:03d}",
                    "customer_type": customer_type,
                    "loan_type": loan_type,
                    "loan_amount": loan_amount,
                    "annual_income": annual_income,
                    "existing_debt": existing_debt,
                    "payment_remarks": int(random.random() < profile["remarks_chance"]),
                    "collateral_value": collateral_value,
                }
            )
            application_id += 1

    return rows


def check_application(row):
    debt_to_income = (row["existing_debt"] + row["loan_amount"]) / row["annual_income"]

    if row["collateral_value"] > 0:
        loan_to_value = row["loan_amount"] / row["collateral_value"]
    else:
        loan_to_value = None

    if row["payment_remarks"] == 1:
        decision = "Reject"
        reason = "Payment remarks"
    elif debt_to_income > 5:
        decision = "Reject"
        reason = "Debt is above 5x income"
    elif row["loan_type"] == "mortgage" and loan_to_value is not None and loan_to_value > 0.90:
        decision = "Manual review"
        reason = "Mortgage has high loan-to-value"
    elif debt_to_income > 4:
        decision = "Manual review"
        reason = "Debt is close to the limit"
    elif row["loan_type"] == "consumer" and row["loan_amount"] > row["annual_income"] * 0.35:
        decision = "Manual review"
        reason = "Large consumer loan compared with income"
    else:
        decision = "Approve"
        reason = "Passes the simple rules"

    return {
        "application_id": row["application_id"],
        "customer_id": row["customer_id"],
        "customer_type": row["customer_type"],
        "loan_type": row["loan_type"],
        "loan_amount": row["loan_amount"],
        "annual_income": row["annual_income"],
        "existing_debt": row["existing_debt"],
        "debt_to_income": round(debt_to_income, 2),
        "loan_to_value": round(loan_to_value, 2) if loan_to_value is not None else None,
        "decision": decision,
        "decision_reason": reason,
    }


def make_summary(results):
    summary = []
    customer_types = sorted({row["customer_type"] for row in results})

    for customer_type in customer_types:
        rows = [row for row in results if row["customer_type"] == customer_type]
        total_loan_amount = sum(row["loan_amount"] for row in rows)

        summary.append(
            {
                "customer_type": customer_type,
                "applications": len(rows),
                "approved": sum(row["decision"] == "Approve" for row in rows),
                "manual_review": sum(row["decision"] == "Manual review" for row in rows),
                "rejected": sum(row["decision"] == "Reject" for row in rows),
                "average_loan_amount": round(total_loan_amount / len(rows), 2),
            }
        )

    return summary


def save_rows(table_name, columns, rows):
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(sql, [[row[column] for column in columns] for row in rows])


def write_csv(file_path, columns, rows):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(file_path, index=False)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    applications = make_sample_applications()
    results = [check_application(row) for row in applications]
    summary = make_summary(results)

    create_database_tables()
    save_rows("loan_applications", APPLICATION_COLUMNS, applications)
    save_rows("underwriting_results", RESULT_COLUMNS, results)
    save_rows("customer_type_summary", SUMMARY_COLUMNS, summary)

    write_csv(APPLICATION_FILE, APPLICATION_COLUMNS, applications)
    write_csv(RESULT_FILE, RESULT_COLUMNS, results)
    write_csv(SUMMARY_FILE, SUMMARY_COLUMNS, summary)

    print(f"Applications checked: {len(results)}")
    print(f"Wrote: {RESULT_FILE.relative_to(ROOT)}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
