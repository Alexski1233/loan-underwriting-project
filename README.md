# loan-underwriting-project

A transparent credit underwriting project that combines PostgreSQL, Python, the 5 Cs of credit, simplified Norwegian lending rules, and Monte Carlo loss simulation to decide whether a loan should be approved and what interest rate should be offered.

The project is built as a portfolio/CV project: readable, reproducible, and focused on explaining the decision logic behind loan approval and risk-based pricing.

## Project Highlights

- Models three loan types: mortgage, car loan, and consumer loan.
- Uses PostgreSQL to store applications and calculate underwriting features such as DTI, LTV, liquidity buffer, and regulatory checks.
- Uses Python to score the 5 Cs of credit: credit history, capacity, collateral, capital, and conditions.
- Applies simplified Norwegian lending rules such as 5x income, mortgage LTV limit, consumer loan term limit, and interest stress testing.
- Uses Monte Carlo simulation to estimate expected loss and tail loss.
- Converts credit risk into an offered interest rate using:

```text
offered rate = 4.25% base rate + product margin + Monte Carlo risk margin
```

## Why This Project

Banks rarely make only a yes/no loan decision. A borrower can be approved, rejected, or sent to manual review, and the same risk assessment also affects:

- loan amount
- interest rate
- required collateral
- repayment term
- covenants or stricter conditions

This project demonstrates that logic with a simple but explainable scorecard model.

## Model Overview

The model has three layers:

1. **PostgreSQL feature layer**
   - stores synthetic loan applications
   - calculates debt-to-income, loan-to-value, capital-to-loan, and liquidity metrics using SQL views
   - flags hard-rule failures

2. **Python underwriting layer**
   - scores each borrower using the 5 Cs
   - assigns a final risk score and risk class
   - runs the interest stress test
   - decides approve, reject, or manual review

3. **Python pricing layer**
   - estimates probability of default from the final risk score
   - estimates loss given default from collateral and loan type
   - runs Monte Carlo simulations of credit losses
   - prices the loan using base rate, product margin, and risk margin

## 5 Cs Scorecard

| Component | Weight | Variables Used |
|---|---:|---|
| Credit history | 25% | credit score, credit utilization, payment remarks, previous defaults |
| Capacity | 35% | DTI, employment history, stressed payment surplus |
| Collateral | 15% | collateral type, LTV, secured vs unsecured loan |
| Capital | 15% | savings, investments, other assets, liquidity buffer |
| Conditions | 10% | loan purpose, loan type, repayment term |

Capacity has the highest weight because the most important question is whether the borrower can service the debt.

## Simplified Norwegian Lending Rules

The model includes simplified versions of common Norwegian lending constraints:

- total debt after the loan should not exceed 5 times gross annual income
- mortgages should not exceed 90% loan-to-value
- consumer loans should not exceed a 5-year term
- borrowers must pass a stress test using the higher of offered rate + 3 percentage points or 7%

These rules are simplified for a school/portfolio project and should not be treated as a complete regulatory implementation.

## Expected Output

Running the model generates 120 synthetic loan applications and writes:

- row-level underwriting results
- approval, manual review, and rejection decisions
- rejection reasons
- 5 Cs component scores
- risk classes
- estimated PD and LGD
- expected and tail loss estimates
- risk-based offered rates
- a Markdown model report

The expected pattern is:

- mortgages usually receive lower rates because they are secured by property
- car loans have medium risk because the collateral depreciates
- consumer loans are priced higher because they are unsecured

## Repository Structure

```text
.
|-- docker-compose.yml
|-- docs/
|   |-- cv_summary.md
|   |-- methodology.md
|   `-- references.md
|-- sql/
|   `-- schema.sql
|-- src/
|   `-- loan_underwriting.py
|-- README.md
`-- requirements.txt
```

The `data/` and `output/` folders are generated when the model is run.

## How to Run

Clone the project:

```bash
git clone https://github.com/Alexski1233/loan-underwriting-project.git
cd loan-underwriting-project
```

Start PostgreSQL:

```bash
docker compose up -d
```

Install Python dependency:

```bash
pip install -r requirements.txt
```

Run the model:

```bash
python src/loan_underwriting.py
```

The script connects to PostgreSQL using this default URL:

```text
postgresql://loan_user:loan_password@localhost:5432/loan_underwriting
```

You can override it with:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/database"
```

## Outputs

- `data/loan_applications.csv`: generated synthetic input data
- `output/underwriting_results.csv`: row-level result for every application
- `output/model_report.md`: readable report with assumptions and result tables
- `output/decision_summary.csv`: summary by decision
- `output/risk_class_summary.csv`: summary by risk class

## Tech Stack

- Python
- PostgreSQL
- SQL views
- Docker Compose
- Monte Carlo simulation
- Scorecard modeling
- Synthetic data generation

## Limitations

This is not a production lending model. The data is synthetic, the PD/LGD functions are simplified, and the regulatory rules are implemented at a high level. The purpose is to demonstrate credit-risk reasoning, data modeling, SQL/Python workflow, and explainable pricing logic.

## Possible Extensions

- replace synthetic data with anonymized real or public loan data
- calibrate PD and LGD from historical defaults
- add stochastic interest-rate paths
- add visual dashboards
- compare scorecard results with a machine learning classifier
- add separate models for mortgage, car, and consumer lending
