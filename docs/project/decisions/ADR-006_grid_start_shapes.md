# ADR-006 — Career grid start: free start and GT-style start (index 23)

- **Status:** accepted (2026-11-03)
- **Scope:** which session-generator grid shapes the career uses for the human's start slot

## Context

The human's grid slot comes from the session generator, not from the series
([RACE_SYSTEM](../../reference/RACE_SYSTEM.md) §2.17). Tests over three
benches gave three behaviours: with `EstimatedLapTime` and index -1 the slot
picked on the wager screen is obeyed; with `AIDriverRank` the index acts as a
cut (first up to 5, last from 6 on, never a middle slot); with `Qualifying` the
slot is a mid-grid value that changes with the AI document, the field size and
the car, and the wager pick is ignored.

## Decision

1. **Free start:** an `EstimatedLapTime` generator with index -1. The player
   chooses the slot (the wager screen's bonus applies).
2. **GT-style start:** an `AIDriverRank` generator with index **23**: the player
   starts last and climbs. Index 23 is fixed for every series that uses it.
3. **`Qualifying` is documented but not used.** Its slot is not a constant and
   depends on the AI document and the car; it stays in the reference as an
   option for a classification-style start.

## Consequences

- New series pick one of the two shapes by choosing the generator; no series
  field sets the start slot.
- The index-6 to 23 bench series are test material, not part of the final career.
- A mid-grid fixed start is out of scope until a generator shape gives a stable
  value.
