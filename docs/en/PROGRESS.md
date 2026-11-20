# Progress

> 🌐 [Português](../pt-br/PROGRESS.md) · **English**

**What this is.** The project's story so far, phase by phase: what was built, what
was tested in game, what turned out to be closed. For the vision see
[CAREER_MOD](../guides/CAREER_MOD.md); for the lever-by-lever map see
[MOD_TOOLKIT](MOD_TOOLKIT.md); the evidence is in
[DISCOVERIES](../project/DISCOVERIES.md). Labels: **verified** (change made, effect
seen in game), **observed** (seen with few runs), **closed** (tested, does not work).

## Timeline

| phase | when | what changed for the player | state |
|---|---|---|---|
| **v0.1.0 and v0.2.0** | 31 Oct | the pipeline: rename, reorder, unlock the whole career; new series from a JSON spec; safe apply (lint, dry-run, backup, verify, rollback); AI grids (pool or fixed list), spec races of 23 cars of one model, a trackday series, the audit of the vanilla career | verified |
| **Test batteries 3–5** | early Nov | where you start (free pick or last), practice length apart from the race, weather and time of day for the race, a mandatory pit stop per event, small fields (8, 12, 16 cars) | observed |
| **Phase 0.2 — rewards** | 6–9 Nov | the career's pay and prizes mapped. Editing payout tables, bonuses or challenge conditions changes only what the screens show; **credits and cars are granted by the server against its own challenges**. What works instead: pay that grows with race length, unlocks by progression, and live vanilla challenges that count races run in our series | closed for prizes of our own; observed for the rest |
| **Phase 0.3 — an own season** | 9–13 Nov | a cup of our own that plays like the vanilla ones, AI pools of one theme, and a second cup built on the game's live challenges (below) | in progress |
| **Phase 0.4 — race format** | 14 Nov | how fast a series' tyres wear, how fast its race clock runs and when its rain starts and ends, each tested in game on a short oval (below). Also the fifth and last test of prizes of our own through the challenges: the screen shows the car we put, the server still counts and pays its own | observed |
| **Phase 0.5 — the AI standard** | 15–16 Nov | the AI of a series no longer leaves the track at the same corner: one global edit of the AI's speed band plus a levelled field at the class ceiling, tried on Brands Hatch GP, Lime Rock, an oval and class A (below) | verified |
| **Phase 0.6 — covering the values** | 16 Nov | every field a series, an event and its override can set was tried in game across its range, in a bench of one-field series: what works, what has no effect and what is not safe (below) | verified |
| **Phase 0.7 — texts, locks and groups** | 16–17 Nov | the car list cut by year, PI band, blocklist and class, the practice length by laps or a timed free practice, the series points set by a table per position, the practice clock to the minute, and the text a locked series shows (below). Also what **does not work**: descriptions, a cup's practice limit and a ladder's label show nothing on screen | verified / observed |
| **Phase 0.8 — own art** | 18 Nov | a series can show **a poster of our own**, under its own name, installed by the mod's tool with plain Python; several posters go in at once, and a lost poster (after a Steam update) only leaves the card without art (below) | observed |
| **Phase 0.9 — intro video, car select and the install's file index** | 19 Nov | a series can play **an intro video of our own, encoded by us, under its own name**: the game reads a new install file once its path is in the install's file index (`hash.manifest`), whose hash we now compute; the first-car selection does not work on our series, so it is switched off (below) | verified / observed |

