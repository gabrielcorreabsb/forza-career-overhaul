<!-- docs_check: historical -->
# Index: which doc to read for each task

One-page map, grouped like the folders. Default reading order:
[GETTING_STARTED](en/GETTING_STARTED.md) → [CONCEPTS](en/CONCEPTS.md) →
[PIPELINE](en/PIPELINE.md) → the doc for your task. Overview: [README](../README.md).

Bilingual pairs (`pt-br/<DOC>.md` and `en/<DOC>.md`, same file name) exist only
for the essentials: `PIPELINE`, `GETTING_STARTED`, `CONCEPTS`, `MOD_TOOLKIT`. Every other doc is
English-only.

## Start

| task | doc | why |
|---|---|---|
| First time (15 min, on a copy of the cache) | **[en/GETTING_STARTED](en/GETTING_STARTED.md)** ([PT](pt-br/GETTING_STARTED.md)) | requirements, oracles, inventory, dry-run, series from a spec |
| Understand the cache, Strategy S and the career model | **[en/CONCEPTS](en/CONCEPTS.md)** ([PT](pt-br/CONCEPTS.md)) | diagrams and glossary |
| Apply or revert a mod on the CmsCache | **[en/PIPELINE](en/PIPELINE.md)** ([PT](pt-br/PIPELINE.md)) | golden rules (game closed), `--dry-run` then `--verify`, rollback and verification |
| See what the mod can do today and how sure we are | **[en/MOD_TOOLKIT](en/MOD_TOOLKIT.md)** ([PT](pt-br/MOD_TOOLKIT.md)) | levers by pillar, recipes, what is closed |

## Tutorials (step by step)

| task | doc | why |
|---|---|---|
| Rename a game text | **[tutorials/01_rename](tutorials/01_rename.md)** | `.str` via `str_edit.py` plus a `bytes` kit |
| Reorder cups, ladders, series | **[tutorials/02_reorder](tutorials/02_reorder.md)** | `LadderOrderData` / `OrderData` |
| Create a new series | **[tutorials/03_new_series](tutorials/03_new_series.md)** | spec, `build_series.py`, lint, dry-run, apply |
| Change the AI grid | **[tutorials/04_ai_grid](tutorials/04_ai_grid.md)** | summary; the model is in `guides/AI_GRIDS.md` |

## Guides (by goal)

| task | doc | why |
|---|---|---|
| Common career: model, ids, what to touch with which tool | **[guides/CAREER_BASICS](guides/CAREER_BASICS.md)** | the basics, before touching any series |
| AI: roster targets, pool or list, PI band, building a grid | **[guides/AI_GRIDS](guides/AI_GRIDS.md)** | the series' AI list **plus** the install-only `AIField` document; `build_aifield.py` |
| A multi-class grid in any series | **[guides/CUSTOM_RACE](guides/CUSTOM_RACE.md)** | modes, class scale, PI band, recipe, test protocol |
| What the career mod is, its stages and the series that already run | **[guides/CAREER_MOD](guides/CAREER_MOD.md)** | the vision (FM4 × GT4), stage table, worked examples |
| A trackday series, worked example | **[guides/CIRCUIT_EXPERIENCE](guides/CIRCUIT_EXPERIENCE.md)** | ids, timeline, which document is active |
| Symptom → cause → fix | **[guides/TROUBLESHOOTING](guides/TROUBLESHOOTING.md)** | consolidated diagnostics |

## Reference (the format)

| task | doc | why |
|---|---|---|
| Know what can be modded, where the game reads it, with which tool | **[reference/MODDING_SURFACE](reference/MODDING_SURFACE.md)** | per area: layer, format, tool, scope (career / global), status |
| Know how career payout, prizes and levels fit together | **[reference/ECONOMY_MAP](reference/ECONOMY_MAP.md)** | payout layers, prize catalog, what a series kit can and cannot move |
| The career tree, ids, ordering, gates | **[reference/CAREER_MODEL](reference/CAREER_MODEL.md)** | cup, ladder, series, event; Builders Cup vs Featured |
| How one event/race is defined | **[reference/RACE_SYSTEM](reference/RACE_SYSTEM.md)** | laps (the override wins), practice that sets the grid, start, overrides |
| Cars, classes, PI and which cars a series accepts | **[reference/CARS_AND_PI](reference/CARS_AND_PI.md)** | classes, PI bands, acceptlist, usable/denied/swap |
| Look up a field of a career/Featured record | **[reference/SCHEMA_REFERENCE](reference/SCHEMA_REFERENCE.md)** | field-by-field catalogue, defaults, evidence labels |
| Files, counts, id ranges and derived tables | **[reference/DATA_REFERENCE](reference/DATA_REFERENCE.md)** | tree, record sizes, identity rules |
| A new series — the why of each step | **[reference/SERIES_CHECKLIST](reference/SERIES_CHECKLIST.md)** | ids, series, ladder, events, overrides, car registry, `.str`; the standard path is [`../specs/README.md`](../specs/README.md) + `build_series.py` |
| Terms | **[reference/GLOSSARY](reference/GLOSSARY.md)** | vocabulary |

## Data (tables generated from your game)

| task | doc | why |
|---|---|---|
| Cars, tracks, classes and enum values | **[data/CARS](data/CARS.md)**, **[data/TRACKS](data/TRACKS.md)**, **[data/ENUMS](data/ENUMS.md)** | regenerate with `inventory.py` then `audit_career.py` |

## Project

| task | doc | why |
|---|---|---|
| Where the project is and where it goes | **[project/PROJECT_STATUS](project/PROJECT_STATUS.md)** | goal, what works today, findings, now / next / later, how to help |
| The findings and what they enable | **[project/DISCOVERIES](project/DISCOVERIES.md)** | discovery log with status |
| Unanswered questions | **[project/OPEN_QUESTIONS](project/OPEN_QUESTIONS.md)** | every hypothesis with the test that would settle it |
| Aggregate findings of the vanilla career audit | **[project/CAREER_AUDIT](project/CAREER_AUDIT.md)** | counts, patterns, anomalies |
| What is NOT in the repo (Forza Mod Tool, key) and how to get it | **[project/THIRD_PARTY](project/THIRD_PARTY.md)** | third-party material kept out; licenses in `../LICENSE`, `../LICENSE-DOCS.md`, `../NOTICE.md` |
| A project decision (ADRs) | **[ADR-001](project/decisions/ADR-001_strategy_s.md)**, [ADR-002](project/decisions/ADR-002_checksum_mapping.md), [ADR-003](project/decisions/ADR-003_mediapc_discontinued.md), [ADR-004](project/decisions/ADR-004_install_vs_runtime.md), [ADR-005](project/decisions/ADR-005_cipher_template.md), [ADR-006](project/decisions/ADR-006_grid_start_shapes.md) | Strategy S, Checksum mapping, mediapc, install vs runtime, cipher template |
| The role of each script | **[../_tools/TOOLS.md](../_tools/TOOLS.md)** | pipeline / generation / inventory / tests |
