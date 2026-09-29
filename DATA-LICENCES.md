# Data licences

What each source publishes about reuse, and the licence that applies to each data file the site serves. The live statement is `docs/licences/index.html` (https://sportsfans.co.za/licences/); this file is its repository copy. Checked 28 September 2026.

The site is **non-commercial for good** — no advertising, sponsorship or paywall — because two backbone sources (Jolpica, Sackmann) permit nothing else.

| Sport | Source | Terms it states | Used for | Data file licence |
|---|---|---|---|---|
| Formula 1 | [F1DB](https://github.com/f1db/f1db) | CC BY 4.0 | circuit outlines, track specifications, supplementary fastest laps | `data/f1.json`: **CC BY-NC-SA 4.0** (attribute F1DB and Jolpica; non-commercial; share alike) |
| Formula 1 | [Jolpica F1](https://github.com/jolpica/jolpica-f1) | CC BY-NC-SA 4.0; API free for non-commercial use | results, sprints, standings | " |
| Rugby | [Nuck's Rugby Archive](https://rugbyarchive.github.io/about.html) | no licence stated (hobby archive) | the ten nations' match archive | `data/rugby.json`: no licence granted for reuse; facts are free, compilations credited; permission being sought |
| Rugby | [Springbok Rugby History](https://bokhist.com/) | no licence stated | Springbok record, player histories, squads | " |
| Rugby | [Pick & Go](https://www.lassen.co.nz/pickandgo.php) | © www.pickandgo.nz, no terms | cross-check only | — |
| Rugby | Wikipedia | CC BY-SA 4.0 | coaching lists | — |
| MotoGP, WorldSBK, Isle of Man TT | Wikipedia (English season articles; the German list of TT winners) | CC BY-SA 4.0 | every result, calendar and published standing; every TT winner and classification | `data/motogp.json`, `data/sbk.json`, `data/tt.json`: CC BY-SA 4.0; attribute; share alike |
| MotoGP, WorldSBK | Wikidata | CC0 1.0 | circuit coordinates and countries | — |
| MotoGP, WorldSBK, Isle of Man TT | OpenStreetMap | ODbL 1.0 | circuit outlines; the Mountain Course and its named places | ODbL |
| MotoGP, WorldSBK | F1DB | CC BY 4.0 | circuit surveys at shared venues | attribution |
| Cricket | [Cricsheet](https://cricsheet.org/register/) | ODC-By 1.0 | scorecards from 2001 (men) / first recorded matches (women); every player figure | `data/cricket.json`, `data/cricket_details/`: ODC-By 1.0 for scorecard-derived parts; attribute Cricsheet |
| Cricket | Kaggle, "Cricket match dataset, Test nations 1877–2025" (kaggle.com/datasets/qammarshahzad/cricket-match-dataset-test-nations-18772025) | licence as stated on Kaggle | historical results (facts) | — |
| Cricket | ICC | published results | ICC event winners and finals (facts) | — |
| NBA (in preparation) | [FiveThirtyEight](https://github.com/fivethirtyeight/data) | CC BY 4.0 | historical results and Elo | attribution |
| NBA (in preparation) | Basketball-Reference / NBA.com via Kaggle mirrors | facts free; bulk republishing not permitted by their terms; NBA statistics for private, non-commercial use | box scores, player seasons | non-commercial |
| Tennis | [Jeff Sackmann](https://github.com/JeffSackmann) | CC BY-NC-SA 4.0 | every ATP and WTA tour-level match from 1968, with statistics | `data/tennis.json`, `data/tennis_matches/`: CC BY-NC-SA 4.0; attribute; non-commercial; share alike |
| Tennis | Wimbledon Compendium | published roll of honour (facts) | champions and finalists before 1968 | — |
| UFC (in preparation) | UFCStats via a public mirror | Zuffa terms forbid scraping and copying; facts are free | fight records | — |

## How the archives stay current

Each atlas is extended by a small reader that runs on a schedule in the site's public repository (`tools/sweepers/`, `.github/workflows/sweep-*.yml`). It reads only the source already credited above for that atlas — Jolpica (F1); the English Wikipedia season, event, race and rally articles through the MediaWiki API (MotoGP, WorldSBK, UFC, the Isle of Man TT, the Dakar Rally); Cricsheet's recently-added internationals and people register (cricket); Jeff Sackmann's `tennis_atp` / `tennis_wta` repositories (tennis); the data file Nuck's Rugby Archive publishes for its own pages (rugby union — held until permission is given). Each run makes a handful of requests with a pause between them and identifies itself (`sportsfans.co.za atlas sweeper (https://sportsfans.co.za/licences/; non-commercial)`). Before writing, each reader must reproduce what the archive already holds from that source; results before the current season are never rewritten. What a sweep adds carries the same licence as the rest of that data file.

Fonts: Google Fonts, SIL Open Font License. Circuit geometry: © OpenStreetMap contributors, ODbL, where used. Code: MIT.

Trademarks: every championship, team, event, venue and manufacturer name is the trademark of its owner and is used only to identify what the numbers describe. No logos are used.

## UFC (`data/ufc.json`)

- **Wikipedia** — the "List of UFC events" article and each event's own article: the results table (weight class, fighters, result, method, round, time, notes) and the infobox (date, venue, city, attendance). Text and tables are CC BY-SA 4.0 (Wikipedia contributors); the results themselves are facts. The archive in use (28 September 2026: 791 events, 8,917 bouts, 787 article revisions) was harvested by Daniel's own reader with every revision id, retrieval date and hash recorded in the data file; `tools/harvest/wiki_ufc.py` and the *Harvest · UFC from Wikipedia* workflow are the equivalent reader for future sweeps, and `tools/prepare_ufc.py` reads either.
- **Wikidata** — fighter nationality, date of birth and height, where the fighter has an article (CC0 1.0); read by the workflow harvester, not yet part of the archive in use.
- Nothing is taken from the promotion's own site or its statistics partner; the earlier UFCStats-based prototype is retired and its data is not carried. Per-fight strike and grappling counts are therefore absent.
- Derived in `tools/prepare_ufc.py` from the transcribed rows alone: the division key from the weight-class label, the method kind from the method text, the title flag from the notes, the elapsed time from round and time (five-minute rounds from UFC 21, July 1999), each fighter's record from the bouts in the archive.
- The data file is **CC BY-SA 4.0**: attribute Wikipedia contributors and share alike. No logos, marks or official artwork; the promotion's names identify the events and nothing on the site is affiliated with it.

## Dakar Rally (`data/dakar.json`)

- **Wikipedia** — the "Dakar Rally" article at revision 1377153751 (retrieved 29 September 2026): every edition's route as the article names it, its era, and the first three of every class with the crew and the make. Text and tables are CC BY-SA 4.0 (Wikipedia contributors); the results themselves are facts. Transcribed by Daniel's prototype page; `tools/prepare_dakar.py` reads it.
- **Natural Earth** — the 1:110m land silhouette behind every route map (public domain), projected and rounded by the prototype. Routes are drawn schematically between their named towns, not from any official course; the stage-by-stage route is not carried.
- Nothing is taken from the organiser's own site, results service or artwork. The 2008 edition, cancelled before the start, is listed with no results.
- The data file is **CC BY-SA 4.0**: attribute Wikipedia contributors and share alike; the land geometry inside it is public domain. No logos, marks or official artwork; the rally's name identifies the event and nothing on the site is affiliated with the Amaury Sport Organisation.
