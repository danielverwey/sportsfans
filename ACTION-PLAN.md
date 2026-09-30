# APEX / sportsfans.co.za — status and action plan

*28 September 2026. Nine sports: seven live as APEX odes, two still as dashboard prototypes.*

Not legal advice: the licence findings below are what the sources themselves state today, checked on 28 September 2026, read by a non-lawyer.

## 1. Where each sport stands

| Sport | Format | Archive | Size (page / data) | Sources and their terms | Risk | Work to do |
|---|---|---|---|---|---|---|
| **Formula 1** | APEX ode, live in `docs/f1/` | 77 seasons, 1,163 GPs, 26,181 results, 78 circuits | 13.6 MB / 7.6 MB | F1DB — CC BY 4.0. Jolpica — **CC BY-NC-SA 4.0** (non-commercial, share-alike). F1.com, Wikipedia as references only. | Low, *if the site stays non-commercial* | Licence lines; mark the F1 data file CC BY-NC-SA |
| **Rugby union** | APEX ode (rebuilt in the motorsport grammar), live in `docs/rugby/` | 3,960 Tests 1871–2026, 47 sides, 371 grounds, 484 careers, 217 coaches | 3.4 MB / 2.5 MB | Nuck's Rugby Archive — **no licence stated** anywhere. Springbok Rugby History (bokhist.com) — **no licence stated**, run by a named South African. Pick & Go — cross-check only. Wikipedia coach lists — CC BY-SA. | Medium until permission is in hand: whole compilations were imported | Two permission emails; keep credits |
| **MotoGP** | APEX ode, live in `docs/motogp/` | 78 seasons, 1,027 GPs, 21,282 results, 71 circuits | 4.9 MB / 4.5 MB | Official results feed and PDFs — Dorna legal notice: "only authorised to use Our Channels for personal purposes"; copying "for any purpose, whether for profit or free of charge" not permitted. 25 outlines traced from their circuit images. Wikipedia for 169 early classifications. | **High**: EU database right + explicit terms; images traced | Replace outlines with OpenStreetMap; decide publish / hold |
| **WorldSBK** | APEX ode, live in `docs/sbk/` | 39 seasons, 1,040 races, 26,564 results, 54 circuits | 5.9 MB / 5.6 MB | Same operator (MotoGP Sports Entertainment Group S.L., Madrid), same notice; 22 traced outlines. | **High** | As MotoGP |
| **Cricket** | APEX ode, live in `docs/cricket/` | 13,823 internationals 1877–2026, men's and women's Test/ODI/T20I; every one with a scorecards; 8,370 players; 560 venues (154 city-only); 58 ICC titles | 14.4 MB offline / 10.5 MB core + 31 MB of yearly scorecard shards | Cricsheet — **ODC-By 1.0**, attributed. Kaggle "Test nations 1877–2025" — results as facts. ICC — facts. No flags or logos. | Low | Done: sharded, converted, audited (`audits/DATA-AUDIT-cricket.md`), 9,183 static pages, grounds listed not drawn |
| **NBA** | Dashboard prototype | 80 seasons, 73,176 games with box scores, 5,106 players, 42,415 player-seasons, 45 franchises, 80 champions | 27 MB / 26.6 MB | FiveThirtyEight nba-elo — CC BY 4.0. Basketball-Reference via Kaggle — Sports Reference: bulk data may not be republished, scraping prohibited, "facts cannot be copyrighted". NBA.com box scores via Kaggle — NBA terms: statistics "only … for legitimate news reporting or private, non-commercial purposes", no scraping. **Team logos are embedded** — NBA Properties' trademarks. | **Logos: must go.** Data: medium (US law protects facts, not databases; the terms bind the scraper, not you) | Remove logos; APEX conversion; shard box scores |
| **Tennis** | APEX ode, live in `docs/tennis/` | 388,665 matches 1968–2026 (ATP/WTA singles, partial doubles), 16,150 players, 9,897 tournaments, 11,043 titles, Wimbledon from 1877 | 17 MB offline / 9 MB core + 44 MB of yearly match shards | Jeff Sackmann / Tennis Abstract — **CC BY-NC-SA 4.0**, attributed directly with the source commit. Wimbledon Compendium — facts. | Low, non-commercial only | Done: sharded, converted, audited (`audits/DATA-AUDIT-tennis.md`), 4,493 static pages, tournaments listed on their surface |
| **UFC** | Dashboard prototype | 790 events, 8,905 bouts 1993–2026, 2,760 fighters, per-fight strike/grappling stats | 10.4 MB / 8.9 MB | UFCStats via Greco1899's mirror (GPL-3 covers his scraper, not the data). Zuffa terms: no scraping, no copying "into a database", personal use only. "UFC", "The Octagon" and the eight-sided cage are registered marks; the prototype's name and masthead mark lean on them. | Medium: facts are free in US law, but a litigious owner and a brand-shaped page | Rename and de-brand; APEX conversion |

