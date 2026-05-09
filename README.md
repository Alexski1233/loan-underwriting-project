# loan-underwriting-project

A pedagogical loan underwriting project built with Python and PostgreSQL.

The project uses a simple rule-based workflow to evaluate sample loan applications. It is not a production banking model, a machine learning model, or a complete credit-risk system. The goal is to demonstrate practical use of Python, SQL, and PostgreSQL in a banking and credit context.

## What the project does

1. Generates sample loan applications.
2. Stores the applications in PostgreSQL.
3. Calculates key underwriting metrics such as debt-to-income and loan-to-value.
4. Classifies each application as `Approve`, `Reject`, or `Manual review`.
5. Stores detailed results and a summary by customer type.
6. Exports CSV files so the output can also be inspected outside the database.

## Decision rules

The rules are intentionally simple and explainable:

- reject if the customer has payment remarks
- reject if total debt after the new loan is above 5x annual income
- send mortgage applications to manual review if loan-to-value is above 90%
- send applications to manual review if debt is close to the limit
- send large consumer loans to manual review
- approve applications that pass the rules

These rules are simplified for learning purposes. They should not be treated as real bank policy.

## Database tables

The SQL schema creates three tables:

- `loan_applications`: generated loan applications
- `underwriting_results`: one underwriting decision per application
- `customer_type_summary`: aggregated results for `strong`, `regular`, and `risky` customers

## Technologies used

- Python
- PostgreSQL
- SQL
- pandas
- GitHub

## Project structure

```text
.
|-- README.md
|-- requirements.txt
|-- sql/
|   `-- schema.sql
`-- src/
    `-- loan_underwriting.py
```

The script also creates these folders when it runs:

```text
data/
output/
```

## How to run

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Make sure the PostgreSQL database exists:

```bash
createdb loan_underwriting
```

Run the project:

```bash
python3 src/loan_underwriting.py
```

By default, the script connects to a local PostgreSQL database using:

```text
postgresql:///loan_underwriting
```

If your PostgreSQL setup requires a username and password, set `DATABASE_URL` before running the script:

```bash
export DATABASE_URL='postgresql://your_user:your_password@localhost:5432/loan_underwriting'
python3 src/loan_underwriting.py
```

## Expected output

A successful run prints:

```text
Applications checked: 36
Wrote: output/underwriting_results.csv
Wrote: output/customer_type_summary.csv
```

The main output files are:

- `output/underwriting_results.csv`
- `output/customer_type_summary.csv`

You can also inspect the database directly:

```sql
SELECT * FROM customer_type_summary;

SELECT application_id, customer_type, loan_type, debt_to_income, loan_to_value, decision, decision_reason
FROM underwriting_results
ORDER BY application_id
LIMIT 10;
```
