# loan-underwriting-project

A small loan underwriting project with Python and PostgreSQL.

The project is intentionally simple. PostgreSQL is used as the database. Python creates sample loan applications, checks them with a few clear rules, and saves the result back to the database.

## What the project does

1. Creates sample loan applications.
2. Stores the applications in PostgreSQL.
3. Checks each application with simple rules.
4. Saves one result row per application.
5. Saves a short summary by customer type.

## Database tables

The SQL file creates three tables:

- `loan_applications`: the original loan applications
- `underwriting_results`: the decision for each application
- `customer_type_summary`: a summary for `strong`, `regular`, and `risky` customers

SQL is only used for storing the data. The calculations are kept in Python so the flow is easy to follow.

## Simple decision rules

The project uses these rules:

- reject if the customer has payment remarks
- reject if total debt after the new loan is above 5x annual income
- send mortgage applications to manual review if loan-to-value is above 90%
- send applications to manual review if debt is close to the limit
- approve applications that pass the rules

This is not a real bank model. It is a simple example project.

## How to run

Start PostgreSQL:

```bash
docker compose up -d
```

Install the Python dependency:

```bash
pip install -r requirements.txt
```

Run the project:

```bash
python src/loan_underwriting.py
```

The script uses this database URL unless another one is set:

```text
postgresql://loan_user:loan_password@localhost:5432/loan_underwriting
```

## Files

```text
.
|-- docker-compose.yml
|-- requirements.txt
|-- sql/
|   `-- schema.sql
|-- src/
|   `-- loan_underwriting.py
`-- README.md
```

When the script runs, it also creates CSV files in `data/` and `output/` so the results can be opened without using the database.
