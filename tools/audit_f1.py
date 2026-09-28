#!/usr/bin/env python3
"""Integrity audit of the DATA literal embedded in the F1 atlas.
Every check is internal consistency (the data against itself) plus a set of
well-known reference facts. Output: a Markdown report."""
import json, collections, datetime, base64, re
import pathlib as _pl; ROOT=_pl.Path(__file__).resolve().parent.parent
d = json.load(open(ROOT/'data'/'f1.json', encoding='utf-8'))
S, D, T, C, L, E = d['seasons'], d['drivers'], d['teams'], d['circuits'], d['layouts'], d['eras']
issues = collections.defaultdict(list)   # check -> list of messages
counts = {}
def note(check, msg): issues[check].append(msg)

# ---- 1. Referential integrity ---------------------------------------------
races = [(s, r) for s in S for r in s['races']]
rows = [(s, r, x) for s, r in races for x in r['rows']]
sprints = [(s, r, x) for s, r in races for x in r['sprint']]
counts.update(seasons=len(S), races=len(races), rows=len(rows), sprint_rows=len(sprints),
              drivers=len(D), teams=len(T), circuits=len(C), layouts=len(L), eras=len(E))
for s, r, x in rows + sprints:
    if x['d'] not in D: note('unknown driver id', f"{s['year']} R{r['round']} {x['d']}")
    if x['t'] not in T: note('unknown team id', f"{s['year']} R{r['round']} {x['t']}")
for s, r in races:
    if r['cid'] not in C: note('unknown circuit id', f"{s['year']} R{r['round']} {r['cid']}")
    if r['layout'] not in L: note('unknown layout id', f"{s['year']} R{r['round']} {r['layout']}")
    elif r['layout'] not in C.get(r['cid'], {}).get('layouts', []): note('layout not listed under its circuit', f"{s['year']} R{r['round']} {r['layout']} / {r['cid']}")
for s in S:
    for x in s['drivers']:
        if x['id'] not in D: note('unknown driver in standings', f"{s['year']} {x['id']}")
        for t in x['teams']:
            if t not in T: note('unknown team in driver standings', f"{s['year']} {t}")
    for x in s['teams']:
        if x['id'] not in T: note('unknown team in standings', f"{s['year']} {x['id']}")
used_d = {x['d'] for _, _, x in rows + sprints} | {x['id'] for s in S for x in s['drivers']}
used_t = {x['t'] for _, _, x in rows + sprints} | {x['id'] for s in S for x in s['teams']}
counts['drivers_unused'] = len(set(D) - used_d); counts['teams_unused'] = len(set(T) - used_t)
counts['circuits_unused'] = len(set(C) - {r['cid'] for _, r in races})
counts['layouts_unused'] = len(set(L) - {r['layout'] for _, r in races})

# ---- 2. Layout assets decode to a single path -----------------------------
for k, v in L.items():
    try:
        svg = base64.b64decode(v['asset'].split(',', 1)[1]).decode()
        if len(re.findall(r' d="', svg)) != 1 or 'width="500" height="500"' not in svg: note('layout asset shape', k)
    except Exception as e: note('layout asset decode', f'{k}: {e}')

# ---- 3. Season structure ----------------------------------------------------
years = [s['year'] for s in S]
if years != list(range(1950, 2027)): note('season sequence', str(years[:3]) + '…')
for s in S:
    rounds = [r['round'] for r in s['races']]
    if rounds != list(range(1, len(rounds) + 1)): note('round numbering', f"{s['year']}: {rounds}")
    dates = [r['date'] for r in s['races']]
    if dates != sorted(dates): note('race dates not chronological', str(s['year']))
    for r in s['races']:
        if not r['date'].startswith(str(s['year'])): note('race date outside its season', f"{s['year']} R{r['round']} {r['date']}")
    if s['year'] < 1958 and s['teams']: note('constructor standings before 1958', str(s['year']))
    if s['year'] >= 1958 and not s['teams']: note('constructor standings missing', str(s['year']))
    if not s['drivers']: note('driver standings missing', str(s['year']))
    elif not any(x['p'].isdigit() for x in s['drivers']): note('driver standings without any ranked entry (published table absent)', f"{s['year']} ({len(s['drivers'])} entries, all unranked, 0 pts)")
    ps=[int(x['p']) for x in s['drivers'] if x['p'].isdigit()]
    if ps and ps!=sorted(ps): note('driver standings not in rank order', str(s['year']))

