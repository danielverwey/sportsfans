# Data audit — WorldSBK atlas

Archive snapshot 2026-09-23, results through 2026-09-06. Checks compare the embedded archive against itself, plus well-known reference facts. Nothing was changed.

## Inventory

- 1,040 race classifications (Counter({'R1': 479, 'R2': 473, 'SPR': 88})) · 26,564 result rows · 1,303 riders · 55 circuits · 39 seasons of standings
- Circuit outlines: 22 circuits carry a profile image in the archive (all traced into vector lines for this page); 33 do not
- Per-race points recorded: 0 rows

## Consistency checks

| Check | Result |
|---|---|
| bad date | ✅ none |
| year ≠ date | ⚠️ 24 — e.g. 1996-RSM-SBK-001; 1996-RSM-SBK-002; 1996-GBR-SBK-001 |
| unknown circuit | ✅ none |
| positions out of order | ✅ none |
| duplicate positions | ✅ none |
| no P1 | ✅ none |
| empty classification | ✅ none |
| unknown rider | ✅ none |
| rider twice in one classification | ✅ none |
| position with non-classified status | ⚠️ 6114 — e.g. 1988-GBR-SBK-001 Retired; 1988-GBR-SBK-001 Retired; 1988-GBR-SBK-001 Retired |
| classified without position | ✅ none |
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

Published standings vs summed per-race points: ✅ every top-ten row reconciles where per-race points exist.

## Reference facts

| Fact | Expected | In data | |
|---|---|---|---|
| 1988 champion | Fred Merkel | Fred Merkel | ✅ |
| 1990 champion | Raymond Roche | Raymond Roche | ✅ |
| 1994 champion | Carl Fogarty | Carl Fogarty | ✅ |
| 1999 champion | Carl Fogarty | Carl Fogarty | ✅ |
| 2002 champion | Colin Edwards | Colin Edwards | ✅ |
| 2006 champion | Troy Bayliss | Troy Bayliss | ✅ |
| 2009 champion | Ben Spies | Ben Spies | ✅ |
| 2013 champion | Tom Sykes | Tom Sykes | ✅ |
| 2015 champion | Jonathan Rea | Jonathan Rea | ✅ |
| 2020 champion | Jonathan Rea | Jonathan Rea | ✅ |
| 2021 champion | Toprak Razgatlioglu | Toprak Razgatlioglu | ✅ |
| 2022 champion | Alvaro Bautista | Alvaro Bautista | ✅ |
| 2023 champion | Alvaro Bautista | Alvaro Bautista | ✅ |
| 2024 champion | Toprak Razgatlioglu | Toprak Razgatlioglu | ✅ |
| Jonathan Rea career wins (all races incl. Superpole) | 119 | 119 | ✅ |
| Carl Fogarty career wins (all races incl. Superpole) | 59 | 59 | ✅ |
| Troy Bayliss career wins (all races incl. Superpole) | 52 | 52 | ✅ |

## Notes

- Every race of the 1996 season is dated in 1997 in the feed (e.g. 1996-RSM-SBK-001 dated 1997-04-14); the page shows the date within the season year and says so on the race sheet. Worth fixing at source.
- Retired rows carry a finishing-order position in the feed; the page shows R for them and uses the position only for ordering.
- The feed carries no per-race points, so all points figures come from the published riders’ and manufacturers’ standings.