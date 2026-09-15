# IFRS 9 Staging Logic

Loans are classified into **Stage 1, Stage 2, or Stage 3** based on their credit risk. The stage determines whether **12-month or lifetime ECL** is applied.

## Stage 3: Credit-Impaired / Default

A loan is Stage 3 when:

* `days_past_due >= 90`

The 90-day threshold is used as the default backstop. Stage 3 is checked first to ensure the most severe applicable stage is assigned.

## Stage 2: Significant Increase in Credit Risk

If the loan is not Stage 3, it becomes Stage 2 if **any** of these conditions apply:

* `days_past_due` is between **30 and 89 days**
* `credit_score_change <= -30`
* `watchlist_flag == 1`

These triggers represent payment delays, deteriorating creditworthiness, or internal risk concerns.

## Stage 1: Performing

Loans that do not meet any Stage 2 or Stage 3 conditions are classified as Stage 1 and receive a **12-month ECL** provision.

## Evaluation Order

The rules are applied in this order:

**Stage 3 → Stage 2 → Stage 1**

This prevents a loan from being assigned to a less severe stage when it meets a higher-risk condition.

## Simplification

Real-world IFRS 9 models typically compare current and origination PDs along with other risk indicators. This project uses simpler rule-based triggers such as **DPD, credit score change, and watchlist status**.
