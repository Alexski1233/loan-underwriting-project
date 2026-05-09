DROP VIEW IF EXISTS regulatory_check;
DROP VIEW IF EXISTS underwriting_features;
DROP TABLE IF EXISTS customer_type_summary;
DROP TABLE IF EXISTS underwriting_results;
DROP TABLE IF EXISTS loan_applications;

CREATE TABLE loan_applications (
    application_id INTEGER PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    customer_type VARCHAR(30) NOT NULL,
    loan_type VARCHAR(20) NOT NULL,
    loan_amount NUMERIC(14, 2) NOT NULL,
    annual_income NUMERIC(14, 2) NOT NULL,
    existing_debt NUMERIC(14, 2) NOT NULL,
    payment_remarks INTEGER NOT NULL,
    collateral_value NUMERIC(14, 2) NOT NULL
);

CREATE TABLE underwriting_results (
    result_id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES loan_applications(application_id),
    customer_id VARCHAR(20) NOT NULL,
    customer_type VARCHAR(30) NOT NULL,
    loan_type VARCHAR(20) NOT NULL,
    loan_amount NUMERIC(14, 2) NOT NULL,
    annual_income NUMERIC(14, 2) NOT NULL,
    existing_debt NUMERIC(14, 2) NOT NULL,
    debt_to_income NUMERIC(6, 2) NOT NULL,
    loan_to_value NUMERIC(6, 2),
    decision VARCHAR(30) NOT NULL,
    decision_reason VARCHAR(120) NOT NULL
);

CREATE TABLE customer_type_summary (
    customer_type VARCHAR(30) PRIMARY KEY,
    applications INTEGER NOT NULL,
    approved INTEGER NOT NULL,
    manual_review INTEGER NOT NULL,
    rejected INTEGER NOT NULL,
    average_loan_amount NUMERIC(14, 2) NOT NULL
);