## 2. Decisions that cut across all eight

1. **The site is non-commercial, permanently.** Two backbone sources (Jolpica for F1, Sackmann for tennis) forbid commercial use and require share-alike. No ads, affiliate links, sponsorship or paywall anywhere on sportsfans.co.za. Say so in every footer and in the README.
2. **A licences page.** `/licences/` listing every source, its licence or terms, and what that means for reuse of each data file — plus `DATA-LICENCES.md` in the repository. The F1 and tennis data files carry CC BY-NC-SA 4.0; the cricket file carries ODC-By attribution; MotoGP/WorldSBK/UFC/NBA files carry "facts as recorded, sources as stated, no licence granted".
3. **No logos, no marks, no brand-shaped pages.** Team colours and names used descriptively are fine; the NBA logos and the octagon masthead mark are not. Every page keeps its "independent, unaffiliated" line and gains a one-line trademark notice.
4. **Permissions.** Email Nuck (via the GitHub repository) and Grundlingh Enslin (sarugbyfan@hotmail.com): what the site is, non-commercial, credited and linked, may we. Nothing else needs asking; Dorna and Zuffa would not answer usefully.
5. **Publish in tiers.**
   - *Tier A — go live now:* F1, rugby (the moment the emails are answered, or with the credits as they stand if you accept the small risk), cricket and tennis once converted.
   - *Tier B — go live after the fixes above:* NBA (logos out), UFC (renamed, de-branded).
   - *Tier C — your call:* MotoGP and WorldSBK. Options: publish and accept the exposure; keep them as offline editions for friends; or publish with the OSM outlines and the raw data files withheld (the pages still work, the JSON is just not offered as a download).
6. **Data on the wire.** The production shells fetch their archive; the largest of the new four (tennis 61 MB, cricket 42 MB, NBA 27 MB) cannot be fetched whole. Each is split at build time into a core file (results, standings, people, venues, titles — under 8 MB) and detail shards by season (scorecards, box scores, serve statistics, fight statistics) loaded only when a match, game or bout is opened. The offline editions keep everything embedded.

## 3. Bringing the four prototypes into the APEX grammar

The same three movements everywhere; each sport supplies its own idiom.

