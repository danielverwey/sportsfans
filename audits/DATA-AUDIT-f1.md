# Data audit — APEX F1 atlas

Dataset cut-off stated in the file: **22 September 2026**. All checks below compare the embedded data against itself, plus a short list of well-known reference facts. Nothing in the data was changed.

## Inventory

| Item | Count |
|---|---:|
| seasons | 77 |
| races | 1,163 |
| rows | 26,181 |
| sprint rows | 590 |
| drivers | 818 |
| teams | 205 |
| circuits | 78 |
| layouts | 160 |
| eras | 10 |
| drivers unused | 0 |
| teams unused | 0 |
| circuits unused | 0 |
| layouts unused | 0 |
| races without fastest lap | 1 |
| driver standings rows | 2,929 |
| driver points differ from race sum | 46 |
| team points differ from race sum | 102 |
| teams on placeholder colour | 134 |
| duplicate driver codes | 165 |

## Consistency checks

| Check | Result |
|---|---|
| unknown driver id | ✅ none |
| unknown team id | ✅ none |
| unknown circuit id | ✅ none |
| unknown layout id | ✅ none |
| layout not listed under its circuit | ✅ none |
| unknown driver in standings | ✅ none |
| unknown team in driver standings | ✅ none |
| unknown team in standings | ✅ none |
| layout asset shape | ✅ none |
| layout asset decode | ✅ none |
| season sequence | ✅ none |
| round numbering | ✅ none |
| race dates not chronological | ✅ none |
| race date outside its season | ✅ none |
| constructor standings before 1958 | ✅ none |
| constructor standings missing | ✅ none |
| driver standings missing | ✅ none |
| classification rows out of order | ✅ none |
| position numbers skip or repeat (no shared drives) | ⚠️ 24 — e.g. 1956 R3 Indianapolis 500; 1961 R7 Italian Grand Prix; 1962 R2 Monaco Grand Prix; 1962 R6 German Grand Prix |
| driver standings without any ranked entry (published table absent) | ⚠️ 2 — e.g. 1952 (3 entries, all unranked, 0 pts); 1953 (8 entries, all unranked, 0 pts) |
| driver standings not in rank order | ✅ none |
| more than one fastest-lap rank 1 | ⚠️ 12 — e.g. 1952 R8 (2); 1953 R5 (2); 1953 R6 (2); 1954 R5 (7) |
| winner flag count ≠ 1 | ⚠️ 3 — e.g. 1951 R4 (2); 1956 R1 (2); 1957 R5 (2) |
| winner flag not on P1 | ✅ none |
| constructor-win flag count ≠ 1 | ✅ none |
| win on unclassified row | ✅ none |
| podium flag outside top 3 | ✅ none |
| top-3 without podium flag | ✅ none |
| laps exceed scheduled | ⚠️ 1 — e.g. 1960 R4 henry_taylor 78/75 |
| negative points | ✅ none |
| non-finish flag on finished status | ✅ none |
| finish flag on non-finish status | ✅ none |
| grid-P1 flag with grid≠1 | ⚠️ 9 — e.g. 1950 R7 fangio g=7; 1951 R4 fangio g=7; 1952 R1 farina g=4; 1953 R4 fangio g=10 |
| fastest lap rank 1 without df flag | ⚠️ 7 — e.g. 1950 R7 fangio; 1951 R4 fangio; 1953 R7 ascari; 1954 R5 ascari |
| driver appears twice in one classification (shared drives?) | ⚠️ 40 — e.g. 1950 R3 ['bettenhausen']; 1950 R6 ['rosier']; 1950 R7 ['ascari', 'fangio']; 1951 R4 ['fangio', 'fagioli', 'ascari'] |
| standings wins ≠ race wins | ✅ none |
| standings not led by P1 | ⚠️ 2 — e.g. 1952; 1953 |
| driver without name | ✅ none |
| bad dob | ✅ none |
| driver without code | ✅ none |

## Points in standings vs points summed from race results

Driver standings rows whose published points differ from the sum of their race + sprint points: **46** of 2,929, in seasons 1950, 1951, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1977, 1979, 1980, 1985, 1986, 1987, 1988, 1989, 1990.
Constructor standings rows that differ: **102**, in seasons 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 2007, 2020.

Differences are expected wherever the championship counted only the best N results (1950–1990 drop-score rules), where shared drives split points, or where a penalty or exclusion adjusted the published table. The page shows the published standings and states the race-points basis wherever it derives a figure itself.

