# Onboarding Risk Copilot

**A second opinion for the moment a business decides whether to trust a new customer with credit.**

When a company lets a new customer "buy now, pay later" on a trade account, someone has to make a call: do we trust this business to pay us back? Say yes too easily and you eventually get burned by a customer who doesn't pay. Say no too often and you turn away good business and annoy people who would have paid you just fine.

This tool helps make that call. You give it a business (an ABN) and how much credit they're asking for. It reads what's known about them, and it does one of three things:

- **Approve** — clearly safe, let them through in seconds.
- **Decline** — clearly not, with the reasons.
- **Refer** — "I'm not sure, a human should look at this one."

It explains every call in plain English, and it is built so that it would rather bother a human than make an expensive mistake.

> An independent demo, not affiliated with CreditorWatch. The risk data here is **made up and clearly labelled as such** — no real customer data, no company systems. The only live data it touches is the free, public Australian Business Register (ABN Lookup).

---

## The one idea that matters

The two ways to be wrong are not equally costly, and that should change how you build.

Approve a customer who then doesn't pay, and you lose real money: the unpaid invoice, often thousands of dollars, usually gone for good. Send a perfectly good customer to a human for a second look, and you have "cost" that person a few minutes. One mistake is a thousand times more expensive than the other.

Most automation ignores this. It treats every decision the same and, sooner or later, confidently approves something it shouldn't. This tool does the opposite on purpose. It is happy to wave through the easy, obvious cases on its own (that's the speed and the saved effort), and it deliberately kicks anything doubtful or large to a person (that's the protection against bad debt). It behaves like a seasoned credit manager: quick on the clear ones, cautious on the rest.

That single choice — be cheap to be cautious, expensive to be reckless — is the whole design.

## Why a person can always trust it

The clever part doesn't get the final word. A plain, fixed set of rules sits on top of the AI and always takes the safer of the two opinions. If the AI says "approve" but the amount is large, or the business has a court action, or a couple of directors just walked out the door, the rules quietly raise the decision to "refer — get a human." The AI advises. The rules decide how much we're willing to risk. So the safety of the system never depends on the AI being on its best behaviour that day.

## How it does well, in numbers

Run against 16 test businesses with known "right answers":

| What we measured | Result | Why it matters |
|---|---|---|
| Agreed with the expert's call | 88% | It's usually right |
| **Approved something it shouldn't have** | **0%** | The expensive mistake never happened |
| Handled without bothering a human | 62% | Real time saved |
| Sent to a human | 38% | The doubtful ones, escalated |
| Reasons backed by real data | 100% | It never makes up a reason |

And the times it was "wrong"? It was *too cautious* — it sent two borderline cases to a human that the expert would have declined outright. It never made the mistake that costs money. That is exactly the behaviour we designed for.

You can reproduce this yourself in one command (below).

## Try it in 30 seconds

No setup, no account, no API key needed:

```bash
python cli.py --demo          # watch it judge 16 sample businesses
python -m evals.run_evals     # see the scorecard above, reproduced
```

Check one business yourself:

```bash
python cli.py --abn 51824753556 --name "Acme Pty Ltd" --limit 20000 --terms 30
```

Want the real AI (Claude) instead of the built-in stand-in? Add a key and pass `--model anthropic`. Everything else is identical. (See `.env.example`.)

A captured run is saved in [`examples/sample_output.md`](examples/sample_output.md) if you'd rather just read it.

## Want the detail?

- [`PRD.md`](PRD.md) — the product thinking: who it's for, the cost-of-mistakes logic, what to measure, and how you'd take it from this demo to something real.
- [`EVALUATION.md`](EVALUATION.md) — why "how often is it right?" is the wrong question for a credit decision, and what to ask instead.

## What's under the hood (the short version)

```
A business (ABN) + how much credit they want
        │
        ▼
  Gather what's known   →  public ABN Lookup (real)  +  risk signals (made-up, labelled)
        │
        ▼
  Safety rules, first pass   →  obvious "no"s stop here (e.g. business no longer registered)
        │
        ▼
  The AI weighs it up   →  Approve / Refer / Decline, with reasons and a confidence level
        │
        ▼
  Safety rules, second pass  →  take the more cautious of the two; escalate big or doubtful cases
        │
        ▼
  A clear, explainable decision you could show an auditor
```

Every number that governs caution lives in one file (`src/policy.py`), so the people responsible for risk can adjust the dials without touching the AI.

## Layout

```
cli.py                  Run it from the command line
src/schema.py           The shared vocabulary (plain data structures)
src/enrich.py           Gather the data about a business
src/llm.py              The reasoning step (built-in stand-in, or Claude)
src/policy.py           The safety rules — the human-in-the-loop layer
src/copilot.py          Ties it together
data/                   16 labelled test businesses (synthetic)
evals/                  The scorecard
examples/               A captured run, so you can read without running
```

## License

MIT. See [`LICENSE`](LICENSE).
