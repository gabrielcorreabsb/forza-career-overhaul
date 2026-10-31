# Concepts

> 🌐 [Português](../pt-br/CONCEPTS.md) · **English**

How Forza Motorsport (2023) stores its career, and how this project changes
it.

## 1. Where the game reads content from

```mermaid
flowchart LR
    S["CMS server"] -->|"downloads snapshots"| C["CmsCache<br/>%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache"]
    I["install media/pcfamily/cms<br/>(seed only)"] -.->|"base content not in cache"| G["game"]
    C --> M["cache-manifest.json<br/>(encrypted index)"]
    M --> P["prod/&lt;snapshot&gt;<br/>(plaintext manifest:<br/>Path, Size, Checksum)"]
    M --> B["blob &lt;bucket&gt;/&lt;SHA256&gt;<br/>(ZIP of encrypted entries)"]
    P -->|"Checksum picks the entry"| B
    B --> E["entry payload<br/>AES-128-CBC over gzip"]
    E --> X["plaintext<br/>JSON / XML / .str"]
    C --> G
```

- The **CmsCache is the runtime source**. Editing the install or `mediapc/`
  has no effect.
- There are **two snapshots** (`20251124t234605pkod` old, `20260923t185113xwyk`
  live) with same-shaped blobs. Entries are matched **by Checksum**, never by
  name or mtime.
- Every `Size`/`Checksum` describes the **encrypted** bytes.

## 2. How a mod is applied (Strategy S)

```mermaid
flowchart LR
    SP["spec / generator"] --> K["kit: plan.json + .enc"]
    K --> L["plan_lint"]
    L --> D["cache_edit --dry-run<br/>(writes marker)"]
    D --> A["cache_edit --verify<br/>(game closed)"]
    A --> W["blob rewritten in place<br/>prod/* Size+Checksum<br/>cache-manifest re-encrypted"]
    A --> LG["patches/ledger.jsonl<br/>+ backup"]
```

**Strategy S**: blobs are content-addressed (`name == sha256(content)`), but
the game accepts a blob whose name no longer matches its content. So we keep
the file name and update only `Size` and `Checksum` in the manifests. `Path`
and `Id` are never changed. Each changed entry is re-encrypted with the
**current encrypted payload as template**, so the gzip settings and every
untouched entry stay byte-identical.

## 3. The career model (`BuildersCupScheduleDataV4.json`)

```mermaid
flowchart TD
    CH["Championship 500 (career)"] --> CUP["cup<br/>(ChampionshipCupData)"]
    CUP -->|"LadderOrderData = order"| LAD["ladder<br/>(ChampionshipLadder)"]
    LAD -->|"OrderData = order"| SER["series<br/>(ChampionshipSeriesData)"]
    SER -->|"OrderedEventIds"| EV["event<br/>(ChampionshipEventData)"]
    EV -.->|"ID == EventDataId"| OV["BCEventOverrides.json<br/>(race rules, AIFileName)"]
    SER -.->|"SeriesId"| XS["BCSeriesSelectableCars.xml<br/>(required entry)"]
    SER -.->|"Name = IDS_ key"| ST["LocStrings_pt-BR.str"]
```

- Championship **1** (Featured Multiplayer) lives in
  `RacersCupMetaDataV4.json` and is never touched (`plan_lint` enforces it).
- Invariants: `ladder.OrderData == ids of its series`, `OrderedEventIds ==
  events` and unique ids. The save marks completion by `EventDataId`, so
  **event ids are never reused** (`patches/ids_retired.json`).
- Custom ranges: series ≥ 20000, events 65897900–65899999.

## 4. Glossary

| term | meaning |
|---|---|
| **snapshot** | one server version of the content (`prod/<name>`); kits are snapshot-bound |
| **ContentGroup** | GUID grouping logical files; a group maps to one blob per snapshot |
| **logical file** | an entry such as `BuildersCupScheduleDataV4.json` inside a blob |
| **payload** | the encrypted bytes of one logical file (AES-128-CBC, IV=0, over gzip) |
| **template** | the current encrypted payload, passed to `cmsoracle enc` to keep its settings |
| **Strategy S** | keep blob names, update `Size`/`Checksum` only |
| **kit** | `patches/<kit>/`: `plan.json` + `.enc` payloads + the kit's notes file |
| **plan** | list of targets for `cache_edit.py` (`bytes`, `json`, `json_raw`) |
| **IDS_ key** | localized-string key; new keys = `IDS_<md5("MC44|<label>")>` |
| **spec** | `specs/<name>.json`, declarative description of a new series |
| **ledger** | `patches/ledger.jsonl`, one line per real apply |
