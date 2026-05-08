DROP TABLE IF EXISTS loan_applications;

CREATE TABLE loan_applications (
    application_id INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL,
    loan_type TEXT NOT NULL CHECK (loan_type IN ('mortgage', 'car', 'consumer')),
    loan_purpose TEXT NOT NULL,
    loan_amount REAL NOT NULL,
    term_years INTEGER NOT NULL,

    annual_income REAL NOT NULL,
    monthly_fixed_expenses REAL NOT NULL,
    existing_debt REAL NOT NULL,
    existing_debt_monthly_payment REAL NOT NULL,
    employment_years REAL NOT NULL,

    credit_score INTEGER NOT NULL,
    credit_utilization REAL NOT NULL,
    active_credit_lines INTEGER NOT NULL,
    payment_remarks INTEGER NOT NULL,
    previous_defaults INTEGER NOT NULL,

    savings REAL NOT NULL,
    investments REAL NOT NULL,
    other_assets REAL NOT NULL,

    collateral_value REAL NOT NULL,
    collateral_type TEXT NOT NULL
);

DROP VIEW IF EXISTS underwriting_features;

CREATE VIEW underwriting_features AS
SELECT
    *,
    annual_income / 12.0 AS monthly_income,
    existing_debt / NULLIF(annual_income, 0) AS dti_existing,
    (existing_debt + loan_amount) / NULLIF(annual_income, 0) AS dti_after_loan,
    CASE
        WHEN collateral_value > 0 THEN loan_amount / collateral_value
        ELSE NULL
    END AS ltv,
    savings + investments + other_assets AS total_customer_capital,
    (savings + investments + other_assets) / NULLIF(loan_amount, 0) AS capital_to_loan,
    savings / NULLIF(monthly_fixed_expenses + existing_debt_monthly_payment, 0) AS liquidity_months_before_loan
FROM loan_applications;

DROP VIEW IF EXISTS regulatory_check;

CREATE VIEW regulatory_check AS
SELECT
    *,
    CASE
        WHEN dti_after_loan <= 5.0 THEN 1
        ELSE 0
    END AS passes_debt_to_income_rule,
    CASE
        WHEN loan_type != 'mortgage' THEN 1
        WHEN ltv <= 0.90 THEN 1
        ELSE 0
    END AS passes_mortgage_ltv_rule,
    CASE
        WHEN loan_type != 'consumer' THEN 1
        WHEN term_years <= 5 THEN 1
        ELSE 0
    END AS passes_consumer_term_rule,
    CASE
        WHEN dti_after_loan > 5.0 THEN 'Debt above 5x income'
        WHEN loan_type = 'mortgage' AND (ltv IS NULL OR ltv > 0.90) THEN 'Mortgage LTV above 90%'
        WHEN loan_type = 'consumer' AND term_years > 5 THEN 'Consumer loan term above 5 years'
        ELSE 'Pass'
    END AS regulatory_status
FROM underwriting_features;