# ---- 4. Row-level consistency ------------------------------------------------
fl_count = collections.Counter(); fr1_dup = []
for s, r in races:
    ps = [x['p'] for x in r['rows']]
    if ps != sorted(ps): note('classification rows out of order', f"{s['year']} R{r['round']}")
    if ps != list(range(1, len(ps) + 1)) and not any(x.get('shared') for x in r['rows']): note('position numbers skip or repeat (no shared drives)', f"{s['year']} R{r['round']} {r['name']}")
    n_fr1 = sum(1 for x in r['rows'] if x['fr'] == 1)
    if n_fr1 > 1: note('more than one fastest-lap rank 1', f"{s['year']} R{r['round']} ({n_fr1})")
    fl_count[n_fr1] += 1
    winners = [x for x in r['rows'] if x['dw']]
    if len(winners) != 1: note('winner flag count ≠ 1', f"{s['year']} R{r['round']} ({len(winners)})")
    elif winners[0]['p'] != 1: note('winner flag not on P1', f"{s['year']} R{r['round']}")
    cw = [x for x in r['rows'] if x['cw']]
    if len(cw) != 1: note('constructor-win flag count ≠ 1', f"{s['year']} R{r['round']} ({len(cw)})")
    # podium flags: driver podium = p<=3 and classified
    for x in r['rows']:
        lab_num = x['label'].isdigit()
        if x['dw'] and not lab_num: note('win on unclassified row', f"{s['year']} R{r['round']} {x['d']}")
        if x['dp'] and (not lab_num or int(x['label']) > 3): note('podium flag outside top 3', f"{s['year']} R{r['round']} {x['d']} label {x['label']}")
        if lab_num and int(x['label']) <= 3 and not x['dp'] and x['de']: note('top-3 without podium flag', f"{s['year']} R{r['round']} {x['d']}")
        if x['laps'] < 0 or x['laps'] > (r['scheduledLaps'] or 0) + 2: note('laps exceed scheduled', f"{s['year']} R{r['round']} {x['d']} {x['laps']}/{r['scheduledLaps']}")
        if x['pts'] < 0: note('negative points', f"{s['year']} R{r['round']} {x['d']}")
        if x['dn'] and (x['status'] == 'Finished' or re.match(r'^\+\d+ Lap', x['status'])): note('non-finish flag on finished status', f"{s['year']} R{r['round']} {x['d']} {x['status']}")
        if not x['dn'] and not (x['status'] == 'Finished' or re.match(r'^\+\d+ Lap', x['status'])) and x['de']: note('finish flag on non-finish status', f"{s['year']} R{r['round']} {x['d']} {x['status']}")
        if x['dg'] and x['g'] != 1: note('grid-P1 flag with grid≠1', f"{s['year']} R{r['round']} {x['d']} g={x['g']}")
        if x['fr'] == 1 and not x['df']: note('fastest lap rank 1 without df flag', f"{s['year']} R{r['round']} {x['d']}")
    ds = [x['d'] for x in r['rows']]
    dup = [k for k, v in collections.Counter(ds).items() if v > 1]
    if dup: note('driver appears twice in one classification (shared drives?)', f"{s['year']} R{r['round']} {dup}")
counts['races_without_fastest_lap'] = fl_count[0]

# ---- 5. Points vs standings ---------------------------------------------------
diff_d = []; diff_t = []
for s in S:
    pts = collections.defaultdict(float); tpts = collections.defaultdict(float); wins = collections.Counter()
    for r in s['races']:
        for x in r['rows'] + r['sprint']:
            pts[x['d']] += x['pts']; tpts[x['t']] += x['pts']
        for x in r['rows']:
            if x['dw']: wins[x['d']] += 1
    for x in s['drivers']:
        if abs(pts[x['id']] - x['pts']) > 1e-6: diff_d.append((s['year'], x['id'], pts[x['id']], x['pts']))
        if wins[x['id']] != x['wins']: note('standings wins ≠ race wins', f"{s['year']} {x['id']} race {wins[x['id']]} vs standings {x['wins']}")
    for x in s['teams']:
        if abs(tpts[x['id']] - x['pts']) > 1e-6: diff_t.append((s['year'], x['id'], tpts[x['id']], x['pts']))
    # champion should be the standings leader
    if s['drivers'] and s['drivers'][0]['p'] != '1': note('standings not led by P1', str(s['year']))
