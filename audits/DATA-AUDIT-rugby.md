# Data audit — Ten Nations rugby atlas

Archive as of 2026-09-23, results through 2026-09-12. Checks compare the embedded data against itself plus scoring-value arithmetic and well-known facts. Nothing was changed.

## Inventory

- 3,960 matches · 484 player snapshots · 217 coach profiles · 10 perspectives
- 718 matches carry a scoring breakdown; 38 pre-1885 fixtures are scored in goals; 21 legacy fixtures; 72 dates flagged uncertain
- World Cup matches by tournament: 1987: 29, 1991: 28, 1995: 30, 1999: 35, 2003: 40, 2007: 40, 2011: 40, 2015: 40, 2019: 38, 2023: 40

## Consistency checks

| Check | Result |
|---|---|
| match ids not 0..N-1 | ✅ none |
| matches not in date order | ✅ none |
| bad date | ✅ none |
| year ≠ date | ✅ none |
| eligible outside the ten | ✅ none |
| eligible names neither side | ✅ none |
| eligible nation not playing | ✅ none |
| scoring length | ✅ none |
| negative score | ✅ none |
| world cup without stage | ✅ none |
| goals unit after 1885 | ✅ none |
| scoring breakdown ≠ score (era values) | ✅ none |
| same fixture twice on one date | ✅ none |
| team count ≠ eligible matches | ✅ none |
| team from ≠ first match | ✅ none |
| coach matchId out of range | ✅ none |
| coach match not involving team | ✅ none |
| linked record n ≠ matchIds | ✅ none |
| reconciles flag but records differ | ✅ none |
| player team outside ten | ✅ none |
| complete history ≠ caps | ✅ none |
| player span reversed | ✅ none |

Scoring breakdowns reconcile with the final score under the scoring values of the day (try 3/4/5 by era, conversion 2, penalty 3, drop 4 then 3, penalty try 7 from 2017) in 718 of 718 matches that carry one.

## World Cup finals in the archive

| Year | Final | Score |
|---|---|---|
| 1987 | New Zealand v France | 29–9 |
| 1991 | England v Australia | 6–12 |
| 1995 | South Africa v New Zealand | 15–12 |
| 1999 | Australia v France | 35–12 |
| 2003 | Australia v England | 17–20 |
| 2007 | England v South Africa | 6–15 |
| 2011 | New Zealand v France | 8–7 |
| 2015 | Australia v New Zealand | 17–34 |
| 2019 | England v South Africa | 12–32 |
| 2023 | New Zealand v South Africa | 11–12 |

Champions listed in the team registry: South Africa [1995, 2007, 2019, 2023]; New Zealand [1987, 2011, 2015]; Australia [1991, 1999]; England [2003]

## Head-to-head cross-checks (won–lost–drawn from the first side)

- South Africa v New Zealand to 12 Sep 2026: 46–64–4
- England v Wales: 71–61–12
- Australia v New Zealand: 44–129–8
- Ireland v Scotland: 73–66–5