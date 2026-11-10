# Stock Event Intelligence — Skills MVP

A small, runnable Codex Skills-first prototype. It demonstrates one complete path:

`discover -> normalize/deduplicate -> verify -> link watchlist -> screen -> brief`

This is an implementation scaffold, not a production market-data integration. The fixture is synthetic and must not be treated as market research.

## Requirements
- Python 3.10+
- No third-party Python dependencies

## Run
```bash
python -m src.event_intelligence.cli init
python -m src.event_intelligence.cli run --input fixtures/events.json
python -m unittest discover -s tests -v
```

The command writes:
- `data/raw/<run_id>.json`: immutable input snapshot
- `data/curated/<run_id>.json`: normalized records and signals
- `database/events.sqlite3`: operational records
- `reports/daily/<run_id>.md`: evidence-linked brief
- `runs/<run_id>.json`: run manifest

## Use in Codex
Open this directory as a Codex project. Skills are under `.agents/skills/`.
Start with `event-intelligence-run`; it orchestrates the other skills and invokes the Python CLI.
Skills provide workflow instructions. Python owns deterministic operations (IDs, deduplication,
validation, gates, scoring, persistence and report rendering). Do not let an LLM invent event
facts, source evidence, consensus values, or probabilities.

## Replace the fixture with a real source
Implement a source adapter that emits the same input contract as `fixtures/events.json`.
Keep `published_at`, `fetched_at`, `available_at`, provider/source identity, URL and raw payload.
Do not promote an aggregator record to verified solely because it has a high provider impact label.
Company events require issuer IR / SEC evidence before being marked verified.

## MVP boundaries
- No trading recommendations or order execution.
- No calibrated event or stock-response probability.
- No historical event study in this MVP.
- No live geopolitical monitoring; only the common event/source contract is prepared.
- No claim that Codex traces are the business data store.
