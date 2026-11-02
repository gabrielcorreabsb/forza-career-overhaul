# Series specs / Specs de série

**EN** — A spec is a JSON file that describes one new career series. Run
`python _tools\build_series.py --spec specs\<name>.json` to turn it into a kit in
`patches/<kit>/`, then apply that kit through the normal pipeline
(`docs/pt-br/PIPELINE.md`). Start from `_TEMPLATE.json`. `examples/` holds a worked
example: `mc55_treino_20004.json` (the maintainers rebuild their reference kit
from it in the private lab).

**PT** — Uma spec é um JSON que descreve uma série nova da carreira. O
`python _tools\build_series.py --spec specs\<nome>.json` gera o kit em
`patches/<kit>/`, e o kit é aplicado pelo pipeline normal (`docs/pt-br/PIPELINE.md`).
Comece pelo `_TEMPLATE.json`. Em `examples/` fica um exemplo
resolvido: `mc55_treino_20004.json` (os mantenedores refazem o kit de
referência a partir dela no laboratório privado).

## Fields / Campos

| field / campo | required | meaning / significado |
|---|:-:|---|
| `kit` | ✓ | kit folder name (`patches/<kit>`) / nome da pasta do kit |
| `title`, `scope`, `requires` | | text for the kit's notes file / texto do the kit's notes file |
| `series.id` | ✓ | new id ≥ 20000, never reused / id novo ≥ 20000, nunca reutilizado |
| `series.name` | ✓ | displayed name; for a test series use `Test: <what is tested> [<id>]`, in English / nome exibido; série de teste: `Test: <o que testa> [<id>]`, em inglês |
| `series.key_label` | | label for the `IDS_` key (default: `name`) / rótulo da chave `IDS_` |
| `series.donor_series` | ✓ | series shell to clone (recommended 601) / série-casca clonada (recomendado 601) |
| `series.donor_xml_series` | | donor entry in `BCSeriesSelectableCars.xml` (default: `donor_series`) |
| `series.always_open` | | default `true`: `CloseTime`/`To` = 9999-12-31 |
| `series.clear_entry_criteria` | | default `true`: no requirements / sem pré-requisitos |
| `series.deo` | | merged into `DefaultEventOverrides` / mesclado no DEO |
| `series.set` | | raw field overrides (e.g. `ImagePath`) / campos crus |
| `placement.ladder` | ✓ | existing ladder id, **or** `{id:"auto"\|N, donor, name, cup}`; `cup` = existing id **or** `{id, donor, name}` (new cup at the tail) |
| `events[].id` | ✓ | 65897900–65899999, never reused / nunca reutilizado |
| `events[].track` | ✓ | `SerialTrackId` (see the `PISTAS` inventory page) |
| `events[].donor_event` | | event to clone (default: donor series' event on the same track, else the first on the track) |
| `events[].laps`, `practice_seconds`, `name`, `set` | | event field overrides / ajustes do evento |
| `events[].override` | | `{donor, class_restriction, target_pi, laps, pits}`; `donor` defaults to the first vanilla override on the track with AI |
| `cars.acceptlist` | ✓ | `"showroom"` (682 cars) or a list of car ids / ou lista de ids |
| `cars.class`, `cars.division` | | default `"Any"`, `"Open"` |
| `snapshots` | | default `"all"` |

## Checks / Checagens

`build_series.py` refuses ids already in use, retired ids
(`ids_retired.json` (in the `patches` folder)), or ids outside the custom ranges. It also refuses
an `AIFileName` missing from the manifest and any ladder/order invariant that
breaks. It warns about always-denied cars and about an acceptlist with no cheap
car.

O `build_series.py` recusa ids em uso, ids aposentados ou ids fora das faixas
custom. Também recusa `AIFileName` ausente do manifesto e invariantes de
ladder/ordem quebrados. Ele avisa quando há carros vetados ou quando a
acceptlist não tem nenhum carro barato.

**Not covered yet / Ainda não cobre:** challenges (mc55 GCC/CGD/CHUB), moving an
existing series (mc57), AI roster XML in the install (mc58).
