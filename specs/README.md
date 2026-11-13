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
| `events[].laps`, `practice_seconds`, `name`, `set` | | event field overrides / ajustes do evento; `laps` is written to both the event's `NumberOfRequiredLaps` (the **practice** laps) and the override's race `Laps`, so a different practice length needs a step after the build |
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

## Round mode / Modo rodada

**EN** — `python _tools\build_series.py --round <round.json>` builds **one kit**
holding a control series and its variations, all cloned from a series that is
already in the cache (the *base*), plus optional renames/removals on the tree
around it. Same pipeline as `--spec`: lint, `--dry-run`, apply with `--verify`.
`--spec` and `--round` are separate modes; `--spec` keeps producing the same
bytes as before.

| field | required | meaning |
|---|:-:|---|
| `kit` | ✓ | kit folder name |
| `title` | ✓ | kit title |
| `question`, `mask`, `min_condition`, `refutes` | ✓ | the four "what is it for" answers, rendered into the notes file; the build refuses without them |
| `group` | ✓ | existing ladder id, **or** `{name, donor, cup}` (+ optional `id`, else the next free ladder id) to clone one (`cup` = existing id or `{id, donor, name}`) |
| `base` | ✓ | `{series, event?}`: the donor series and, by default, its only event (declare `event` when it has more) |
| `ops[]` | | applied before the series: `rename_cup`, `rename_ladder` (`{id, name}`), `remove_series`, `remove_ladder`, `remove_cup` (`{id}`) |
| `series[].id`, `.name`, `.event_id` | ✓ | new series/event ids; the name must be `Test: <variation> [<id>]` with the same id (`event_id` is for one-event series; use `events` instead for 1–5 events) |
| `series[].events` | | optional 1–5 events `[{event_id, track?, laps?}]` (instead of `.event_id`): each entry clones the base event (or that track's donor event) and an override with ID = event id, in array order; `laps` sets practice + race laps; every event gets the base PointSpread table |
| `series[].track` | | target track; needs a `donor_event` (or a base event) on that track |
| `series[].event`, `.override`, `.series_set` | | **only what changes**. Dotted keys edit nested fields (`FeatureRace.Laps`); a path that does not exist is an error unless the variation declares `"create": true` |
| `series[].donor_event`, `override.donor` | | clone an event/override from another track (an override carries its track, so it cannot cross tracks) |
| `series[].cars` | | optional `{acceptlist, class?, division?}`: the XML entry holds the declared car ids and the series' `SelectableCars` points at them (`Acceptlist` + the given class/division, each defaulting to the donor's when omitted); without it the entry clones the donor list and `SelectableCars` stays untouched |
| `series[].ai_cars` | | optional `{acceptlist}`: the series' `AISelectableCars` holds the declared guids (`{"Acceptlist": [...]}`); without it the series keeps the donor's `AISelectableCars` untouched |
| `aifield` | | optional list of 1–12 definitions (`specs/aifield/<name>.json`): each one is built with `build_aifield.py --cache-plan` and merged into the same plan, so one kit frees a document and rewrites it as a pool; without it the plan is byte-identical to before |

Refusals: more than 5 series or more than 5 events in one series,
`event_id` together with `events`, a top-level `track`/`donor_event` or a
common `override.donor` with `events`, a name outside `Test: <variation> [<id>]`, an id
already in use or in the retired list, removing a vanilla series (id < 20000)
or a cup/ladder that holds one, an `AIFileName` missing from the manifest,
a `cars`/`ai_cars` block with a missing/empty/non-integer acceptlist, an unknown key, a
class that is not a single letter, or an unknown or always-denied car id, and
any ladder/order invariant that breaks. Removed series/events/cups/ladders are
appended to `ids_retired.json` (sorted, idempotent); the overrides and
`BCSeriesSelectableCars.xml` blocks they leave behind stay orphaned on purpose,
so the diff stays minimal.

Round specs are lab-only: they name series and kits that only exist in a modded
cache. The public export ships the mode, not the rounds.

