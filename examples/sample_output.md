# Sample run — python cli.py --demo (mock backend, no API key)

```
====================================================================
Blue Gum Joinery Pty Ltd   (ABN 11111111101)
Requested: $15,000 on 30-day terms
--------------------------------------------------------------------
  [ APPROVE ]   confidence 0.94   (decided by: model)
  Why:
    + Strong credit rating A1.  (credit_rating)
    + Low default probability 1.2%.  (pd_12m)
    + Established entity, 12 years on the ABR.  (abn_age_years)
====================================================================
====================================================================
Harbour Freight Co Pty Ltd   (ABN 11111111102)
Requested: $25,000 on 30-day terms
--------------------------------------------------------------------
  [ APPROVE ]   confidence 0.80   (decided by: model)
  Why:
    + Strong credit rating A2.  (credit_rating)
    + Low default probability 2.0%.  (pd_12m)
    + Established entity, 8 years on the ABR.  (abn_age_years)
====================================================================
====================================================================
Stillwater Logistics Pty Ltd   (ABN 11111111103)
Requested: $120,000 on 45-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.90   (decided by: model+policy)
  model alone said: APPROVE  ->  raised by guardrail
  Why:
    + Strong credit rating A1.  (credit_rating)
    + Low default probability 1.5%.  (pd_12m)
    + Established entity, 10 years on the ABR.  (abn_age_years)
  Guardrail flags:
    ! Requested limit $120,000 exceeds the $50,000 auto-decision cap; exposure too large to approve without a human.
  note: Model said APPROVE; guardrail raised it to REFER (most-conservative rule).
====================================================================
====================================================================
Redline Electrical Pty Ltd   (ABN 11111111104)
Requested: $20,000 on 30-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.55   (decided by: model+policy)
  Why:
    - 2 director changes in 90 days.  (director_changes_90d)
    + Established entity, 6 years on the ABR.  (abn_age_years)
  Guardrail flags:
    ! 2 director changes in 90 days. Businesses losing 2+ directors in 12 months are materially more likely to become insolvent; escalate to a human.
  note: Model confidence 0.55 below automation threshold 0.70; floored to REFER.
====================================================================
====================================================================
Pinnacle Fitouts Pty Ltd   (ABN 11111111105)
Requested: $30,000 on 30-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.55   (decided by: model+policy)
  Why:
    - 1 active court action(s).  (court_actions)
    + Established entity, 7 years on the ABR.  (abn_age_years)
  Guardrail flags:
    ! 1 active court action(s) on file; requires human judgement on materiality.
  note: Model confidence 0.55 below automation threshold 0.70; floored to REFER.
====================================================================
====================================================================
Nimbus Startup Pty Ltd   (ABN 11111111106)
Requested: $15,000 on 30-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.55   (decided by: model+policy)
  Why:
    - Young entity, only 0.8 years registered.  (abn_age_years)
  Guardrail flags:
    ! Thin file (data completeness 45%); not enough evidence to automate.
  note: Model confidence 0.55 below automation threshold 0.70; floored to REFER.
====================================================================
====================================================================
Cobalt Trades Pty Ltd   (ABN 11111111107)
Requested: $20,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.50   (decided by: model+policy)
  Why:
    - Elevated 12-month default probability 6.5%.  (pd_12m)
    - 1 payment default(s) totalling $4,200.  (payment_defaults)
    + Established entity, 5 years on the ABR.  (abn_age_years)
  Guardrail flags:
    ! Modelled default probability 6.5% is elevated (>= 5%); escalate.
    ! Credit rating C1 is below the auto-approve floor of B2.
  note: Model confidence 0.50 below automation threshold 0.70; floored to REFER.
====================================================================
====================================================================
Ironbark Holdings Pty Ltd   (ABN 11111111108)
Requested: $20,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.99   (decided by: policy)
  Why:
    - Modelled 12-month default probability 13.0% exceeds decline threshold 12%.  (policy)
  Guardrail flags:
    ! Modelled 12-month default probability 13.0% exceeds decline threshold 12%.
  note: Decided by policy guardrail; model not consulted.
====================================================================
====================================================================
Defunct Ventures Pty Ltd   (ABN 11111111109)
Requested: $10,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.99   (decided by: policy)
  Why:
    - Entity status is Deregistered; cannot extend credit.  (policy)
  Guardrail flags:
    ! Entity status is Deregistered; cannot extend credit.
  note: Decided by policy guardrail; model not consulted.
====================================================================
====================================================================
Tumbleweed Retail Pty Ltd   (ABN 11111111110)
Requested: $40,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.99   (decided by: policy)
  Why:
    - Modelled 12-month default probability 15.0% exceeds decline threshold 12%.  (policy)
  Guardrail flags:
    ! Modelled 12-month default probability 15.0% exceeds decline threshold 12%.
  note: Decided by policy guardrail; model not consulted.
====================================================================
====================================================================
Saltbush Catering Pty Ltd   (ABN 11111111111)
Requested: $25,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.89   (decided by: model+policy)
  Why:
    - Elevated 12-month default probability 7.0%.  (pd_12m)
    - 1 payment default(s) totalling $5,500.  (payment_defaults)
    - Pays 25 days beyond terms on average.  (avg_days_beyond_terms)
  Guardrail flags:
    ! Modelled default probability 7.0% is elevated (>= 5%); escalate.
    ! Credit rating C2 is below the auto-approve floor of B2.
====================================================================
====================================================================
Greenfield Sole Trader   (ABN 11111111112)
Requested: $10,000 on 30-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.55   (decided by: model+policy)
  Why:
    - Young entity, only 1.5 years registered.  (abn_age_years)
    · Not registered for GST; turnover may be limited.  (gst_registered)
  Guardrail flags:
    ! Thin file (data completeness 50%); not enough evidence to automate.
  note: Model confidence 0.55 below automation threshold 0.70; floored to REFER.
====================================================================
====================================================================
Granite Estates Pty Ltd   (ABN 11111111113)
Requested: $10,000 on 60-day terms
--------------------------------------------------------------------
  [ APPROVE ]   confidence 0.96   (decided by: model)
  Why:
    + Strong credit rating A1.  (credit_rating)
    + Low default probability 1.0%.  (pd_12m)
    + Established entity, 15 years on the ABR.  (abn_age_years)
====================================================================
====================================================================
Meridian Supplies Pty Ltd   (ABN 11111111114)
Requested: $50,000 on 30-day terms
--------------------------------------------------------------------
  [ APPROVE ]   confidence 0.73   (decided by: model)
  Why:
    + Strong credit rating A2.  (credit_rating)
    + Established entity, 9 years on the ABR.  (abn_age_years)
====================================================================
====================================================================
Hollow Log Brewing Pty Ltd   (ABN 11111111115)
Requested: $18,000 on 30-day terms
--------------------------------------------------------------------
  [ DECLINE ]   confidence 0.99   (decided by: policy)
  Why:
    - Entity status is Cancelled; cannot extend credit.  (policy)
  Guardrail flags:
    ! Entity status is Cancelled; cannot extend credit.
  note: Decided by policy guardrail; model not consulted.
====================================================================
====================================================================
Switchback Couriers Pty Ltd   (ABN 11111111116)
Requested: $8,000 on 30-day terms
--------------------------------------------------------------------
  [ REFER  ]   confidence 0.55   (decided by: model+policy)
  Why:
    - Elevated 12-month default probability 9.0%.  (pd_12m)
    - 1 payment default(s) totalling $7,000.  (payment_defaults)
    + Established entity, 5 years on the ABR.  (abn_age_years)
  Guardrail flags:
    ! Modelled default probability 9.0% is elevated (>= 5%); escalate.
    ! Credit rating C1 is below the auto-approve floor of B2.
  note: Model confidence 0.55 below automation threshold 0.70; floored to REFER.
====================================================================
```

# Evaluation — python -m evals.run_evals

```

Onboarding Risk Copilot — evaluation
====================================================
  Applicants evaluated     : 16
  Accuracy (vs analyst)    : 88%
  Unsafe-approve rate      : 0%   (target 0%)
  Auto-decision rate       : 62%
  Referral rate            : 38%
  Citation faithfulness    : 100%

  Confusion matrix (rows = truth, cols = predicted)
              APPROVE    REFER  DECLINE
    APPROVE         4        0        0
    REFER           0        6        2
    DECLINE         0        0        4

  No unsafe approvals. Every clear-cut DECLINE/REFER was caught.
====================================================
```