## Phase 0.3, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| A series of ours with **several events** runs in sequence, adds series points per driver, is done after the last event | seasons made of multi-race series | verified | D62 |
| **The game reads the AI roster from the cache**, not the install; the AI sits at the roster window's ceiling | AI grids rebuilt with the normal apply tool, no install edits | verified | D60, D61 |
| **The game's PI scale** (C 500, B 600, A 700, S 800, R 900) is not the catalogue's PI column | correct caps and windows | verified | D63 |
| **One AI roster per class** keeps the field inside the player's class (German only, C to S) | class series with an honest field | verified | D64 |
| **A closed pool of hand-picked models** gives a grid of only those models | one-make, one-brand, themed championships | verified | D65 |
| A series' own car list **does not filter** the roster document | the roster must be written in the document itself | closed | D66 |
| **A vanilla roster document with an identical copy can be freed** (point its event at the copy) and reused as a pool of ours | own pools at scale: 313 documents are freeable | verified | D67 |
| **Own AI pools work at every size tried**: 4, 12 (American only), 21 (Italian only) and 37 models (2010s only) each filled the whole grid with that theme, after 8 more vanilla documents were freed in one go with the hub and online intact | themed championships by country, make or decade | verified | D68 |
| **Our series count toward the game's own challenges and the real prize arrives**: laps, track and car count one for one; ten races in a Mustang gave the Mustang; a win at Suzuka in a Nissan unlocked the Nissan; ten laps at Daytona in a Ferrari gave a Ferrari 488 GTB. The progress lives on the server: after reopening the game the screen shows 0% until the first race of the session | a series can be built to serve a live challenge | verified | D69 |
| **A challenge on a track segment score counts by the track alone and pays a car**: the live "segment score of 8 or more at Daytona Sports Car" completed while finishing a series of ours on that track and delivered a Porsche 911 RSR; it is the only segment challenge still active | one series can serve more than one live challenge | verified | D71 |
| A roster document of 46 slots still showed **24 drivers** | grids above 24 stay closed for now | observed | D70 |
| **First season, "German Ovals"** (6 series in 3 groups, in a cup of its own): the cup shows, the second group stays locked until the first is done, the German-only AI sits in the player's class | the first playable season | first group played; groups 2–3 not yet | — |
| **Second season, "Challenge Tour"** (a cup of five groups, one per live challenge, each with its own car list and one-theme AI): applied in game, the cup shows; the Suzuka and Daytona groups were played end to end (all-Japanese and all-Ferrari AI; the win and the laps counted; the Nissan, a Ferrari 488 GTB and a Porsche 911 RSR arrived) | a season that follows the game's monthly challenges | two groups played; three still to play (they need cars the player does not own yet) | D69, D71 |

## Phase 0.4, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| **A series' tyre wear scale works** (with wear switched on in the player's own difficulty): 6 against 1 over 10 laps made the car lose grip at the end; the % damage readout barely moved, so it is a poor measure. The game itself only uses 1, 3, 4 and 6 | a series can set how fast tyres fade; sprint 1, long 3 or 4, hard 6 | observed (one run each, by feel) | D72 |
| **The race clock runs from the event override, not from the series default**: the pair of keys `TimeOfDayTimeScale` and `TimeOfDayTimeScaleOverride` in the event override made a 10-lap oval race go from afternoon to night (144 faster than 60); the series default alone (24, 60, 144) moved nothing. A start at 22h also works | a day-to-night race in a few minutes; sunsets on a schedule | observed (by eye) | D73 |
| **Weather has its own block for practice and for the race**: rain in practice only and rain in the race only both worked in the same series | dry practice and wet race, or the reverse | observed | D74 |
| **A weather forecast's body can be edited, and its phase times are real seconds**: phases retimed to 100 s and 50 s followed the edit in a 300 s race, and a phase changed to clear sky showed up. A 20 s transition to clear sky dried the track at once, far too abrupt | rain that starts, peaks and ends on a schedule; use a long transition or a middle phase when it clears | observed (by eye) | D74 |
| **Our test series differ from the vanilla ones** in the AI's behaviour switches (the rubber band is off, a slot-car start is on) and in some series defaults, because they are copies of one bench series | results from the bench describe a bench AI; the vanilla block is the one to use in a season | audit | [SERIES_FIELD_VALUES](../reference/SERIES_FIELD_VALUES.md) |

Every value the vanilla series use, field by field, is in [SERIES_FIELD_VALUES](../reference/SERIES_FIELD_VALUES.md).

## Phase 0.5, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| **Narrowing the AI's per-driver speed band** (two keys of the AI statics file) cut its off-track errors; no track overrides them, so it holds everywhere | one edit fixes the AI leaving the track in every series | verified | D76 |
| **A higher off-track speed limit** makes the AI recover faster after leaving the track; with three more recovery keys raised together it also loses less control | a gentler recovery | observed | D77, D86 |
| **A levelled field at the class ceiling** puts all 23 AI cars at one PI on chosen models, in class S and class A; the model still sets the pace (four slow models lap 4–7 s behind) | class series with an honest, even field; slow models can be swapped | verified | D78 |
| The series' **AI difficulty label and slot count do not act**; its damage and wear values were masked by the player's preset | do not use them as levers for the AI | verified (grid, pace); observed (damage, wear) | D79 |
| **A new per-track file in the AI statics zip is read** by the game | tune one track alone | verified | D80 |