| | River (I) | Grid (II) | Stage tabs (III) | Opening | Symbolic replay |
|---|---|---|---|---|---|
| **Cricket** | Share of international wins by nation, year by year, with a format lens (Test / ODI / T20I) and a men's/women's switch; the barcode strip marks World Cup and Championship winners | Grounds: real venues (the 560 include location-only records, shown but flagged), as schematic ovals with the pitch, lit in the colours of the side that has won there most | Season · Match · Teams · Players · Grounds · Records · Barcode · Duel | The toss: a coin turning, then "first ball" | The innings worm — runs building over overs from the scorecard where one exists (9,835 matches), a symbolic build from the totals where not |
| **NBA** | Share of wins by franchise, season by season (colours: the 45 identities with their eras) with the Finals winner on the strip | The Court: each franchise as a half-court schematic in its colours, sized by games; arenas as a sub-view (35 modern arenas only, so franchises make the better grid) | Season · Game · Teams · Players · Arenas · Records · Barcode · Duel | Tip-off | Quarter-by-quarter scoring build from the box score (q1–q4 points are in the data), players' lines as the tower |
| **Tennis** | Share of tour-level titles by nation, year by year, on the tour lens (ATP / WTA / both); the strip marks each year's major winners | Tournaments: the majors large, then every event with 20+ editions, each as a court schematic in its surface's colour | Season · Tournament (the draw) · Players · Nations · Courts · Records · Barcode · Duel | The serve toss | The draw building round by round to the final; a match's score building set by set |
| **UFC** | Bouts by division, year by year (colours by weight class), the strip marking title-fight nights | Host cities: events by city, Las Vegas dominant, each as a schematic cage in the colour of the division that has fought there most | Season · Event (the card) · Divisions · Fighters · Venues · Records · Barcode · Duel | The cage door closing | Round-by-round strike and takedown build from the fight statistics; a fight card as the tower |

Each conversion follows the rugby recipe exactly: adapter over the prototype's archive (untouched), F1 app skeleton, sport-specific views, `check_site.js` coverage, an audit report in `audits/`, static entity pages in `tools/sitegen.py`, a card and River miniature on the hub. Rugby took one session; cricket and NBA are of that order; tennis is larger because of the draw view and the sharding; UFC is the smallest.

## 4. Order of work

| Phase | What | Why this order |
|---|---|---|
| **0 — this week, before DNS goes live** | Licences page + DATA-LICENCES.md + non-commercial and trademark lines on every page; correct Cricsheet wording; OpenStreetMap outlines for MotoGP and WorldSBK; send the two rugby emails; decide Tier C | Closes every open rights question on the four live atlases; nothing else waits on it |
| **1 — Cricket** ✅ | Sharded data, APEX conversion, audit, static pages, hub card | Done 28 September: the toss opening, the river of wins by nation on a Test/ODI/T20I lens, grounds listed, scorecards with innings worms, teams, players, records, barcode, duel |
| **2 — Tennis** ✅ | Sharding first (61 MB → core + shards), then conversion | Done 28 September: the serve opening, the river of titles by nation on an ATP/WTA lens, tournaments listed on their surface, draws built round by round with match sheets, players, nations, tournaments, records, barcode, head-to-heads |
| **3 — NBA** | Logos out of the prototype immediately (five-minute fix, do it in Phase 0); conversion later | Rights are workable but need the fix first; box-score sharding is the same job as cricket's |
| **4 — UFC** | Rename, de-brand, conversion | Smallest job; the naming decision matters more than the code |
| **5 — Close** | Hub with eight cards, sitemap, full `check_site.js` and `check_links.py` run, offline editions for all eight, release | |
| **Sweepers (0.5)** ✅ | Every atlas sweeps itself on its own schedule (`.github/workflows/sweep-<atlas>.yml` → `sweep-run.yml`); the reading editions and dated footers are generated from the data so a sweep never leaves them stale; the gate (`tools/gate.py`) refuses changes to history. Rugby's schedule waits for `RUGBY_APPROVED` | |

Go-live for the domain does not wait for phases 1–4: the site is publishable with four atlases after Phase 0, and each later sport is a normal update (RELEASE.md).

## 5. Phase 0 checklist (28 September 2026)

