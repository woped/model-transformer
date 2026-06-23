# Example diagrams

Reference BPMN and PNML models kept for manual inspection and ad-hoc testing.
They are **not** loaded by any automated test (verified: no test references them).

- `bpmn/` — example BPMN process models
- `pnml/` — example WoPeD Petri-net models

Active test fixtures live elsewhere and should not be confused with these:

- `tests/transform/assets/multiplesubprocesses.{bpmn,pnml}` — used by `test_equality`
- `tests/transform/assets/diagrams/{bpmn,pnml}/e2e_*.xml` — used by the e2e suite

If you wire any example here into a test, move it back next to the fixtures it
supports so it cannot silently drift out of sync with the code.