Largest driver differences:

| Season | Driver | Race sum | Published |
|---|---|---:|---:|
| 1963 | Jim Clark | 73 | 54 |
| 1988 | Alain Prost | 105 | 87 |
| 1954 | Juan Fangio | 57.14 | 42 |
| 1962 | Graham Hill | 52 | 42 |
| 1979 | Jody Scheckter | 60 | 51 |
| 1958 | Mike Hawthorn | 49 | 42 |
| 1965 | Graham Hill | 47 | 40 |
| 1980 | Carlos Reutemann | 49 | 42 |

## Reference facts

| Fact | Expected | In data | |
|---|---|---|---|
| 1950 champion (published standings) | farina | farina | ✅ |
| 1952 champion (published standings) | ascari | absent | ❌ |
| 1953 champion (published standings) | ascari | absent | ❌ |
| 1957 champion (published standings) | fangio | fangio | ✅ |
| 1969 champion (published standings) | stewart | stewart | ✅ |
| 1976 champion (published standings) | hunt | hunt | ✅ |
| 1988 champion (published standings) | senna | senna | ✅ |
| 1994 champion (published standings) | michael_schumacher | michael_schumacher | ✅ |
| 2004 champion (published standings) | michael_schumacher | michael_schumacher | ✅ |
| 2008 champion (published standings) | hamilton | hamilton | ✅ |
| 2010 champion (published standings) | vettel | vettel | ✅ |
| 2016 champion (published standings) | rosberg | rosberg | ✅ |
| 2020 champion (published standings) | hamilton | hamilton | ✅ |
| 2021 champion (published standings) | max_verstappen | max_verstappen | ✅ |
| 2023 champion (published standings) | max_verstappen | max_verstappen | ✅ |
| 2024 champion (published standings) | max_verstappen | max_verstappen | ✅ |
| Schumacher career wins | 91 | 91 | ✅ |
| Senna career wins | 41 | 41 | ✅ |
| Prost career wins | 51 | 51 | ✅ |
| Fangio career wins | 24 | 24 | ✅ |
| Clark career wins | 25 | 25 | ✅ |
| Vettel career wins | 53 | 53 | ✅ |
| Hamilton wins to end 2024 | 105 | 105 | ✅ |
| Verstappen wins to end 2024 | 63 | 63 | ✅ |
| races in 1950 | 7 | 7 | ✅ |
| races in 2024 | 24 | 24 | ✅ |
| races in 2021 | 22 | 22 | ✅ |
| races in 2020 | 17 | 17 | ✅ |
| Monza GPs to end 2025 | 75 | 75 | ✅ |
| Monaco GPs to end 2025 | 71 | 71 | ✅ |
| Indianapolis 500 in 1950–60 | 11 | 11 | ✅ |

## Notes

- 134 constructors carry the source’s placeholder colour (#b5a5ed); the page gives each a distinct muted hue for display only.
- 1 Grands Prix have no fastest-lap rank recorded; these show “not recorded” rather than a guess.
- Rows flagged "driver appears twice" are shared drives in the 1950s, where one car was handed between drivers; the source keeps one row per classified entry.
- 2026 is the season in progress; standings are as at the cut-off date.

## Findings worth fixing at source

1. **1952 and 1953 driver standings are absent.** The archive holds only a handful of unranked, zero-point entries for those two seasons, so the Ascari championships are not in the published-standings data. The page now orders those two seasons by race points and says so on screen; every other season uses the published table. Re-pulling those two seasons from the standings API would close the gap.
2. **Shared drives (1950–1961).** Where a car was handed between drivers, the source keeps one row per driver with the same position and marks it `shared`. Side effects visible in the checks: three shared wins (1951 French, 1956 Argentine, 1957 British — all historically correct), shared fastest laps (seven drivers at the 1954 British GP, also correct), and grid-P1 / fastest-lap flags carried by the relief driver’s row. The page counts them as the source flags them.
3. **Position numbers skip in 24 classifications** (e.g. 2002 French GP jumps 19 → 22; 1988 Monaco 26 → 31). Rows are shown in source order; nothing is invented to fill the holes.
4. **One lap-count anomaly:** 1960 Dutch GP, Henry Taylor, 78 laps recorded against a 75-lap race (status “+5 Laps”). The replay clamps it to the scheduled distance.
5. **Standings points vs race sums** differ in the drop-score decades, as expected; the page always labels which basis it is using.