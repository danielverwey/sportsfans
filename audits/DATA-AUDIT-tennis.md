# Data audit — tennis atlas

Archive: 11,043 titles (1877–2026), 388,665 matches in 59 yearly shards (1968–2026), 16,150 players, 9,897 tournaments, 20,412 editions, 69,230 player-season rows. Source: Jeff Sackmann’s tennis_atp and tennis_wta (CC BY-NC-SA 4.0), commit 8373358735; Wimbledon’s own Compendium for champions before 1968 (the other majors’ rolls begin with the Open era in this archive). Nothing was changed.

## Coverage

| Circuit | Matches | With statistics | Match years | Titles | Title years |
|---|---|---|---|---|---|
| MS | 199,386 | 101,928 | 1968–2026 | 4,680 | 1877–2026 |
| WS | 162,181 | 47,829 | 1968–2026 | 4,716 | 1884–2026 |
| MD | 26,539 | 5,123 | 2000–2024 | 1,436 | 1884–2026 |
| WD | 559 | 0 | 2019–2024 | 108 | 1913–2026 |
| XD | 0 | 0 | —–— | 103 | 1913–2026 |

Scores that do not parse as sets: 1,832 of 388,665 (retirements, walkovers and unknowns are accepted as written).

## Consistency checks

| Check | Result |
|---|---|
| edition with unknown tournament | ✅ none |
| bad edition date | ✅ none |
| edition year ≠ date (December start of the next season accepted) | ⚠️ 11 — e.g. MS:1968-T162, MS:1972-2047, MS:1977-605 |
| unknown circuit | ✅ none |
| unknown surface | ✅ none |
| shard edition unknown | ✅ none |
| shard year ≠ edition year | ✅ none |
| duplicate match id | ✅ none |
| match without both sides | ✅ none |
| match player unknown | ✅ none |
| player on both sides | ✅ none |
| unequal sides | ✅ none |
| doubles pairing in a singles draw | ✅ none |
| implausible duration | ⚠️ 398 — e.g. MS:1991-408:20 9, MS:1991-316:8 8, MS:1991-429:27 9 |
| bad rank | ✅ none |
| edition match count ≠ shard | ✅ none |
| title with unknown tournament | ✅ none |
| title player unknown | ✅ none |
| title final match missing from shards | ✅ none |
| title year ≠ edition year | ✅ none |
| duplicate title id | ✅ none |
| player-season for unknown player | ✅ none |
| surface split ≠ total | ✅ none |
| titles > finals | ✅ none |

## Well-known facts

| Fact | In the archive |
|---|---|
| Wimbledon’s roll of honour begins in 1877 (Spencer Gore) | ✅ |
| Djokovic 24 majors, Nadal 22, Federer 20 (singles) | ✅ |
| Serena Williams 23 singles majors, Steffi Graf 22; Margaret Court’s three Wimbledons (1963, 1965, 1970) | ✅ |
| Laver’s Grand Slam of 1969: all four majors | ✅ |
| Graf’s Golden Slam of 1988: four majors and the Olympic title | ✅ |
| Djokovic–Nadal head to head 31–29 | ✅ |
| Longest match Isner–Mahut, Wimbledon 2010, 665 minutes (five source durations above 700 minutes are treated as errors and kept out of the records) | ✅ |
| Nadal 14 Roland-Garros titles | ✅ |
| Federer 103 singles titles, Connors more than a hundred | ✅ |
| First open tournament in 1968; no match records before | ✅ |

## Source notes

Exclusions and quirks carried from the source: invalid opposing identity excluded 4, source number collision preserved 16, missing id 6, qualifying excluded 261, incomplete doubles tape 208.
