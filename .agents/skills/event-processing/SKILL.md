---
name: event-processing
description: Normalize, deduplicate and verify candidate event records while preserving provenance and uncertainty.
---

# Event Processing

- Invoke the Python pipeline; do not manually fabricate normalized facts.
- Deduplicate using event type, normalized subject and event time; retain all source records.
- Keep `temporal_mode`, event time and verification status separate.
- `PENDING`, `PARTIALLY_VERIFIED`, `CONFLICTED`, and `VERIFIED` are distinct states.
- An aggregator or news mention is discovery evidence, not official confirmation.
- If source records conflict, keep the conflict visible and block alert promotion.