- [x] `docs/licences/` page and `DATA-LICENCES.md`
- [x] Footer line on every atlas and static page: non-commercial · unaffiliated · trademark notice
- [x] F1 data file marked CC BY-NC-SA 4.0 (`docs/data/LICENCE.txt`); tennis and cricket follow with their atlases
- [x] Dorna-derived outlines removed (ring fallback meanwhile); `tools/osm_outlines.py` + the `Circuit outlines` workflow fetch OpenStreetMap geometry on demand
- [x] Tier C decided: both held off the site; clean-room rebuild from Wikipedia (`tools/harvest/wiki_bikes.py` + the `Harvest` workflow) replaces the data
- [x] NBA prototype: team logos removed (monograms in team colours)
- [x] UFC prototype: masthead mark removed, retitled, UFC named descriptively
- [ ] Emails to Nuck's Rugby Archive and Springbok Rugby History — drafts in PERMISSIONS.md, to send
- [ ] DNS records at the registrar; GitHub Pages custom domain; Enforce HTTPS

## 6. Phases 1 and 2 (28 September 2026)

- [x] Cricket: `tools/prepare_cricket.py` (core + 26 shards), `src/cricket/`, `tools/audit_cricket.py` (all checks clean: batting + extras = total in every one of 9,835 scorecards), static pages, hub card, licences entry
- [x] Tennis: `tools/prepare_tennis.py` (core + 59 shards), `src/tennis/`, `tools/audit_tennis.py` (facts hold: Djokovic–Nadal 31–29, Isner–Mahut 665 minutes, Nadal 14 Roland-Garros; source quirks noted), static pages, hub card, licences entry
- [x] Venues listed, not drawn, on rugby, cricket and tennis (NBA will follow the same rule)
- [x] `docs/data/` and `docs/downloads/` left out of git (rebuilt by the deploy workflow); offline editions reproducible byte for byte
- [x] Sweepers for cricket (Cricsheet, daily) and tennis (Sackmann, twice a week): see section 10

## 7. The bikes rebuilt, and the Isle of Man TT (28 September 2026)

- [x] MotoGP and WorldSBK rebuilt from Daniel's Wikipedia-transcribed archives (`tools/prepare_bikes.py`): results, calendars and published standings CC BY-SA 4.0, Wikidata coordinates CC0, OpenStreetMap outlines ODbL stitched into the racing line, F1DB surveys re-keyed by venue name; sponsor titles stripped from Grand Prix names; both published, the hold lifted
- [x] Isle of Man TT built as a new ode (`src/tt/`, `tools/prepare_tt.py`): the river of wins by marque with the war years open, the Mountain Course from OpenStreetMap with 56 named places, the ten-second start, the lap replay, riders, marques, classes, records, barcode, duel; five km/h tables converted and four unreadable averages set aside, all listed in the data
- [x] Contribute address on every page: sportsfans.co.za@gmail.com
- [ ] Run the *Circuit outlines from OpenStreetMap* workflow for `motogp` and `sbk` (Assen, Brno, Sachsenring, Catalunya, Phillip Island, Silverstone, Valencia, Motegi, Sepang and others still show the ring of winners)

## 8. Home links, the outline workflow, the sitemap, and UFC on open data (28 September 2026)

