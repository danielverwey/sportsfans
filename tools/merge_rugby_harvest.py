#!/usr/bin/env python3
"""Bring Daniel's consolidated rugby harvest into the archive: the national registers of every side in the atlas, the
team sheets and named scorers of every Test the harvest could reach, Wikidata's dates for the people it linked, and the
reviewed corrections to a handful of match records.

    python tools/merge_rugby_harvest.py build/harvest/rugby_harvest_consolidated_021.json

Reads data/rugby.json and writes it back in the same shape, so the atlas, the static pages and the reading edition need
no new fields to work:

  players   every register entry the harvest carries (20,780 across 28 sides) in the atlas's own player record — the 484
            existing profiles keep their ids, published figures and captured histories; every other entry is added with
            the published caps, tries and points where the national list gives them, its debut, and a match-by-match
            history built from the team sheets and scorers, linked to the atlas's own match ids by the same perspective
            index the existing histories use. Names printed in a match source that no register entry could be linked to
            are kept as printed and marked for review, so team sheets stay complete.
  matches   a scoring breakdown (the twelve-number `scoring` row) for every Test whose scorers reconcile to the recorded
            score under the values of the day and which had none; the harvest's Wikipedia match sources; and the ten
            reviewed corrections (six dates against official match records, one score orientation, the 2016 Americas
            Rugby Championship side recorded as Argentina XV rather than a senior Argentina Test).

Nothing the archive already holds is overwritten except by those reviewed corrections, each of which is listed in
`harvestCorrections` with its evidence. Null in the harvest means unknown, never zero.
"""
import argparse, collections, datetime, hashlib, json, pathlib, re, sys, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent

def slug(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode('ascii').lower().replace('’', '').replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'x'
def pts(y): return {'try': 5 if y >= 1992 else 4 if y >= 1971 else 3, 'conversion': 2, 'penalty_goal': 3, 'drop_goal': 3 if y >= 1948 else 4, 'penalty_try': 7 if y >= 2017 else (5 if y >= 1992 else 4 if y >= 1971 else 3)}
POS = {'HK': 'Hooker', 'PR': 'Prop', 'TP': 'Prop', 'LP': 'Prop', 'LK': 'Lock', 'LL': 'Lock', 'RL': 'Lock', 'FL': 'Flanker', 'OF': 'Flanker', 'BF': 'Flanker', 'FLK': 'Flanker', 'BR': 'Back row', 'N8': 'Number 8', 'SH': 'Scrum-half', 'FH': 'Fly-half',
       'CE': 'Centre', 'IC': 'Centre', 'OC': 'Centre', 'CT': 'Centre', 'CN': 'Centre', 'CR': 'Centre', 'WG': 'Wing', 'LW': 'Wing', 'RW': 'Wing', 'FB': 'Full-back', 'Full back': 'Full-back', 'Full-back': 'Full-back', 'Halfback': 'Half-back', 'Half back': 'Half-back',
       'Forward': 'Forward', 'F': 'Forward', 'Three-quarters': 'Three-quarter', 'UB': 'Utility back', 'LF': 'Forward', 'BL': 'Back', 'FK': 'Full-back', 'H': 'Half-back', 'L': 'Lock', 'P': 'Prop'}
SCORE_WORD = {'try': ('try', 'tries'), 'conversion': ('conversion', 'conversions'), 'penalty_goal': ('penalty', 'penalties'), 'drop_goal': ('drop goal', 'drop goals'), 'penalty_try': ('penalty try', 'penalty tries'), 'goal_from_mark': ('goal from mark', 'goals from mark'), 'goal': ('goal', 'goals')}
CODES = {'British & Irish Lions': 'LIO', 'South America': 'SAM', 'NZ Cavaliers': 'CAV', 'World Invitation': 'WXV', 'Great Britain': 'GBR', 'USA': 'USA', 'Czechia': 'CZE', 'Ivory Coast': 'CIV', 'Netherlands': 'NED', 'Germany': 'GER', 'Japan': 'JPN', 'Fiji': 'FIJ', 'Samoa': 'SAM', 'Tonga': 'TGA', 'Georgia': 'GEO', 'Namibia': 'NAM', 'Portugal': 'POR', 'Canada': 'CAN', 'Romania': 'ROU', 'Uruguay': 'URU', 'Spain': 'ESP', 'Chile': 'CHI', 'Russia': 'RUS', 'Paraguay': 'PAR', 'Brazil': 'BRA', 'Zimbabwe': 'ZIM', 'Morocco': 'MAR', 'Tunisia': 'TUN', 'Madagascar': 'MAD', 'Croatia': 'CRO', 'Pacific Islands': 'PIS'}
def pos_label(code):
    if not code: return ''
    c = str(code).strip().strip('()')
    if c in POS: return POS[c]
    return c[:1].upper() + c[1:]
def scoring_text(events):
    parts = []
    for e in events or []:
        t, n = e.get('type'), e.get('count') or 0
        if not n or t not in SCORE_WORD: continue
        parts.append(f'{n} {SCORE_WORD[t][0 if n == 1 else 1]}')
    return ', '.join(parts)
def wd_date(stmts, key):
    for s in stmts.get(key) or []:
        v = (s.get('value') or {}); t = v.get('time') or ''; prec = v.get('precision') or 0
        m = re.match(r'^\+?(\d{4})-(\d{2})-(\d{2})', t)
        if not m: continue
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if prec >= 11 and mo and d:
            try: return datetime.date(y, mo, d).strftime('%-d %b %Y')
            except ValueError: return str(y)
        if prec == 10 and mo: return datetime.date(y, mo, 1).strftime('%b %Y')
        return str(y)
    return None

ap = argparse.ArgumentParser(); ap.add_argument('harvest', nargs='?', default=str(ROOT/'build'/'harvest'/'rugby_harvest_consolidated_021.json')); args = ap.parse_args()
A = json.loads((ROOT/'data'/'rugby.json').read_text(encoding='utf-8')); H = json.loads(pathlib.Path(args.harvest).read_text(encoding='utf-8'))
TEN = [t['name'] for t in A['teams']]; TEAMCODE = {t['name']: t['code'] for t in A['teams']}; TEAMCODE.update({k: v for k, v in CODES.items() if k not in TEAMCODE})
M = A['matches']; HM = {m['id']: m for m in H['matches']}
report = collections.Counter(); corrections = []

# ---------------------------------------------------------------- 1. reviewed match corrections
for hm in H['matches']:
    m = M[hm['id']]
    assert m.get('sourceId') == hm['source_match_key'] or m['date'] == hm['baseline']['date'], (hm['id'], m.get('sourceId'))
    for rc in hm.get('reviewed_corrections') or []:
        before, after = rc.get('before') or {}, rc.get('after') or {}
        if 'date' in after and m['date'] == before.get('date'):
            corrections.append({'match': m['id'], 'field': 'date', 'before': m['date'], 'after': after['date'], 'evidence': rc.get('evidence_url'), 'basis': rc.get('basis')}); m['date'] = after['date']; m['year'] = int(after['date'][:4]); report['date corrected'] += 1
        if 'score' in after and (m['hs'], m['as_']) == (before.get('score', {}).get('home'), before.get('score', {}).get('away')):
            corrections.append({'match': m['id'], 'field': 'score', 'before': f"{m['hs']}–{m['as_']}", 'after': f"{after['score']['home']}–{after['score']['away']}", 'evidence': rc.get('evidence_url'), 'basis': rc.get('basis')}); m['hs'], m['as_'] = after['score']['home'], after['score']['away']; report['score corrected'] += 1
        if rc.get('corrected_team') and rc.get('original_team'):
            o, c = rc['original_team'], rc['corrected_team']
            if m['home'] == o: m['home'] = c
            if m['away'] == o: m['away'] = c
            m['eligible'] = [e for e in m['eligible'] if e != o]
            m.setdefault('notes', []).append(f'{c}, not a senior {o} Test: the Argentine union and World Rugby classify the 2016 Americas Rugby Championship side as {c}; the fixture stays in the archive but counts in no nation’s record.')
            corrections.append({'match': m['id'], 'field': 'side', 'before': o, 'after': c, 'evidence': (rc.get('official_sources') or [None])[0], 'basis': rc.get('basis')}); report['side reclassified'] += 1
dates = [m['date'] for m in M]; report['date inversions after corrections'] = sum(1 for a, b in zip(dates, dates[1:]) if b < a)
for t in A['teams']:
    t['count'] = sum(1 for m in M if t['name'] in m['eligible'])
for c in A.get('coaches', []):   # a reclassified fixture leaves the coach's linked record
    keep = [i for i in c['matchIds'] if c['team'] in M[i]['eligible']]
    if len(keep) != len(c['matchIds']):
        c['matchIds'] = keep; report['coach links dropped with reclassified fixtures'] += 1
        if c.get('linkedRecord'):
            w = l = d = 0
            for i in keep:
                m = M[i]; pf, pa = (m['hs'], m['as_']) if m['home'] == c['team'] else (m['as_'], m['hs']); w += pf > pa; l += pf < pa; d += pf == pa
            c['linkedRecord'].update({'n': len(keep), 'w': w, 'l': l, 'd': d})

# ---------------------------------------------------------------- 2. scoring breakdowns and match sources
SLOT = {'try': 0, 'conversion': 1, 'penalty_goal': 2, 'drop_goal': 3, 'goal_from_mark': 4, 'penalty_try': 5}
for hm in H['matches']:
    m = M[hm['id']]
    if not m.get('scoring') and m['scoreUnit'] == 'points':
        sides = [hm['teams'].get(m['home']), hm['teams'].get(m['away'])]
        if all(s and s.get('scoring_status') in ('totals_reconcile', 'verified_zero') for s in sides):
            row = [0] * 12; ok = True
            for k, s in enumerate(sides):
                for sc in s.get('scorers') or []:
                    t = sc.get('type'); n = sc.get('count') or 0
                    if t not in SLOT or t == 'goal_from_mark': ok = False; break
                    row[k * 6 + SLOT[t]] += n
                if not ok: break
            if ok:
                v = pts(m['year']); calc = lambda o: row[o] * v['try'] + row[o + 1] * v['conversion'] + row[o + 2] * v['penalty_goal'] + row[o + 3] * v['drop_goal'] + row[o + 5] * v['penalty_try']
                if calc(0) == m['hs'] and calc(6) == m['as_']: m['scoring'] = row; report['scoring breakdowns added'] += 1
                else: report['scoring breakdowns not reconciling (skipped)'] += 1
    new = [u for u in hm.get('sources') or [] if u and u not in m['sources']]
    if new: m['sources'] = (m['sources'] + new)[:8]; report['matches with added sources'] += 1

# ---------------------------------------------------------------- 3. the player register
def plays(m, side): return (m['home'] == side or m['away'] == side) and (side not in TEN or side in m['eligible'])
sides = sorted({s for m in M for s in (m['home'], m['away'])})
persp = {s: {m['id']: i for i, m in enumerate([m for m in M if plays(m, s)])} for s in sides}
existing = {p['id']: p for p in A['players']}
to_existing = {v: k for k, v in H['original_player_id_map'].items()}   # harvest id -> atlas id
lineup_of = {}   # (match id, player id) -> lineup entry
for hm in H['matches']:
    for side, blk in hm['teams'].items():
        for e in blk.get('lineup') or []:
            if e.get('player_id'): lineup_of[(hm['id'], e['player_id'])] = e
SRC = {s['id']: s for s in H['sources']}
used_ids = set(existing); out_players = list(A['players'])
def new_id(team, name, hp):
    base = f'{TEAMCODE.get(team, team[:3]).lower()}-{slug(name)}'
    if hp['id'].startswith('source:'): base += '-' + hashlib.sha1(hp['id'].encode()).hexdigest()[:6]
    cand = base; n = hp.get('national_register_number')
    if cand in used_ids and n: cand = f'{base}-{n}'
    k = 2
    while cand in used_ids: cand = f'{base}-{k}'; k += 1
    used_ids.add(cand); return cand
def year_of(d): return int(d[:4]) if d else None
for hp in H['players']:
    stats = dict(hp.get('reported_statistics') or {}); vc = hp.get('verified_career') or {}
    if vc.get('caps') is not None and stats.get('Caps') is None and stats.get('Test caps') is None: stats['Caps'] = vc['caps']
    if vc.get('points') is not None and stats.get('Points') is None and stats.get('Test points') is None: stats['Points'] = vc['points']
    num = lambda *ks: next((int(stats[k]) for k in ks if stats.get(k) is not None and str(stats[k]).lstrip('-').isdigit()), None)
    ex = existing.get(to_existing.get(hp['id']))
    team = hp['team']
    # history rows from the team sheets and scorers, in the atlas's perspective-index convention
    rows_by_mid = {}
    if ex:
        pl = [m for m in M if plays(m, ex['team'])]
        for h in ex['history']:
            if h.get('match') is not None and h['match'] < len(pl):
                mid = pl[h['match']]['id']; rows_by_mid[mid] = h
                e = lineup_of.get((mid, hp['id']))
                if e and e.get('shirt_number') and not h.get('shirt'): h['shirt'] = e['shirt_number']; report['shirt numbers filled on existing rows'] += 1
    added = []
    for mh in hp.get('match_history') or []:
        mid = mh['match_id']; t = mh.get('team') or team
        if mid in rows_by_mid or mid not in persp.get(t, {}): continue
        m = M[mid]; e = lineup_of.get((mid, hp['id'])) or {}
        pos = pos_label(e.get('position')) if e.get('position') else ('Reserve' if (mh.get('selection') or e.get('selection')) == 'named_replacement' else '')
        if e.get('captain') and pos: pos += ' (C)'
        row = {'date': m['date'], 'opponent': m['away'] if m['home'] == t else m['home'], 'position': pos, 'scoring': scoring_text(mh.get('scoring')), 'tries': sum(x.get('count') or 0 for x in (mh.get('scoring') or []) if x.get('type') == 'try'), 'match': persp[t][mid]}
        if e.get('shirt_number'): row['shirt'] = e['shirt_number']
        if mh.get('appearance_confirmed') is None and (mh.get('selection') or e.get('selection')) == 'named_replacement': row['bench'] = True   # named, appearance not confirmed
        rows_by_mid[mid] = row; added.append(row)
    wd = (hp.get('wikidata_enrichment') or {}).get('statements') or {}
    full = hp.get('full_name') or hp.get('birth_name')
    srcs = []
    for u in [hp.get('wikipedia_article'), (hp.get('verified_career') or {}).get('source_url')]:
        if u and u not in srcs: srcs.append(u)
    if ex:
        p = ex
        if added and p.get('complete'): report['rows not added to complete histories'] += len(added); added = []
        if added:
            p['history'] = sorted(p['history'] + added, key=lambda h: h['date']); report['existing profiles with history rows added'] += 1; report['history rows added to existing profiles'] += len(added)
        if p.get('caps') is None: p['caps'] = num('Caps', 'Test caps')
        if p.get('tries') is None: p['tries'] = num('Tries')
        if p.get('points') is None: p['points'] = num('Points', 'Test points')
        for k, ks in (('cons', ('Cons', 'Con')), ('pens', ('Pens', 'Pen')), ('drops', ('DGs', 'Drop'))):
            if p.get(k) is None and num(*ks) is not None: p[k] = num(*ks)
        if not p.get('fullName') and full and full != p['name']: p['fullName'] = full
        if not p.get('dob') and wd_date(wd, 'date_of_birth'): p['dob'] = wd_date(wd, 'date_of_birth')
        if not p.get('died') and wd_date(wd, 'date_of_death'): p['died'] = wd_date(wd, 'date_of_death')
        if not p.get('position') and hp.get('position'): p['position'] = pos_label(hp['position'])
        if not p.get('first') and hp.get('debut_date'): p['first'] = hp['debut_date']
        p['sources'] = (p.get('sources') or []) + [u for u in srcs if u not in (p.get('sources') or [])]
        if hp.get('national_register_number') and team != 'South Africa' and not p.get('regNo'): p['regNo'] = hp['national_register_number']
        report['existing profiles enriched'] += 1
        continue
    if not hp.get('match_history') and not stats and not hp.get('debut_date') and not hp.get('representative_debut_year'): report['register entries with nothing to show (skipped)'] += 1; continue
    hist = sorted(added, key=lambda h: h['date'])
    first = hp.get('career_first') or hp.get('debut_date') or (hist[0]['date'] if hist else None)
    last = hp.get('career_last') or (hist[-1]['date'] if hist else None)
    sy = year_of(first) or hp.get('representative_debut_year'); ey = year_of(last) or sy
    if sy and ey and ey < sy: ey = sy
    caps = num('Caps', 'Test caps')
    p = {'id': new_id(team, hp['name'], hp), 'name': hp['name'], 'caps': caps, 'tries': num('Tries'), 'points': num('Points', 'Test points'), 'first': first, 'last': last, 'history': hist,
         'sources': srcs, 'complete': hp.get('career_span_status') == 'published_complete_test_career', 'position': pos_label(hp.get('position')) if hp.get('position') else (collections.Counter(h['position'] for h in hist if h['position'] and h['position'] != 'Reserve').most_common(1) or [('', 0)])[0][0],
         'team': team, 'startYear': sy, 'endYear': ey, 'span': (f'{sy}–{ey}' if sy and ey and ey != sy else str(sy) if sy else '')}
    for k, ks in (('cons', ('Cons', 'Con')), ('pens', ('Pens', 'Pen')), ('drops', ('DGs', 'Drop'))):
        if num(*ks) is not None: p[k] = num(*ks)
    if full and full != p['name']: p['fullName'] = full
    if wd_date(wd, 'date_of_birth'): p['dob'] = wd_date(wd, 'date_of_birth')
    if wd_date(wd, 'date_of_death'): p['died'] = wd_date(wd, 'date_of_death')
    if hp.get('national_register_number'):
        if team == 'South Africa': p['number'] = str(hp['national_register_number'])
        else: p['regNo'] = hp['national_register_number']
    if last and not hp.get('career_last'): p['lastObserved'] = True
    if hp['id'].startswith('source:'):
        p['identity'] = 'review'; report['printed names kept for review'] += 1
    if hp.get('test_status') == 'no_test_caps_in_source_snapshot': p['uncapped'] = True
    out_players.append(p); report['register entries added'] += 1
    if hist: report['added entries with a match history'] += 1
HF = ['match', 'position', 'scoring', 'tries', 'shirt', 'bench']
def pack(h):
    row = [h.get('match'), h.get('position') or '', h.get('scoring') or '', h.get('tries') or 0, h.get('shirt') or 0, 1 if h.get('bench') else 0]
    while len(row) > 4 and not row[-1]: row.pop()
    return row
for p in out_players:
    p['history'] = [pack(h) for h in p['history'] if h.get('match') is not None]
    for k in ('notes',):
        if not p.get(k): p.pop(k, None)
A['historyFields'] = HF; A['players'] = out_players
A['registers'] = {t: (SRC.get(f'wiki-list-{t.lower().replace(" ", "")}') or {}).get('url') for t in sorted({p['team'] for p in out_players})}
A['registers'] = {k: v for k, v in A['registers'].items() if v}

# ---------------------------------------------------------------- 4. what the archive now says about itself
cov = {c['team']: {'register': c['register_entries'], 'sheets': c['team_sheets'], 'scorers': c['named_scorers'], 'matches': c['matches'], 'first': c['first_match'], 'last': c['last_match']} for c in H['coverage_by_nation']}
for c in H.get('coverage_by_opponent_nation') or []: cov[c['team']] = {'register': c['register_entries'], 'sheets': c['team_sheets'], 'scorers': c['named_scorers'], 'matches': c['matches_in_inherited_atlas']}
lic = H['licensing']['source_counts_by_licence']
not_est = sorted({s.get('attribution') or s['url'].split('/')[2] for s in H['sources'] if s.get('licence') == 'not_established'})
both = sum(1 for hm in H['matches'] if hm['coverage']['both_lineups']); anyl = sum(1 for hm in H['matches'] if hm['coverage']['any_lineup']); named = sum(1 for hm in H['matches'] if hm['coverage']['any_named_scorers'])
A['harvest'] = {'batch': H['progress_this_harvest']['batch_id'], 'created': H['created'], 'registerEntries': len(H['players']), 'players': len(A['players']), 'sheetsBoth': both, 'sheetsAny': anyl, 'namedScorers': named, 'scoringBreakdowns': sum(1 for m in M if m.get('scoring')), 'lineupEntries': H['summary']['lineup_entries'], 'wikidataPeople': H['summary']['distinct_wikidata_people'],
                'sourcePages': H['summary']['source_pages'], 'licences': {'CC BY-SA 4.0': lic.get('CC-BY-SA-4.0', 0) + lic.get('CC BY-SA 4.0', 0), 'CC0 1.0': lic.get('CC0-1.0', 0), 'CC BY 4.0': lic.get('CC-BY-4.0', 0), 'not established': lic.get('not_established', 0)}, 'notEstablished': not_est, 'unresolvedNames': H['summary']['unresolved_short_name_identities'], 'missingSheets': H['summary']['missing_team_sheets']}
A['playerCoverage'] = cov; A['harvestCorrections'] = corrections; A['asof'] = H['created']
out = ROOT/'data'/'rugby.json'; out.write_text(json.dumps(A, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
for k, v in sorted(report.items()): print(f'{v:>7,}  {k}')
print(f'players {len(A["players"]):,} · with a history {sum(1 for p in A["players"] if p["history"]):,} · history rows {sum(len(p["history"]) for p in A["players"]):,} · matches with breakdown {A["harvest"]["scoringBreakdowns"]:,} · {out.stat().st_size/1e6:.1f} MB')