## Phase 0.6, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| **Laps, start hour and minute, the clock-speed pair and the start type** hold across their range in the event override; a **performance cap of 300** in the override stops a car above it | per-event laps, time of day and start; a real gate on the car | verified | D81 |
| **The AI roster document decides the grid**: an open class, a cap of 0 and the series' own slot counts change nothing; a generator changes the start type only | to change the field, write the roster document | verified | D82 |
| **Weather by forecast id** works for the race and for the practice (overcast, clear, storm, partly cloudy); a one-phase forecast with five skies started clear in four races out of four | the sky per event; the order of the skies may be the lever | verified (ids); observed (first sky) | D83 |
| **The build phase, an event gate and a series gate** work; a series typed as a reward showcase completed and paid nothing | a season that skips the build screen and unlocks in order | verified | D84 |
| A 30-minute practice and the skip-lap flag **do nothing** here; the career has **no qualifying**; two generators dropped the connection, one crashed, and an empty roster document crashes the race | a list of what not to use | verified (no effect); observed (generators) | D85 |

## Phase 0.7, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| The **practice start hour** is its own field, apart from the race hour; the **start minute** works too (30 and 15) | practice and race at different times of day, to the minute | verified | D87, D90 |
| **0 practice laps** give one lap and then a 10-minute free practice; 5 laps give 5; the practice time limit shows only in a free practice; two required stops demand two | the length of the practice per event | observed | D95 |
| A **blocklist** offered 635 cars without the named one; a **class** filter alone offered only that class; class and accept list intersect; the strict severity showed nothing | exclude cars by name or restrict by class, no accept list needed | observed | D96 |
| The four **AI behaviour switches** of a series' race act one by one: catch-up off loosens the back of the field, slow-down off gives less separation from slow cars, proximity off makes the AI less contact-seeking; position spread off changes nothing | a looser or tighter AI field per series | observed | D97 |
| **Year, price and PI ranges of the car list** cut what the career offers, with an empty blocklist and class Any (the PI band is on the game's scale; the price field is not in the catalogue's unit) | a series for old or recent cars, or a PI band, without naming cars | observed | D88 |
| The **points table** of an event decides the series points by finishing position; the lap-target field shows no effect | a series that pays its own points per position | observed | D89 |
| One required stop in the override makes the race demand one stop; the five AI switches of the practice block did not change the race; the Modern NASCAR slot-car start looked like the others | a stop per event; the practice switches stay as in vanilla | verified (stop); observed (rest) | D90 |
| A cup's practice limit, a ladder's label and a ladder's completion list **show nothing** on screen | nothing to ship from them | observed | D91 |
| The **description** of a series, a ladder and a cup is not drawn by any career screen, the vanilla ones included | the name is the only visible text | observed | D92 |
| The **lock text** of a series locked by another series, a ladder or an event is our own text on the card, up to 249 characters (wrapped; the card grows); an empty value shows a missing-text marker; a lock by **driver level** always shows the game's message | clear, own-language reasons for a lock | observed | D93, D94 |

## Phase 0.8, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| A series' **poster** (`ImagePath`) and a ladder's image change the art on their cards; the series' banner and button fields changed nothing seen | point each series and ladder at fitting art | observed | D98 |
| **Our own poster art** shows on a series card: a new entry, under its own name, in the game's poster archives, in the vanilla entry shape (4096-byte grid, data-offset field); Deflate is accepted, so no Microsoft runtime is needed | every series of the mod with its own poster | observed | D99–D102 |
| Several posters written in one go, and one removed, all behave; a series whose poster is missing shows an empty card body and nothing breaks | install every poster in one step; losing the art (a Steam update) is harmless | observed | D103, D104 |