- [x] Every atlas links back to the landing page: the brand, "all atlases" in the strap line, and the footer (`build.py` `production()`)
- [x] `tools/osm_outlines.py` rewritten: three Overpass mirrors with backoff, a 5 km second pass, a route-relation pass for the public-road courses, Snaefell copied from the TT archive, a job summary that lists what was found and what was skipped and why; the workflow now rebuilds `docs/` and deploys, and does both sports in one run
- [x] Workflows moved to the Node 24 action versions (checkout v5, setup-python v6, setup-node v5, upload-artifact v5, upload-pages-artifact v5, deploy-pages v5)
- [x] Sitemap split into an index with one file per atlas (`sitemap.xml` → `sitemap-<sport>.xml`)
- [x] UFC decided: the UFCStats-based prototype is retired; the atlas is rebuilt on Wikipedia (CC BY-SA 4.0) and Wikidata (CC0) — `tools/harvest/wiki_ufc.py` + the *Harvest · UFC from Wikipedia* workflow write `build/harvest/ufc.json`; `tools/prepare_ufc.py` turns it into `data/ufc.json`; `src/ufc/` is the ode (River of bouts by division · Arenas listed, never drawn · Stage: Season, Event as the tower, Divisions, Fighters, Venues, Records, Barcode, Duel; the opening is a fenced ring, not the eight-sided mark); `tools/audit_ufc.py`; static pages in `tools/sitegen.py`; the hub card and the licences entry appear only once `ufc` is in `PUBLISH`
- [x] UFC archive harvested by Daniel's own Wikipedia reader (791 events, 8,917 bouts, 2,786 fighters, 787 article revisions with hashes); `tools/prepare_ufc.py` reads it, `tools/audit_ufc.py` is clean apart from two genuine oddities (a 51-person Apex attendance as recorded; Sakuraba–Silveira refought the same night in 1997); `ufc` published
- [ ] Per-fight strike and grappling statistics are not carried (they only exist in the promotion's own statistics service); the atlas reads results, methods, rounds, times, titles and bonus awards instead
- [ ] NBA: the same route — a Wikipedia harvest of every season's game log is impractical; decide between Basketball-Reference terms (no bulk redistribution) and holding the atlas off the site

## 9. The Dakar Rally, alphabetical order, the favicon (29 September 2026)

- [x] Daniel's changes adopted: atlases, switchers and downloads listed alphabetically; a favicon (`src/hub/favicon.svg` → `favicon.ico`, `apple-touch-icon.png`); hub cards open the atlas in a new tab; every atlas reads River → Stage → venues
- [x] Dakar Rally atlas (`src/dakar/`, `tools/prepare_dakar.py`, `data/dakar.json`): 48 editions 1979–2026 (2008 cancelled), 534 podium places across 8 classes, 430 people, 56 marques; the river of class wins by marque, every route drawn between its named towns over the Natural Earth land, the caravan replayed symbolically, podiums of every class, drivers, marques, classes, records, barcode, duel; static pages for every edition, driver, marque and class; reading edition; licences entry
- [x] The e-mail address no longer printed anywhere: every notice reads "contribute" as the link
- [ ] Wikidata nationality and date of birth for the Dakar people (the prototype carries names only)
- [x] SEO pass (29 September 2026): JSON-LD on every page (BreadcrumbList everywhere; Person / Place / SportsTeam / Organization on entity pages; WebSite + Organization on the hub; WebPage on each atlas; one Dataset per data file on the licences page, for Google Dataset Search); share cards (`src/hub/share/<key>.png`, rendered once by `tools/share_images.js`) with og:image / og:site_name / twitter:card on every page; sitemap `lastmod` from each archive's snapshot date; long-tail careers (fewer than three appearances and no result of note — 5,163 pages) marked noindex,follow and left out of the sitemap; the five biggest directory indexes split into a page per surname initial; preload hints for each atlas's data and app
- [x] Sweeping made one command per atlas (29 September 2026): `tools/sweep.py` (prepare → audit → gate), the gate extended from F1 to every atlas (nothing may disappear; past changes listed for review; `--accept` after review), cricket and tennis prepare scripts read the prototype page directly (`tools/archive_in.py`); two faults found by the first dry run and fixed — `prepare_bikes.py` would have replaced the 53 MotoGP / 47 SBK OpenStreetMap outlines with the prototype's 30 / 28 (now it keeps them), and the TT sidecar marque was chosen by a tie-break Python randomises per run (now the engine maker, deterministically: 84 derived sidecar rows moved from chassis names such as Shelbourne, Ireson, Windle to Honda / Yamaha, one win among them)
- [ ] Search Console: watch the Pages report once it fills (indexed vs discovered-not-indexed), then tune the thin-page threshold; add the property to Bing Webmaster Tools (import from Search Console)
- [ ] Optional: self-host the three fonts (removes the Google Fonts round trip on every page)

## 10. Every atlas sweeps itself (29 September 2026)

Nothing is updated by hand any more. Each atlas has a *Sweep · <atlas>* workflow on its own schedule: read the source → merge into `data/` → gate → rebuild → check every link → commit → deploy. A failed step commits nothing, shows red in Actions and GitHub e-mails you.

| Atlas | Reads | When (UTC) | Proves itself on |
|---|---|---|---|
| Formula 1 | Jolpica, current season | Mon + Wed 06:17, Mar–Dec | the gate's F1 facts (strict) |
| MotoGP | Wikipedia season article | Mon + Wed 07:27, Feb–Nov | last season's rounds and this season's held rounds (≥ 90%) |
| WorldSBK | Wikipedia season article | Mon + Wed 07:47, Feb–Oct | as MotoGP |
| UFC | Wikipedia event articles, last 21 days | Sun + Tue 13:13 | exact round trip of the archive through `prepare_ufc.py` |
| Cricket | Cricsheet, internationals added in the last 7 days (30 on the first run) | daily 04:23 | exact round trip through `prepare_cricket.py` |
| Tennis | Jeff Sackmann's CSVs, current season (and the last in Jan–Feb) | Mon + Thu 09:33 | round trip through `prepare_tennis.py` |
| Rugby union | Nuck's Rugby Archive data file | Mon + Thu 08:43 — **held** | the last two years of Tests (≥ 90%) |
| Isle of Man TT | Wikipedia "<year> Isle of Man TT" | daily 09:53, 25 May–20 June | last year's races (≥ 90%) |
| Dakar Rally | Wikipedia "Dakar Rally" | daily 10:03, 3–31 January | the last two editions (≥ 90%) |
| (browser check) | the whole site in headless Chromium | Mon 12:37 | — |

- [x] `tools/sweepers/` (one reader per atlas + `run.py`), `tools/harvest/wiki.py` (shared Wikipedia reading), `sweep-run.yml` + nine `sweep-<atlas>.yml`; the deploy workflow now checks out the branch tip so a sweep's new commit is what gets published
- [x] The gate's shape check: every new record must carry the archive's own fields and types; F1 allows current-season corrections and says so
- [x] Every reader tested offline against the real archive: remove the newest rounds / races / editions / Tests, sweep them back from a copy of the source in its published format, compare — identical (tennis: identical apart from the order of tied rivalries); a changed layout stops the reader with nothing written
- [ ] **Rugby:** when Nuck's Rugby Archive agrees, set the repository variable `RUGBY_APPROVED` = `yes` (Settings → Secrets and variables → Actions → Variables). Until then the schedule is off and a hand-started run is a dry run. The reader was tested against the file's published field list; its first dry run on GitHub is the first read of the live file — check its report
- [x] First dry run of each (29 September 2026, by hand from Actions). Found and fixed before any schedule fired: the nine workflows shared one concurrency group, so runs queued together were cancelled silently (one group per atlas now); the TT reader missed every race because the article's headings carry sponsors ("RST x D3O Superbike"), and would have added a duplicate "Carole Nash Sportbike Race 1" (class words now come from the archive's own families); the Dakar reader read the old table layout (the article now has winners tables and a podium table per category, both read); the cricket sweeper counted byes and leg-byes as dot balls and so rewrote every re-read scorecard (now as the archive counts). The UFC harvester lost every bout note — the results tables now give a note as a footnote marker in the Notes column, which the cell cleaner dropped, and with the notes went the title and tournament flags derived from them (the marker is now followed to the note's text). The gate now covers the cricket scorecard shards and lists the differing fields of every changed record, and a failed proof reports what the reader saw. Results of the dry runs: F1 found round 15 (Azerbaijan), rugby one Test (Australia 42–38 South Africa, held for `RUGBY_APPROVED`), UFC two records improved within its re-read window (UFC 331's bonuses, gate and champion marker); MotoGP, WorldSBK, tennis, TT, Dakar and cricket nothing new, every proof at 94–100%
- [ ] Not swept: ICC event titles (cricket), player and coach snapshots (rugby; they stay dated), Wikidata nationality/date of birth (UFC, Dakar)

