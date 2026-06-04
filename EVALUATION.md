# Evaluation

Why accuracy alone is the wrong target for a credit decision, and what to
measure instead.

## The test set

`data/synthetic_applicants.json` holds 16 labelled applicants. Each carries a
full set of signals and a `ground_truth` decision (APPROVE / REFER / DECLINE)
representing what a senior credit analyst would do. The set is deliberately
small and hand-built to span the decision space: clean blue-chips, high-exposure
asks, director exodus, active court actions, thin files, elevated default
probabilities, deregistered and cancelled entities, and genuine borderline
cases. It is synthetic and illustrative — the point is the evaluation *method*,
which transfers directly to a real labelled set.

## Metrics

**Accuracy** — exact match to the analyst label. Reported, but not the goal.
A model that swaps a few cheap referrals for one catastrophic approval can post
high accuracy while being unfit for production.

**Unsafe-approve rate** — the share of applicants the system APPROVED that
should have been REFER or DECLINE. This is the expensive error and the real
release gate. Target: zero.

**Auto-decision rate** — the share decided without a human (APPROVE or DECLINE).
The efficiency win. Only meaningful while unsafe-approve stays at zero.

**Referral rate** — the share sent to a human. Too low and the system is
reckless; too high and it adds nothing over a manual queue. A dial to calibrate,
not a number to minimise.

**Citation faithfulness** — the share of generated reasons that cite a real
signal field. A hallucination guardrail: a reason that references data the
applicant does not have is a defect, regardless of whether the final decision
was correct.

## Current results (mock backend)

```
Accuracy (vs analyst)    : 88%
Unsafe-approve rate      : 0%     (target 0%)
Auto-decision rate       : 62%
Referral rate            : 38%
Citation faithfulness    : 100%

Confusion (rows = truth, cols = predicted)
              APPROVE    REFER  DECLINE
    APPROVE         4        0        0
    REFER           0        6        2
    DECLINE         0        0        4
```

## Reading the errors

The two misclassifications are both REFER cases the system **declined**. That is
an over-cautious error: a human would have looked and possibly approved, but the
system never approved anything it should not have. Every error falls on the safe
side of the asymmetry described in the PRD. There are zero unsafe approvals,
which is the property that actually matters.

If this were real data, the next move would be to calibrate the decline
thresholds to push those two borderline cases back into REFER (recovering the
lost customers) while watching that the unsafe-approve rate stays at zero. That
trade — recover conversions without taking on bad debt — is the ongoing product
job, and it is exactly what the harness is built to measure.

## Running it

```bash
python -m evals.run_evals               # mock backend, deterministic, no key
python -m evals.run_evals --model anthropic   # with Claude
```

The mock backend makes the evaluation reproducible and CI-friendly. Because the
guardrail wraps whichever backend produced the recommendation, the unsafe-approve
property is enforced identically whether the reasoner is the heuristic or a
live model.
