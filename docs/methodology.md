# Methodology

This project models loan underwriting as a transparent decision process rather than a black-box prediction problem.

## 1. Data Generation

The project creates 120 synthetic loan applications across three loan types:

- mortgage
- car loan
- consumer loan

Each application includes borrower income, existing debt, expenses, employment history, credit behavior, savings, investments, collateral value, loan amount, loan term, and loan purpose.

The data is synthetic so the project can be published safely on GitHub without personal or confidential information.

## 2. SQL Feature Engineering

SQL is used for the structured underwriting layer. The database includes:

- one main `loan_applications` table
- one `underwriting_features` view
- one `regulatory_check` view

The SQL views calculate:

- monthly income
- existing debt-to-income
- debt-to-income after the new loan
- loan-to-value
- total customer capital
- capital-to-loan ratio
- liquidity buffer before the new loan
- simplified regulatory pass/fail flags

## 3. 5 Cs Credit Score

The Python model scores each application using the 5 Cs of credit.

| Component | Interpretation |
|---|---|
| Credit history | Has the borrower repaid debt reliably in the past? |
| Capacity | Can the borrower afford the new debt? |
| Collateral | What can the bank recover if the borrower defaults? |
| Capital | How much financial buffer or own money does the borrower have? |
| Conditions | Does the purpose, loan type, and term make sense? |

The final score is a weighted average:

```text
final score =
  25% credit history
+ 35% capacity
+ 15% collateral
+ 15% capital
+ 10% conditions
```

## 4. Hard Rules

The score does not override hard rules. An application can be rejected even with a decent score if it fails key constraints:

- total debt above 5 times annual income
- mortgage LTV above 90%
- consumer loan term above 5 years
- failed interest stress test

This separates **eligibility** from **risk quality**.

## 5. Monte Carlo Pricing

The model converts risk into price.

First, probability of default is estimated from the final 5 Cs score and loan type. Lower scores imply higher PD. Consumer loans receive a higher multiplier than mortgages because they are unsecured.

Second, loss given default is estimated from collateral. Secured loans usually have lower LGD than unsecured loans.

Then the model simulates default events and loss severity. The risk margin combines:

- expected loss
- a portion of tail loss

The offered rate is:

```text
offered rate = base rate + product margin + risk margin
```

The base rate is set to 4.25%.

## 6. Decision Output

Each application receives:

- decision: approve, manual review, or reject
- decision reason
- 5 Cs component scores
- final score
- risk class
- estimated PD
- estimated LGD
- expected loss rate
- tail loss rate
- offered interest rate
- weakest score components

This makes the model explainable and easy to audit.