## Phase 0.9, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| A series' own **`IntroVideoPath`** plays that video on entry, with no other field; the colours list (`IntroCarColors`) alone changes nothing; a **ladder's** video field showed nothing | a custom series with an intro movie, picked from the game's own videos by name | observed | D105 |
| The **first-car selection** (`FirstCarSelectEnabled` true) lists `FirstCarSelectCars`, but confirming a car raised an error back to the menu on our series, even for a car the player owns and the series accepts; with it **false** the screen is gone, the video still plays and the race runs normally | keep the video, drop the broken screen; offering a choice of cars is the normal selection of the series' car list (three accepted cars are all listed) | observed | D105, D106 |
| The intro is a **3D scene picked by the video's name**, with its own music and narration; an unknown name falls back to a default scene. With `PlayIntroVideoFullScreen` **true** the series plays the `.bk2` itself, full screen, with no scene and no narration | a plain intro video we control | observed | D107, D108 |
| A `.bk2` under a **new name** gave a black screen; overwriting a video no game data names played the new content | own content without touching any vanilla series video | observed | D109, D111 |
| **The install's file index**: `media\base\hash.manifest` lists every file and folder the game may read, keyed by a hash of the path that we rebuilt for all 5,188 records of both indexes; adding a record made the new-name video play | **new files in the install** (videos today; any loose file the game looks up by path) | verified | D110, D112, D113 |

## What is next

State labels: **viable** (the mechanism is known), **to test** (plausible, needs a controlled run in game), **not possible**
(decided by the game or its server, not by the content data).

| item | why | state |
|---|---|---|
| **Own AI pools at scale** | one roster per series on the freeable documents (make, decade, country) | viable |
| **Entry path at E and D** | 209 of 711 cars are in no event; E (31 of 50 used) and D (50 of 106) are the worst served; short series for them, with an AI band that keeps the field in class | viable |
| **Car × event matrix** | a list that puts every car in at least one event turns the catalogue into the career; numeric limits (year, power) are untested | viable, partly to test |
| **Permanent event list** | the timed (Featured) content has no permanent home; re-parenting a series with fresh ids is proven, synthesising its lists is the open part | viable |
| **Race format** | tyre wear scale, race clock speed and weather timing are proven (Phase 0.4); fuel, qualifying, the AI's behaviour flags against the series' ones and a smooth clear-sky transition are still to test | partly done, rest to test |
| **Career tyre compound** | per-mode lists in the client flags set the default tyre for online modes but not the career; adding a career item is one entry | to test |
| **Grids above 24 cars** | no precedent: every vanilla document asks for 23 AI + the player ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) 8) | to test |
| **Own intro video** | proven end to end with a copied video (D113): install the `.bk2`, add its index record, point the series at it in full screen ([INTRO_VIDEO](../reference/INTRO_VIDEO.md)); our own clip, encoded to Bink 2 revision `KB2j`, plays in game with its sound (D114, D118); one command encodes, installs and indexes it; the sound comes out from one side only | observed |
| **New files in the install** | the file index is solved ([INSTALL_INDEX](../reference/INSTALL_INDEX.md)): other loose files the game reads by path (textures, sounds, scenes) may now be added instead of overwritten; each kind needs its own test | to test |
| **Own art per series** | proven in game (D99–D104): a poster of our own per series, written by the mod's tool in plain Python; left: the release step for players and the art itself | viable |
| **Other languages** | new strings go into the pt-BR table only; the other 20 locales have no keys yet. Decided: done at the mod's release, copying the keys of the real content to every language (names translated as a draft, English as the fallback) | at release |

**Not possible, do not repeat:** a real Qualifying (D33), prizes of our own and payout edits in the cache or install files
(the server grants them), manufacturer affinity (a server value; the substitute is the one-make series), physics, the
account economy and global AI switches that also reach multiplayer.

## How to help

- **Run the pipeline on a copy** and report what breaks: [GETTING_STARTED](GETTING_STARTED.md) takes about 15 minutes and never
  touches the game.
- **Build a series** from a spec and open an issue with the spec: a decade, a country, a one-make grid, an entry-class ladder.
- **Settle an open question**: each item in [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) names the experiment that decides it.
- **Improve a guide** with a symptom you hit and its cause: [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md).

## Reading the evidence

Findings marked *observed* rest on one or two runs. If your result differs, open an
issue with the numbers (see the README, "Contributing"). Release history:
[CHANGELOG](../../CHANGELOG.md).
