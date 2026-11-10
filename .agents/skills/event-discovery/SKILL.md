---
name: event-discovery
description: Discover candidate scheduled macro and company events from configured source adapters or an explicitly supplied input file.
---

# Event Discovery

- Collect candidate events only from configured sources or user-supplied records.
- Preserve provider IDs, source role, URL, published/fetched/available timestamps and raw payload.
- Label the source role; do not treat provider impact labels as verification.
- Emit records conforming to `contracts/input-event.schema.json`.
- If no real source adapter exists, state that discovery is fixture-only; do not imply live collection.