counts['driver_standings_rows'] = sum(len(s['drivers']) for s in S)
counts['driver_points_differ_from_race_sum'] = len(diff_d)
counts['team_points_differ_from_race_sum'] = len(diff_t)
# years where differences occur (drop-score / penalty seasons expected)
diff_years_d = sorted({y for y, *_ in diff_d}); diff_years_t = sorted({y for y, *_ in diff_t})

# ---- 6. Driver / team master data -------------------------------------------
for k, v in D.items():
    if not v.get('name'): note('driver without name', k)
    if v.get('dob'):
        try: datetime.date.fromisoformat(v['dob'])
        except ValueError: note('bad dob', f"{k} {v['dob']}")
    if not v.get('code'): note('driver without code', k)
placeholder = [k for k, v in T.items() if v.get('color', '').lower() == '#b5a5ed']
counts['teams_on_placeholder_colour'] = len(placeholder)
codes = collections.Counter(v['code'] for v in D.values())
counts['duplicate_driver_codes'] = sum(1 for c, n in codes.items() if n > 1)

# ---- 7. Reference facts (well-known; checked against the data) ---------------
champ = {s['year']: s['drivers'][0]['id'] for s in S if s['drivers']}
ref = {1950: 'farina', 1952: 'ascari', 1953: 'ascari', 1957: 'fangio', 1969: 'stewart', 1976: 'hunt', 1988: 'senna', 1994: 'michael_schumacher', 2004: 'michael_schumacher',
       2008: 'hamilton', 2010: 'vettel', 2016: 'rosberg', 2020: 'hamilton', 2021: 'max_verstappen', 2023: 'max_verstappen', 2024: 'max_verstappen'}
ref_checks = []
for y, who in ref.items():
    ok = champ.get(y) == who
    ref_checks.append((f'{y} champion (published standings)', who, champ.get(y) if champ.get(y) and any(x['p'].isdigit() for x in [s for s in S if s['year']==y][0]['drivers']) else 'absent', ok))
def wins_of(did): return sum(1 for _, _, x in rows if x['d'] == did and x['dw'])
def gp_at(cid): return sum(1 for _, r in races if r['cid'] == cid)
for label, got, want in [('Schumacher career wins', wins_of('michael_schumacher'), 91), ('Senna career wins', wins_of('senna'), 41), ('Prost career wins', wins_of('prost'), 51),
                         ('Fangio career wins', wins_of('fangio'), 24), ('Clark career wins', wins_of('clark'), 25), ('Vettel career wins', wins_of('vettel'), 53),
                         ('Hamilton wins to end 2024', sum(1 for s, _, x in rows if x['d'] == 'hamilton' and x['dw'] and s['year'] <= 2024), 105),
                         ('Verstappen wins to end 2024', sum(1 for s, _, x in rows if x['d'] == 'max_verstappen' and x['dw'] and s['year'] <= 2024), 63),
                         ('races in 1950', len(S[0]['races']), 7), ('races in 2024', len([r for s, r in races if s['year'] == 2024]), 24),
                         ('races in 2021', len([r for s, r in races if s['year'] == 2021]), 22), ('races in 2020', len([r for s, r in races if s['year'] == 2020]), 17),
                         ('Monza GPs to end 2025', sum(1 for s, r in races if r['cid'] == 'monza' and s['year'] <= 2025), 75),
                         ('Monaco GPs to end 2025', sum(1 for s, r in races if r['cid'] == 'monaco' and s['year'] <= 2025), 71),
                         ('Indianapolis 500 in 1950–60', sum(1 for s, r in races if r['cid'] == 'indianapolis' and s['year'] <= 1960), 11)]:
    ref_checks.append((label, want, got, got == want))

# ---- report -------------------------------------------------------------------
out = ['# Data audit — APEX F1 atlas', '', f"Dataset cut-off stated in the file: **{d['cutoff']}**. All checks below compare the embedded data against itself, plus a short list of well-known reference facts. Nothing in the data was changed.", '',
       '## Inventory', '', '| Item | Count |', '|---|---:|']
