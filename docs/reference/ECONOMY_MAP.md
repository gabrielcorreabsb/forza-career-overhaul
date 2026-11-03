# ECONOMY_MAP - how career payout, prizes and progression fit together

Public map of the career economy: file names and conclusions only. The
detailed per-file tables (field names, counts, value ranges) live in the
lab audit, generated read-only from the live cache. Scope labels follow
`MODDING_SURFACE.md`: **career** means a kit can touch it per series,
**global** means one value for every mode.

## 1. Race payout (credits)

Three layers multiply into the post-race payout:

- **Base table** (`CarCreditScalingTable.json`): one entry per track with a
  value per car class, repeated per game mode (`BuildersCup`, `RacersCup`,
  `FreePlay`, `Rivals`). The `BuildersCup` entry is the career one - the
  only piece of the payout with career scope. Nothing here takes a series
  or event id: the base varies by track x class, not by series.
  In the live data the `BuildersCup` base is nearly flat across tracks (a few
  tenths per class); one track pays roughly ten times the rest, which widens
  the observed range of the table.
- **Scalar tables** (`CreditScalars.json`): named multipliers for AI
  difficulty, race regulations, collision mode, damage difficulty,
  rewinds, skipped practice/qualifying laps and finish position (one
  entry per grid slot), plus rounding (interval + method), gating
  (minimum drivers / minimum placement for rewards) and a VIP
  multiplier. All **global**: no table takes a series, event or track id.
- **Rule presets** (`SeriesRules.json`): named presets carrying a
  `CreditScalar` among driving-assist and session settings.

Candidate formula (**hypothesis**, order unproven): payout = Builders Cup
base (track x class) x difficulty scalar + finish-position bonus x
regulation/damage/rewind scalars x preset `CreditScalar` x VIP
multiplier, rounded by interval/method, subject to the driver/placement
gates. Whether the Challenge-the-Grid wager (section 2) enters the
payout is still open.

## 2. Prizes (cars, credits, suits)

- **Catalog** (`Rewards.json`): lists of car rewards, credit bundles,
  driver suits, liveries, tour unlocks, achievements and a few
  series-level rewards. Each entry carries a `RewardId`; ids are unique
  across lists. Most car prizes arrive immediately, a minority after the
  race.
- **Career linkage**: every career cup carries `ChallengeTheGridData`
  with one wager line per grid position plus a virtual trophy, and one
  `ChampionshipSeriesObjectivesData_N.json` file per vanilla series holds
  challenges whose `Rewards` list points at catalog ids (all references
  resolve - verified). Custom series have no objectives file, so a new
  series inherits the payout table but gets no prize of its own; the
  prize mechanism itself (challenge -> catalog id) is proven, only new
  content is blocked.

## 3. Progression (car and driver levels)

- **Car** (`LevelConfigurationV3.json`): 50 levels with part unlocks;
  per-point credit value and starting points are global scalars.
- **Driver** (`DriverLevelConfig.json`): fixed XP per level, suit rewards
  at 13 levels up to 100, milestone rewards beyond. Both progressions are
  **global** account state - outside the reach of a series kit.

## 4. What a series kit can and cannot move

- **Can**: pick the payout base by choosing track and car class; attach
  prizes only by re-pointing an existing vanilla challenge (out of mod
  scope - it edits vanilla content).
- **Cannot**: set a per-series payout or prize (no series-scoped field
  exists); touch progression; change a scalar for the career only (every
  scalar is global, so any test must check the Featured control).
- **Cheapest tests first**: scale one Builders Cup base cell (single
  track x class) and observe the career payout vs Featured; then zero
  one wager bonus to settle whether the wager enters the payout.
