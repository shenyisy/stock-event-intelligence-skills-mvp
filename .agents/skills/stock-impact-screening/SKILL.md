---
name: stock-impact-screening
description: Link normalized events to configured watchlist stocks and apply deterministic attention-signal gates.
---

# Stock Impact Screening

- Use `config/watchlist.json` and `config/policy.json`.
- Treat exposure rules as hypotheses, not causal findings.
- Use only explicit subject ticker or configured candidate ticker links; do not infer arbitrary ticker exposure.
- Python computes the score and gates. Explain score components and blockers.
- No consensus means no surprise calculation. No historical study means `INSUFFICIENT_EVIDENCE`.
- `ACTIONABLE_ALERT` means review attention only, not a trade instruction.
