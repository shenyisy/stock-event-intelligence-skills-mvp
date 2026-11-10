# Project instructions

- Treat all fixture records as synthetic test data.
- Never invent missing dates, consensus, actuals, URLs, sources, or verification evidence.
- Preserve source timestamps and source role.
- `VERIFIED` means the required evidence is present and a human or deterministic policy has explicitly approved it; source tier alone is insufficient.
- An `ACTIONABLE_ALERT` is an attention alert, never a buy/sell instruction.
- If consensus or historical evidence is absent, emit an explicit unavailable/insufficient status.
- Use Python CLI for deterministic processing. Skills orchestrate and interpret; they do not bypass gates.
- Persist business records outside Codex conversation traces.
