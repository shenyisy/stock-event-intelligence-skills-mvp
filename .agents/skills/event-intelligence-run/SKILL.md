---
name: event-intelligence-run
description: Run the end-to-end stock event intelligence MVP from candidate events to a sourced daily brief. Use when asked to scan, process, or summarize upcoming events for the configured watchlist.
---

# Event Intelligence Run

1. Read `AGENTS.md`, `config/watchlist.json`, and `config/policy.json`.
2. Ask for an input file only if no source adapter or fixture is configured. For a smoke test use `fixtures/events.json`.
3. Run `python -m src.event_intelligence.cli run --input <path>`.
4. Inspect the generated run manifest, curated JSON and brief.
5. Explain source coverage, duplicate handling, verification blockers and missing consensus. Never present synthetic fixtures as real market facts.
6. Do not bypass Python gates or write business records only into the conversation.