## 11. Navigating within an ode (29 September 2026)

- [x] One shared Stage navigation for every atlas (`src/common/stage.js` + `stage.css`, injected by `build.py`): a season timeline under the era strip, oldest left to newest right, spanning the lens; ‹ › and ← → step seasons, and on the unit tab step races / matches / draws / events, wrapping into the neighbouring season; the sticky status line jumps back to the timeline
- [x] The Back button retraces every view change (the address bar is pushed, not replaced)
- [x] The rule stated: timelines flow forward, lists start at today — the season dropdown says "Newest first", the era-wide race table too
- [x] One tab order everywhere: season · unit · people · teams · venues · records · barcode · duel (rugby, cricket and UFC moved a tab)
- [x] Phone: the tab row fades at its edge to show it scrolls; the era strip and the season strip are taller
- [x] Dakar's unit is the Podium: one class of one edition (the three places, the winner's run in that class, the class edition by edition), the second tab as everywhere; the timeline steps podiums and wraps into the next edition, and the whole-lens view lists every class podium newest first
- [x] Find anything (29 September 2026): one box in every Stage's sticky bar (`src/common/search.js`, `/` focuses it) over every name the atlas knows — people, teams, venues, seasons, races / matches / draws / events / editions — grouped, ranked by how well known the name is among equal matches, ↑ ↓ Enter Esc, opening the view directly. The in-list search on the F1 Drivers and Constructors tabs now filters the ranked list itself rather than only showing chips

