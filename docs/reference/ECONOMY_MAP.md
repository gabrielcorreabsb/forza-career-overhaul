# ECONOMY_MAP - how career payout, prizes and progression fit together

Public map of the career economy: file names and conclusions only. The
detailed per-file tables (field names, counts, value ranges) live in the
lab audit, generated read-only from the live cache. Scope labels follow
`MODDING_SURFACE.md`: **career** means a kit can touch it per series,
**global** means one value for every mode.

> **Status so far: editing the cache's payout tables (the career base cell of a track and car class, and the cup's wager table) changed, at
> most, what the interface shows, not the credits paid at the end of the race. The one concrete change to the credits we have found is the
> session generator's mandatory-stop demand: with a stop demanded the race finish parcel was 550 instead of 800 and the difficulty parcel 250
> instead of 350 (one field, both directions, one series, observed).**

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

**What the post-race screen shows (observed).** The credit arrives as parcels: Practice (only if the practice was done), Race finish, a VIP
parcel equal to the sum of the base parcels (the VIP multiplier of 2), a Difficulty bonus and a Rule-set bonus. The last two appeared on a
top-3 finish and were absent on a sixth place.

**What editing the cache's tables did (observed).** Two edits were tested, one at a time, on a bench series with a fixed car, finish
position and settings:

| edit | what the pre-race screen showed | what the credits paid did |
|---|---|---|
| the career base cell of the series' track and car class, doubled | new numbers (the podium bonus changed) | **unchanged** (two comparisons, two generators) |
| the cup's wager table set to 10.0 on every slot | not recorded | **unchanged** |

The start slot (a slot picked and obeyed, or one imposed by the generator) did not change the credits either. The client reads the base
table for its estimate, but the paid credits do not follow it: the payout seems to be computed outside the cache's tables, most likely on
the server (a reading, not proven). A mandatory stop demanded by the session generator lowered the credits in a one-field check: 550 for the finish parcel and 250 for
the difficulty parcel with a stop, 800 and 350 without (same series, same finishing position, both directions). It is the only edit that changed
the paid credits so far; why a stop lowers them is open.

Candidate formula (**hypothesis**): base parcels (practice, finish) x the VIP multiplier, plus a difficulty and a rule-set bonus on a
top-3 finish, rounded to steps of 50. Which input sets the size of the base parcels is open.

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

- **Cannot** (tested): steer the credits of a series through the career base cell of its track and class, or through the cup's wager
  table; set a per-series payout or prize (no series-scoped field exists); touch progression; change a scalar for the career only (every
  scalar is global, so any test must check the Featured control).
- **Cannot, either** (tested in November 2026, see §5): attach a prize to a series of ours by re-pointing a vanilla challenge.
- **Found (one series, observed)**: the session generator's mandatory-stop demand changes the credits paid (see above); other options of the
  generator are candidates to read the same way.
- **Untested**: the global scalar tables (`CreditScalars.json`), which affect every mode.
- **Practical consequence**: balance a series by what the player does (laps, practice, difficulty, finishing), not by editing a payout
  table. The base-table and wager-table edits only change what the screens show.

## 5. Prizes belong to the server (tested, November 2026)

Every attempt at a prize of our own showed the same split: **the client reads the edited data and marks the row
completed, but credits and cars are granted by the server against its own challenge list.**

| test | result |
|---|---|
| a challenge pointed at a series of ours | the race paid only its normal receipt |
| a vanilla car challenge whose only condition is a fresh series of ours | the row showed completed; no car; after a restart it was not completed again |
| the reward showcase series of that car, opened by a series of ours | the showcase opened (a gate on a vanilla series follows our data), but it drives a car already won; it does not grant it |
| a 1,000,000-credit challenge conditioned on our series | the row showed completed; the credits never arrived |
| per-series objectives switched on for a fresh series | nothing shown or paid |
| payout rates and bonus percentages in the install's tunable files (halved or set to 100) | the pay did not change |
| a vanilla series given our content under its own ids | the server's counter for its "complete all series" challenge did not move |
| a live lap challenge with its condition moved to our oval series and its prize swapped for another car (last round, 14/11) | the hub row showed the swapped car (the prize picture comes from the client cache), but the counter never moved on the oval lap: the server counts its own rule (laps on the original track) and pays its own prize |

What does work: a live, unedited vanilla challenge counts the races run in our series (a monthly "5 races in a 2020s
car" paid 75,000 credits, and a clean-laps challenge counted our laps), pay grows with race length, and a series or
group can be gated on another to unlock in order. The career therefore rewards through those, not through prizes
of its own.