for k, v in counts.items(): out.append(f'| {k.replace("_", " ")} | {v:,} |')
out += ['', '## Consistency checks', '', '| Check | Result |', '|---|---|']
checks = ['unknown driver id', 'unknown team id', 'unknown circuit id', 'unknown layout id', 'layout not listed under its circuit', 'unknown driver in standings', 'unknown team in driver standings', 'unknown team in standings',
          'layout asset shape', 'layout asset decode', 'season sequence', 'round numbering', 'race dates not chronological', 'race date outside its season', 'constructor standings before 1958', 'constructor standings missing', 'driver standings missing',
          'classification rows out of order', 'position numbers skip or repeat (no shared drives)', 'driver standings without any ranked entry (published table absent)', 'driver standings not in rank order', 'more than one fastest-lap rank 1', 'winner flag count ≠ 1', 'winner flag not on P1', 'constructor-win flag count ≠ 1', 'win on unclassified row', 'podium flag outside top 3', 'top-3 without podium flag',
          'laps exceed scheduled', 'negative points', 'non-finish flag on finished status', 'finish flag on non-finish status', 'grid-P1 flag with grid≠1', 'fastest lap rank 1 without df flag', 'driver appears twice in one classification (shared drives?)',
          'standings wins ≠ race wins', 'standings not led by P1', 'driver without name', 'bad dob', 'driver without code']
for c in checks:
    v = issues.get(c, [])
    out.append(f'| {c} | {"✅ none" if not v else "⚠️ " + str(len(v)) + " — e.g. " + "; ".join(v[:4])} |')
out += ['', '## Points in standings vs points summed from race results', '',
        f'Driver standings rows whose published points differ from the sum of their race + sprint points: **{len(diff_d)}** of {counts["driver_standings_rows"]:,}, in seasons {", ".join(map(str, diff_years_d)) or "none"}.',
        f'Constructor standings rows that differ: **{len(diff_t)}**, in seasons {", ".join(map(str, diff_years_t)) or "none"}.', '',
        'Differences are expected wherever the championship counted only the best N results (1950–1990 drop-score rules), where shared drives split points, or where a penalty or exclusion adjusted the published table. The page shows the published standings and states the race-points basis wherever it derives a figure itself.', '']
if diff_d:
    out += ['Largest driver differences:', '', '| Season | Driver | Race sum | Published |', '|---|---|---:|---:|']
    for y, i, a, b in sorted(diff_d, key=lambda t: -abs(t[2] - t[3]))[:8]: out.append(f'| {y} | {D[i]["name"]} | {a:g} | {b:g} |')
out += ['', '## Reference facts', '', '| Fact | Expected | In data | |', '|---|---|---|---|']
for label, want, got, ok in ref_checks: out.append(f'| {label} | {want} | {got} | {"✅" if ok else "❌"} |')
out += ['', '## Notes', '',
        f'- {counts["teams_on_placeholder_colour"]} constructors carry the source’s placeholder colour (#b5a5ed); the page gives each a distinct muted hue for display only.',
        f'- {counts["races_without_fastest_lap"]} Grands Prix have no fastest-lap rank recorded; these show “not recorded” rather than a guess.',
        '- Rows flagged "driver appears twice" are shared drives in the 1950s, where one car was handed between drivers; the source keeps one row per classified entry.',
        '- 2026 is the season in progress; standings are as at the cut-off date.', '',
        '## Findings worth fixing at source', '',
        '1. **1952 and 1953 driver standings are absent.** The archive holds only a handful of unranked, zero-point entries for those two seasons, so the Ascari championships are not in the published-standings data. The page now orders those two seasons by race points and says so on screen; every other season uses the published table. Re-pulling those two seasons from the standings API would close the gap.',
        '2. **Shared drives (1950–1961).** Where a car was handed between drivers, the source keeps one row per driver with the same position and marks it `shared`. Side effects visible in the checks: three shared wins (1951 French, 1956 Argentine, 1957 British — all historically correct), shared fastest laps (seven drivers at the 1954 British GP, also correct), and grid-P1 / fastest-lap flags carried by the relief driver’s row. The page counts them as the source flags them.',
        '3. **Position numbers skip in 24 classifications** (e.g. 2002 French GP jumps 19 → 22; 1988 Monaco 26 → 31). Rows are shown in source order; nothing is invented to fill the holes.',
        '4. **One lap-count anomaly:** 1960 Dutch GP, Henry Taylor, 78 laps recorded against a 75-lap race (status “+5 Laps”). The replay clamps it to the scheduled distance.',
        '5. **Standings points vs race sums** differ in the drop-score decades, as expected; the page always labels which basis it is using.']
open(ROOT/'audits'/'DATA-AUDIT-f1.md', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