**PT** — `python _tools\build_series.py --round <rodada.json>` gera **um kit** com
uma série de controle e as variações dela, todas clonadas de uma série que já
está no cache (a *base*), mais renomes/remoções opcionais na árvore em volta.
Mesmo pipeline do `--spec`: lint, `--dry-run`, apply com `--verify`. São modos
separados; o `--spec` continua gerando os mesmos bytes.

| campo | obrigatório | significado |
|---|:-:|---|
| `kit`, `title` | ✓ | pasta do kit e título |
| `question`, `mask`, `min_condition`, `refutes` | ✓ | as quatro respostas da seção "Para que serve" da NOTA; sem elas o gerador recusa |
| `group` | ✓ | id de ladder existente **ou** `{name, donor, cup}` (+ `id` opcional, senão o próximo ladder livre) para clonar (`cup` = id existente ou `{id, donor, name}`) |
| `base` | ✓ | `{series, event?}`: série doadora e, por padrão, o único evento dela (declare `event` se tiver mais) |
| `ops[]` | | aplicadas antes das séries: `rename_cup`, `rename_ladder` (`{id, name}`), `remove_series`, `remove_ladder`, `remove_cup` (`{id}`) |
| `series[].id`, `.name`, `.event_id` | ✓ | ids novos; o nome tem de ser `Test: <variação> [<id>]` com o mesmo id (`.event_id` é para série de 1 evento; para 1–5 eventos use `events`) |
| `series[].events` | | opcional, 1–5 eventos `[{event_id, track?, laps?}]` (em vez de `.event_id`): cada item clona o evento-base (ou o doador daquela pista) e um override com ID = id do evento, na ordem do array; `laps` grava voltas de treino + corrida; todo evento recebe a tabela PointSpread da base |
| `series[].track` | | pista alvo; exige `donor_event` (ou evento da base) nessa pista |
| `series[].event`, `.override`, `.series_set` | | **só o que muda**. Chave com ponto edita campo aninhado (`FeatureRace.Laps`); caminho inexistente é erro, exceto com `"create": true` na variação |
| `series[].donor_event`, `override.donor` | | clonar evento/override de outra pista (o override carrega a pista, não atravessa) |
| `series[].cars` | | opcional `{acceptlist, class?, division?}`: o bloco do XML recebe os ids declarados e o `SelectableCars` da série aponta para eles (`Acceptlist` + classe/divisão dadas, cada uma herdada da doadora quando omitida); sem ele o bloco clona a lista da doadora e o `SelectableCars` fica intocado |
| `series[].ai_cars` | | opcional `{acceptlist}`: o `AISelectableCars` da série recebe os guids declarados (`{"Acceptlist": [...]}`); sem ele a série mantém o `AISelectableCars` da doadora intocado |
| `aifield` | | lista opcional de 1–12 definições (`specs/aifield/<nome>.json`): cada uma é gerada com o `build_aifield.py --cache-plan` e juntada no mesmo plano, então um kit libera um documento e o reescreve como pool; sem ela o plano fica byte-idêntico ao de antes |

Recusa: mais de 5 séries ou mais de 5 eventos numa série, `event_id` junto
com `events`, `track`/`donor_event` de nível de série ou `override.donor`
comum com `events`, nome fora de `Test: <variação> [<id>]`, id em uso ou
aposentado, remover série vanilla (id < 20000) ou cup/ladder que tenha uma,
`AIFileName` ausente do manifesto, bloco `cars`/`ai_cars` sem acceptlist (ou vazia/com
id não-inteiro), chave desconhecida, classe com mais de uma letra, carro
desconhecido ou sempre vetado, e qualquer invariante de ladder/ordem
quebrado. Séries/eventos/cups/ladders removidos entram em `ids_retired.json`
(ordenado, idempotente); os overrides e blocos do `BCSeriesSelectableCars.xml`
que sobram ficam órfãos de propósito, para o diff ser mínimo.

Spec de rodada fica só no laboratório: ela cita séries e kits que só existem num
cache modificado. O export público leva o modo, não as rodadas.
