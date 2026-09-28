# Data audit — cricket atlas

Archive results through 2026-09-17. Core file 13,823 internationals, 8,370 players, 560 venues (154 recorded as a city only), 113 sides, 58 ICC titles, 37,168 player-season rows; 9,835 scorecards in 26 yearly shards. Nothing was changed.

## Coverage

| Game | Format | Matches | With scorecard | From | To | Scorecards from |
|---|---|---|---|---|---|---|
| Men | Test | 2,633 | 895 | 1877-03-15 | 2026-09-12 | 2001-12-19 |
| Women | Test | 24 | 24 | 2003-02-22 | 2026-07-13 | 2003-02-22 |
| Men | ODI | 4,721 | 2,576 | 1971-01-05 | 2026-09-15 | 2002-06-27 |
| Women | ODI | 611 | 611 | 2007-01-22 | 2026-09-06 | 2007-01-22 |
| Men | T20I | 3,663 | 3,558 | 2005-02-17 | 2026-09-17 | 2005-02-17 |
| Women | T20I | 2,171 | 2,171 | 2009-06-18 | 2026-09-17 | 2009-06-18 |

## Consistency checks

| Check | Result |
|---|---|
| duplicate game id | ✅ none |
| games not in date order | ✅ none |
| bad date | ✅ none |
| year ≠ date | ✅ none |
| unknown format | ✅ none |
| unknown game | ✅ none |
| sides malformed | ✅ none |
| side not in teams | ✅ none |
| winner not playing | ✅ none |
| winner on a non-win | ✅ none |
| unknown result | ✅ none |
| drawn limited-overs match | ✅ none |
| venue id unknown | ✅ none |
| innings side not playing | ✅ none |
| innings total out of range | ✅ none |
| detail flag without shard entry | ✅ none |
| batting + extras ≠ total | ✅ none |
| dismissals ≠ wickets | ✅ none |
| bowler wickets > innings wickets | ✅ none |
| champion game unknown | ✅ none |
| champion side unknown | ✅ none |
| player-season for unknown player | ✅ none |
| player-season for unknown team | ✅ none |
| outs > innings | ✅ none |
| highest score > runs | ✅ none |
| duplicate player-season | ✅ none |

## Well-known facts

| Fact | In the archive |
|---|---|
| First Test at Melbourne, 15 March 1877, Australia v England | ✅ |
| Exactly two tied Tests (Brisbane 1960, Madras 1986) | ✅ |
| First ODI 5 January 1971 at Melbourne | ✅ |
| First men’s T20I 17 February 2005 | ✅ |
| Men’s World Cup winners 1975–2023 | ✅ |
| Highest recorded Test total 823/7d England at Multan, 2024 (innings totals exist only where a scorecard does, from 2001) | ✅ |
| Highest recorded Test score 400* (Lara, 2004) | ✅ |
| South Africa played no internationals 1971–1990 | ✅ |
| Best recorded single season-format batting is plausible (< 2,000 runs) | ✅ |

## Source reconciliation

3,805 matches matched between the historical results list and Cricsheet; 6,030 added from Cricsheet alone; 3,988 historical only. 5 match-number conflicts, resolved to the Cricsheet number: M ODI 2016-10-29 (historic #3800, Cricsheet #3780); M ODI 2023-12-20 (historic #4715, Cricsheet #4714); M T20I 2021-07-25 (historic #1203, Cricsheet #1202); M T20I 2022-07-31 (historic #1717, Cricsheet #1716); M T20I 2024-09-27 (historic #2869, Cricsheet #2870).

Dismissal kinds across all scorecards: caught 79,288, bowled 30,985, lbw 16,452, run out 11,679, caught and bowled 4,592, stumped 4,475, retired hurt 224, hit wicket 134, retired out 54, obstructing the field 17, retired not out 13, timed out 2, handled the ball 1, hit the ball twice 1.
