# Product brief — Onboarding Risk Copilot

This is the thinking behind the demo. It is written to be read by anyone, not
just product people.

## The problem, plainly

Every business that lets customers pay later has to answer one question about
each new customer: *can we trust them to pay?*

Today a person answers it. They pull a credit report, read through it, and use
judgement. The information needed is all there, but reading it well takes
expertise and time, and most teams don't have a credit expert sitting spare.
The usual shortcut is a rigid "if this, then that" rulebook. It's fast but
blunt: it can't read nuance and it can't explain itself.

So teams are stuck choosing between two bad options. Decide quickly and risk
saying yes to someone who won't pay. Decide carefully and lose customers to a
slow, clunky process.

## Who this is for

- **The person approving accounts** (a credit or accounts-receivable officer at
  a small or mid-sized supplier). They want the easy decisions made for them, and
  the genuinely risky ones handed over with the reasons already laid out.
- **The person responsible for the money** (the finance or risk owner). They want
  automation they can trust and explain — one that physically cannot approve
  something it shouldn't, no matter how the AI is feeling that day.

## The heart of it: the two mistakes aren't equal

| The mistake | What it looks like | What it costs |
|---|---|---|
| Wrong **yes** | automation approves a customer who never pays | the unpaid invoice — thousands of dollars, usually unrecoverable |
| Wrong **maybe** | a cautious system asks a human to double-check | a few minutes of someone's time |

A wrong "yes" can cost a thousand times more than a wrong "maybe." So the tool is
built to be lopsided on purpose. Its first job is to **never make the expensive
mistake**. Its second job is to handle as much as it safely can on its own.

This is the opposite of chasing a high "right answer" score. A system can look
impressively accurate while still, once in a while, confidently approving a
disaster. We would rather be a little over-cautious and never lose the money.

The opposite danger is real too. Be *too* cautious and you refer everything to a
human, and you've built nothing more useful than a slow queue. That's why "how
much did it handle on its own?" is a headline number we watch, not an
afterthought.

## How it decides (version 0.1)

The AI gives an opinion. A plain rulebook sits above it and always takes the
safer of the two. The final answer is never less cautious than either one alone.

- **Automatic "no"** (the AI isn't even asked): the business no longer legally
  exists, or its risk of failing in the next year is very high.
- **Always send to a human:** the amount is large; directors have suddenly left;
  there's a court action; risk is elevated; the credit rating is weak; the file is
  too thin to judge; or the AI itself says it isn't confident.
- **Automatic "yes":** only the clear, well-evidenced, lower-value, high-confidence
  cases.

## What we measure, and why

1. **Did it ever approve something it shouldn't? (Target: never.)** This is the
   one that matters. It's a go/no-go gate, not a nice-to-have.
2. **How much did it handle without a human?** The efficiency it buys you — but
   only counts while number 1 stays at zero.
3. **Of the cases it escalated, how many did a human actually reject?** Tells you
   whether it's escalating the right things. Needs real-world data; not in the demo.
4. **Did every reason point to real data? (Target: always.)** A reason that cites
   information the customer doesn't have is a defect, even if the decision was right.
5. **How fast** it clears the easy majority.

## Not in this version

A live connection to a real credit bureau, training our own models, a polished
screen for end users, writing decisions back into accounting software, and the
learning loop that would tune the caution dials from real outcomes.

## From demo to the real thing

1. Swap the made-up risk signals for a real data feed. The structure stays the same.
2. Swap the built-in reasoner for the live AI. Nothing else changes; they share
   one interface.
3. Add a feedback loop: every time a human overrules a referral, learn from it,
   and use it to tune the caution dials.
4. Before anything goes live, run it silently alongside real past decisions and
   prove the "never wrongly approve" number holds on real data first.
5. Keep the receipts. Every decision already records its reasons, what the AI
   alone thought, and where the safety rules stepped in — the paper trail a
   regulated business needs.

## What could go wrong, and the answer

- **The AI invents a reason** → every reason is checked against real data, and we
  measure how often it slips. Today: never.
- **It quietly gets less cautious over time** → "did it wrongly approve anything?"
  is a release gate, so drift gets caught before it ships.
- **The caution dials go stale** → they live in one place, owned by risk, meant to
  be re-tuned against outcomes, not buried in code.
- **Hidden unfairness in the data** → before trusting it with more decisions, the
  signals and overrides should be checked for bias against particular groups.
  Flagged here, not solved — and that honesty is the point.
