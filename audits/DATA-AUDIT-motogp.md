# Data audit — MotoGP atlas

Archive snapshot 2026-09-23, results through 2026-09-20. Checks compare the embedded archive against itself, plus well-known reference facts. Nothing was changed.

## Inventory

- 1,100 race classifications (Counter({'RAC': 1024, 'SPR': 76})) · 22,884 result rows · 1,437 riders · 71 circuits · 78 seasons of standings
- Circuit outlines: 25 circuits carry a profile image in the archive (all traced into vector lines for this page); 46 do not
- Per-race points recorded: 13,940 rows

## Consistency checks

| Check | Result |
|---|---|
| bad date | ✅ none |
| year ≠ date | ✅ none |
| unknown circuit | ✅ none |
| positions out of order | ✅ none |
| duplicate positions | ⚠️ 1 — e.g. 48f25a3b-e905-4651-8b9e-68ed77bb6a26 [8] |
| no P1 | ✅ none |
| empty classification | ✅ none |
| unknown rider | ✅ none |
| rider twice in one classification | ⚠️ 1 — e.g. 93d9836a-8b1c-4a30-b9d5-7e814a01166b Bruno Kneubühler |
| position with non-classified status | ✅ none |
| classified without position | ⚠️ 1 — e.g. ed28d526-c0bc-4244-af0f-ef852a3fd6cf |
| negative points | ✅ none |
| pole rider unknown | ✅ none |
| fastest-lap rider unknown | ✅ none |
| fastest-lap rider not in classification | ✅ none |
| standings out of order | ✅ none |
| standings without P1 | ✅ none |
| standings rider unknown | ✅ none |
| champion has no race entry that season | ✅ none |
| seasons with races ≠ seasons with standings | ✅ none |

Coverage table vs counted main races: ✅ matches every season

Published standings vs summed per-race points (top 10 each season, where per-race points exist): **130** rows differ — drop-score rules, penalties and sprint points explain most; e.g. 1992 Wayne Rainey 0 vs 140; 1992 Mick Doohan 0 vs 136; 1992 John Kocinski 0 vs 102; 1992 Kevin Schwantz 0 vs 99; 1992 Doug Chandler 0 vs 94

## Reference facts

| Fact | Expected | In data | |
|---|---|---|---|
| 1949 champion | Leslie Graham | Leslie Graham | ✅ |
| 1957 champion | Libero Liberati | Libero Liberati | ✅ |
| 1966 champion | Giacomo Agostini | Giacomo Agostini | ✅ |
| 1975 champion | Giacomo Agostini | Giacomo Agostini | ✅ |
| 1983 champion | Freddie Spencer | Freddie Spencer | ✅ |
| 1993 champion | Kevin Schwantz | Kevin Schwantz | ✅ |
| 2001 champion | Valentino Rossi | Valentino Rossi | ✅ |
| 2007 champion | Casey Stoner | Casey Stoner | ✅ |
| 2013 champion | Marc Marquez | Marc Marquez | ✅ |
| 2019 champion | Marc Marquez | Marc Marquez | ✅ |
| 2020 champion | Joan Mir | Joan Mir | ✅ |
| 2022 champion | Francesco Bagnaia | Francesco Bagnaia | ✅ |
| 2023 champion | Francesco Bagnaia | Francesco Bagnaia | ✅ |
| 2024 champion | Jorge Martin | Jorge Martin | ✅ |
| Giacomo Agostini career wins (main races) | 68 | 68 | ✅ |
| Valentino Rossi career wins (main races) | 89 | 89 | ✅ |
| Marc Marquez career wins (main races) | — | 78 | ✅ |

## Notes

- 22 rows carry a finishing position with status “NC” (e.g. the winner of the 2003 Portuguese GP); the page treats a row with a position as classified, as the source prototype did.
- Per-race points in the feed are zero for 1992–2004 and absent before 1992; the page therefore takes championship points from the published standings everywhere, and only the Sprint lens uses per-race points (2023 on).
- One dead-heat style duplicate position (1972 Tourist Trophy, two riders 8th), one rider listed twice (1972 Tourist Trophy) and one classified row without a position (1989 Dutch TT) are left as recorded.