## 11. Cricket: every scorecard, full names, published careers (30 September 2026)

- [x] Daniel's harvests merged (`tools/merge_cricket_harvest.py`): 3,988 historical scorecards (the Hugging Face Test, ODI and T20I datasets, 3,934; Cricbuzz, 54) — every men's Test from 1877 and ODI from 1971 now has one, 13,823 in all; the rebuilt register with 767 more names expanded (5 still initials only), 8,735 published career lines from 74 Wikipedia lists; toss filled for 3,931 matches and the last day for 1,743
- [x] Identities: every scorecard player linked to one register entry (harvest link, Cricinfo id, name/side/career, surname and initial); 9 split entries joined, 439 career lines moved from duplicate entries to the player the scorecards record, 355 empty duplicates removed; 45 new identities the register did not have. Audit clean; Bradman 6,996 at 99.94, Tendulkar 15,921 Test runs, Muralitharan 800 wickets come out of the cards exactly
- [x] The ode: historical scorecards with their source credited on the card (no worm, bowler blank where unrecorded, extras total where not itemised, 8-, 5- and 4-ball overs shown as bowled); full names on player pages; the published career beside the recorded figures; career-only players (women's careers before 2003) reachable by search; search knows every alias; strike rates only over innings whose balls were counted (new `sruns` player-season field, also computed by the sweeper); landing card updated
- [x] Licences page, DATA-LICENCES.md and data/LICENCE.txt: the Hugging Face datasets and Cricbuzz credited as "no licence stated" (Daniel's decision, 30 September), Wikipedia lists CC BY-SA, Wikidata CC0, CricketWeb cross-check only
- [ ] Register names Daniel's prototype expanded that look doubtful (e.g. MS Gony shown as Manpreet Singh Grewal) are carried as they are; a review pass is worth doing
- [ ] Canada's and East Africa's 1970s World Cup matches are not in the results list, so those players are known only by their published careers
- [x] Offline editions withdrawn (30 September 2026): `docs/downloads/` is no longer built, the downloads page and every link to it are gone (hub, atlas footers, static-page footers, licences page). The build still writes the single-file editions to `HTML FILEs/` locally as its embedding check

## 12. The Summer Olympics: an ode to the Games (30 September 2026)

- [x] Daniel's prototype (`summer_olympics_atlas_1896_2024.html`) brought in: `tools/prepare_olympics.py` → `data/olympics.json` — 30 Games held (1916, 1940 and 1944 kept as gaps), 5,766 medal events, 17,825 awards, 27,685 named medallists, 166 delegations, 51 sports, every medal table reconciled against the cited comparison table, 1,221 event lineages
- [x] The ode in the APEX grammar: the cauldron opening; the River of gold (or all medals) by delegation, thick as the programme, split at the two wars; the Stage with Games (medal table, the host on the map, the programme, a symbolic replay of the table building event by event, the medallists), Event (the podium with ties and rosters, the event Games by Games, most medals in it), Athletes, Nations, Sports, Hosts, Records, Barcode and Duel (nations or athletes); Section III "The Hosts": every Games on the world map and as a card; the reading edition with every Games' medal table and every podium; StageNav (Games and events) and StageSearch
- [x] Sport, category (men's, women's, mixed, open) and era lenses; colours by the nation of the Games or a chosen delegation; deep links for every view
- [x] Static pages: every Games, every champion and multiple medallist (12,407; a single silver or bronze is named unlinked and lives in the atlas), every delegation, every sport, every event held at three Games or more, every host city; hub card and share image; licences page and DATA-LICENCES (no rings, emblems or pictograms; not affiliated with the IOC)
- [x] Sweeper (`tools/sweepers/olympics.py`, Mon + Thu 11:07 July–September): proves itself on the latest Games' list (≥90% of the archive's awards read back), reads the next Games' list, writes it only when the medal table article reconciles delegation by delegation, marks it provisional while the Games are on and completes it once they close; ids by lineage never move; gate records Games, events and awards
- [x] Audit (`tools/audit_olympics.py`): all checks clean — Phelps 23 gold of 28, Latynina 18 medals, Bolt 8 of 8, Paris 2024 with 329 events, Athens 1896 with 43, the leaders of 1896, 1936, 1980, 2008 and 2024
- [ ] The first scheduled run is the live test of the list reader against Wikipedia's current layout (the sandbox could not reach the API); run "Sweep · Summer Olympics" by hand with "dry run" ticked and read the check line in the summary
- [ ] The 301 historical events the prototype labelled men's by judgement (1900 archery, croquet, early events) carry that label; `tools/olympics_common.py` reads the category from the name, the event article's title or the section, and would call them open

## 13. Rugby: the register, the team sheets, the scorers (30 September 2026)

- [x] Daniel's consolidated harvest merged (`tools/merge_rugby_harvest.py`, batch open-harvest-021): 20,539 players across 28 sides (from 484), the published caps, tries and points of the national lists, 102,812 history rows from 2,321 team sheets and 3,008 sets of named scorers, 2,119 new scoring breakdowns that reconcile to the score (2,837 in all), dates of birth and death from Wikidata for 12,048 people, ten reviewed match corrections (six dates, one score orientation, the 2016 Americas Rugby Championship side as Argentina XV) and one more from the same batch, each listed with its evidence
- [x] The ode unchanged in function and look: the same tabs, views and theme; team sheets fill the match view's line-up towers (shirt order, bench marked), full names, register numbers and dates on the player page, the register searchable, the sources panel and licences page say where each part comes from
- [ ] 2,515 names printed in match sources are still unlinked to a register entry (kept as printed, marked for review); 3,361 team sheets are still missing; 35 scoring breakdowns do not reconcile and were not added
- [ ] Rights: the harvest's own status is "mixed sources, not wholesale cleared" — Wikipedia parts CC BY-SA, Wikidata CC0, the unions' match records cross-checks only with no licence stated; the inherited match compilations still await permission
