"""Split the tennis prototype archive into a core file and yearly match shards.

  python3 tools/prepare_tennis.py <the reader's export: tennis_data.json, .json.gz, or the prototype page>

Writes data/tennis.json (players, tournaments, editions, titles, player-season rows, the river, rivals, records)
and data/tennis_matches/<year>.json (every match of that year, keyed by edition). Nothing in the source is altered;
the offline edition embeds the whole set again.
"""
import json, sys, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools')); from archive_in import load_archive
def prepare(D):
    """The source archive → (the core file, {year: {edition: [match rows]}}). Pure."""
    G = D['games']; P = D['players']; T = D['tournaments']; E = D['editions']; C = D['champions']
    F = {k: i for i, k in enumerate(D['gameFields'])}
    IOC = {'USA': 'United States', 'GBR': 'Great Britain', 'AUS': 'Australia', 'GER': 'Germany', 'RSA': 'South Africa', 'FRA': 'France', 'ITA': 'Italy', 'ESP': 'Spain', 'JPN': 'Japan', 'ARG': 'Argentina', 'SWE': 'Sweden', 'NZL': 'New Zealand', 'BRA': 'Brazil', 'CAN': 'Canada', 'RUS': 'Russia', 'NED': 'Netherlands', 'CZE': 'Czechia', 'SUI': 'Switzerland', 'AUT': 'Austria', 'IRL': 'Ireland', 'MEX': 'Mexico', 'ROU': 'Romania', 'CHN': 'China', 'BEL': 'Belgium', 'IND': 'India', 'HUN': 'Hungary', 'KOR': 'South Korea', 'UNK': 'Unknown', 'COL': 'Colombia', 'POL': 'Poland', 'CHI': 'Chile', 'CRO': 'Croatia', 'ISR': 'Israel', 'BUL': 'Bulgaria', 'TPE': 'Chinese Taipei', 'HKG': 'Hong Kong', 'FIN': 'Finland', 'UKR': 'Ukraine', 'THA': 'Thailand', 'TUR': 'Türkiye', 'INA': 'Indonesia', 'DEN': 'Denmark', 'PHI': 'Philippines', 'NOR': 'Norway', 'EGY': 'Egypt', 'ECU': 'Ecuador', 'PER': 'Peru', 'VEN': 'Venezuela', 'URU': 'Uruguay', 'POR': 'Portugal', 'MAS': 'Malaysia', 'GRE': 'Greece', 'SRB': 'Serbia', 'SVK': 'Slovakia', 'LUX': 'Luxembourg', 'MAR': 'Morocco', 'SLO': 'Slovenia', 'BOL': 'Bolivia', 'PUR': 'Puerto Rico', 'URS': 'Soviet Union', 'SGP': 'Singapore', 'PAR': 'Paraguay', 'DOM': 'Dominican Republic', 'SRI': 'Sri Lanka', 'IRI': 'Iran', 'PAK': 'Pakistan', 'JAM': 'Jamaica', 'LAT': 'Latvia', 'EST': 'Estonia', 'UZB': 'Uzbekistan', 'ZIM': 'Zimbabwe', 'BLR': 'Belarus', 'TUN': 'Tunisia', 'CYP': 'Cyprus', 'GUA': 'Guatemala', 'ALG': 'Algeria', 'KAZ': 'Kazakhstan', 'CRC': 'Costa Rica', 'LTU': 'Lithuania', 'GEO': 'Georgia', 'MDA': 'Moldova', 'TCH': 'Czechoslovakia', 'BAR': 'Barbados', 'BAH': 'Bahamas', 'YUG': 'Yugoslavia', 'SYR': 'Syria', 'CUB': 'Cuba', 'BIH': 'Bosnia and Herzegovina', 'LIB': 'Lebanon', 'KEN': 'Kenya', 'ESA': 'El Salvador', 'MON': 'Monaco', 'FRG': 'West Germany', 'MKD': 'North Macedonia', 'NGR': 'Nigeria', 'PAN': 'Panama', 'TTO': 'Trinidad and Tobago', 'ARM': 'Armenia', 'MLT': 'Malta', 'SEN': 'Senegal', 'KUW': 'Kuwait', 'VIE': 'Vietnam', 'HAI': 'Haiti', 'BER': 'Bermuda', 'GHA': 'Ghana', 'MAD': 'Madagascar', 'KGZ': 'Kyrgyzstan', 'BOT': 'Botswana', 'MNE': 'Montenegro', 'TOG': 'Togo', 'JOR': 'Jordan', 'ISL': 'Iceland', 'CIV': 'Côte d’Ivoire', 'AHO': 'Netherlands Antilles', 'QAT': 'Qatar', 'POC': 'Pacific Oceania', 'TKM': 'Turkmenistan', 'NAM': 'Namibia', 'LIE': 'Liechtenstein', 'TJK': 'Tajikistan', 'KSA': 'Saudi Arabia', 'IRQ': 'Iraq', 'BRN': 'Bahrain', 'CMR': 'Cameroon', 'BEN': 'Benin', 'UAE': 'United Arab Emirates', 'LBN': 'Lebanon', 'AZE': 'Azerbaijan', 'RHO': 'Rhodesia', 'OMA': 'Oman', 'BAN': 'Bangladesh', 'HON': 'Honduras', 'ETH': 'Ethiopia', 'TRI': 'Trinidad and Tobago', 'ECA': 'East Caribbean', 'CUW': 'Curaçao', 'ANT': 'Antigua and Barbuda', 'AND': 'Andorra', 'FIJ': 'Fiji', 'MRI': 'Mauritius', 'ZAM': 'Zambia', 'CAR': 'Caribbean', 'CGO': 'Congo', 'LBA': 'Libya', 'SUD': 'Sudan', 'MGL': 'Mongolia', 'VAN': 'Vanuatu', 'GUM': 'Guam', 'SAM': 'Samoa', 'SCG': 'Serbia and Montenegro', 'SMR': 'San Marino', 'LES': 'Lesotho', 'SOL': 'Solomon Islands', 'PNG': 'Papua New Guinea', 'NIG': 'Niger', 'GDR': 'East Germany', 'BRU': 'Brunei', 'BUR': 'Burkina Faso', 'COK': 'Cook Islands', 'MHL': 'Marshall Islands', 'BRI': 'British Isles', 'NMI': 'Northern Mariana Islands', 'MOZ': 'Mozambique', 'TGO': 'Togo', 'SUR': 'Suriname', 'PRY': 'Paraguay', 'ANG': 'Angola', 'BDI': 'Burundi', 'GUY': 'Guyana', '': 'Unlisted'}
    ioc_of = lambda pid: (P.get(pid, {}).get('ioc') or '')
    surf_key = {'Hard': 'h', 'Clay': 'c', 'Grass': 'g', 'Carpet': 'i', 'Unknown': 'i', 'clay': 'c'}
    MAJOR = {k for k, t in T.items() if t.get('major')}
    # ---- shards, player-season rows, river, rivals, records
    shards = collections.defaultdict(lambda: collections.defaultdict(list)); PSR = {}; river = collections.defaultdict(lambda: collections.defaultdict(collections.Counter)); riv = collections.defaultdict(collections.Counter)
    rec = collections.defaultdict(lambda: collections.defaultdict(list))
    def ps(pid, y, c):
        return PSR.setdefault((pid, y, c), {'w': 0, 'l': 0, 't': 0, 'f': 0, 'mj': 0, 'hw': 0, 'hl': 0, 'cw': 0, 'cl': 0, 'gw': 0, 'gl': 0, 'iw': 0, 'il': 0, 'sw': 0, 'sl': 0})
    for g in G:
        e = E[g[F['e']]]; y = e['y']; c = e['c']; sk = surf_key.get(e['surface'], 'i')
        shards[y][g[F['e']]].append([g[F['id']], g[F['w']], g[F['l']], g[F['s']], g[F['r']], g[F['n']], g[F['mins']], g[F['bo']], g[F['ws']], g[F['ls']], g[F['wr']], g[F['lr']], g[F['st']], g[F['src']]])
        for pid in g[F['w']]:
            a = ps(pid, y, c); a['w'] += 1; a[sk + 'w'] += 1
        for pid in g[F['l']]:
            a = ps(pid, y, c); a['l'] += 1; a[sk + 'l'] += 1
        if c in ('MS', 'WS') and g[F['w']] and g[F['l']]:
            river[c][y][ioc_of(g[F['w']][0])] += 1
            w, l = g[F['w']][0], g[F['l']][0]; riv[w][l] += 1; riv[l][w] += 0
            mins = g[F['mins']]; st = g[F['st']]; base = [g[F['id']], y, w, l, g[F['s']], g[F['r']]]
            if mins and mins >= 150 and mins < 700: rec[c]['longest'].append([mins] + base)
            if st and st[0][0] is not None and st[0][0] >= 25: rec[c]['aces'].append([st[0][0]] + base + [w])
            if st and st[1][0] is not None and st[1][0] >= 25: rec[c]['aces'].append([st[1][0]] + base + [l])
            wr, lr = g[F['wr']], g[F['lr']]
            if wr and lr and lr <= 3 and wr >= 100: rec[c]['upsets'].append([wr - lr] + base + [wr, lr])
            # games in the match
            try:
                gm = sum(int(x) for s in g[F['s']].replace('RET', '').split() for x in s.split('(')[0].split('-') if x.strip().isdigit())
                if gm >= 60: rec[c]['games'].append([gm] + base)
            except Exception: pass
    for c in rec:
        for k in rec[c]: rec[c][k] = sorted(rec[c][k], key=lambda r: -r[0])[:30]
    # titles, finals and majors come from the roll of honour (match-backed from 1968, the majors' own records before)
    titles = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for ch in C:
        for pid in ch['w']:
            a = ps(pid, ch['y'], ch['c']); a['t'] += 1; a['f'] += 1; a['mj'] += (ch['t'] in MAJOR)
            if ch['c'] in ('MS', 'WS'): titles[ch['c']][ch['y']][ioc_of(pid)] += 1
        for pid in ch['l']:
            a = ps(pid, ch['y'], ch['c']); a['f'] += 1
    PSF = ['p', 'y', 'c', 'w', 'l', 't', 'f', 'mj', 'hw', 'hl', 'cw', 'cl', 'gw', 'gl', 'iw', 'il']
    PS = [[pid, y, c] + [a[k] for k in PSF[3:]] for (pid, y, c), a in sorted(PSR.items())]
    rivals = {}
    for pid, opp in riv.items():
        tops = sorted(opp.items(), key=lambda x: -(x[1] + riv[x[0]][pid]))[:6]
        rivals[pid] = [[o, w, riv[o][pid]] for o, w in tops if w + riv[o][pid] >= 3]
        if not rivals[pid]: del rivals[pid]
    # ---- tournaments: summary from editions and titles
    tsum = {}
    for eid, e in E.items():
        t = tsum.setdefault(e['t'], {'eds': 0, 'first': e['y'], 'last': e['y'], 'circ': collections.Counter(), 'surf': collections.Counter(), 'level': collections.Counter()})
        t['eds'] += 1; t['first'] = min(t['first'], e['y']); t['last'] = max(t['last'], e['y']); t['circ'][e['c']] += 1; t['surf'][e['surface']] += 1; t['level'][e['level']] += 1
    tops = collections.defaultdict(collections.Counter)
    for ch in C:
        for pid in ch['w']: tops[ch['t']][pid] += 1
        t = tsum.setdefault(ch['t'], {'eds': 0, 'first': ch['y'], 'last': ch['y'], 'circ': collections.Counter(), 'surf': collections.Counter(), 'level': collections.Counter()}); t['first'] = min(t['first'], ch['y']); t['last'] = max(t['last'], ch['y'])
    tourn = {}
    for tid, t in T.items():
        s = tsum.get(tid); top = tops[tid].most_common(1)[0] if tops[tid] else None
        tourn[tid] = {'n': t['n'], 'c': t.get('c'), 'c2': t.get('c2'), 's': t.get('s'), 'city': t.get('city', ''), 'url': t.get('url', ''), 'major': bool(t.get('major')), 'first': s['first'] if s else None, 'last': s['last'] if s else None, 'eds': s['eds'] if s else 0, 'titles': sum(tops[tid].values()), 'top': list(top) if top else None, 'circ': dict(s['circ']) if s else {}, 'surf': s['surf'].most_common(1)[0][0] if s and s['surf'] else t.get('s'), 'levels': dict(s['level']) if s else {}}
    editions = {eid: {'t': e['t'], 'c': e['c'], 'y': e['y'], 'date': e['date'], 'surface': 'Clay' if e['surface'] == 'clay' else e['surface'], 'level': e['level'], 'name': e['name'], 'draw': e['draw'], 'team': e['team'], 'n': len(shards[e['y']][eid])} for eid, e in E.items()}
    players = {pid: {k: v for k, v in p.items() if k != 'historic' or v} for pid, p in P.items()}
    TF = ['n', 'c', 'c2', 's', 'city', 'url', 'major', 'first', 'last', 'eds', 'titles', 'top', 'circ', 'surf']
    EF = ['t', 'c', 'y', 'date', 'surface', 'level', 'name', 'draw', 'team', 'n']
    CF = ['id', 't', 'c', 'y', 'w', 'l', 's', 'm', 'src', 'url']
    tourn_rows = {tid: [t[k] for k in TF] for tid, t in tourn.items()}
    edition_rows = {eid: [e['t'], e['c'], e['y'], e['date'], e['surface'], e['level'], '' if e['name'] == tourn[e['t']]['n'] else e['name'], e['draw'], 1 if e['team'] else 0, e['n']] for eid, e in editions.items()}
    champ_rows = [[ch.get(k, '') for k in CF] for ch in C]
    core = {'players': players, 'tFields': TF, 'tournaments': tourn_rows, 'eFields': EF, 'editions': edition_rows, 'cFields': CF, 'champions': champ_rows, 'psFields': PSF, 'ps': PS, 'river': {c: {y: dict(v) for y, v in ys.items()} for c, ys in river.items()}, 'titlesBy': {c: {y: dict(v) for y, v in ys.items()} for c, ys in titles.items()}, 'rivals': rivals, 'records': {c: dict(v) for c, v in rec.items()}, 'ioc': IOC, 'coverage': D['coverage'], 'snapshot': D['snapshot'], 'sourceCommit': D['sourceCommit'], 'statFields': D['statFields'], 'matchYears': sorted(shards), 'lastDate': max(e['date'] for e in E.values())}
    return core, shards

GF = ['id', 'e', 'w', 'l', 's', 'r', 'n', 'mins', 'bo', 'ws', 'ls', 'wr', 'lr', 'st', 'src']
def read_shards():
    return {int(f.stem): json.loads(f.read_text(encoding='utf-8')) for f in sorted((ROOT/'data'/'tennis_matches').glob('*.json'))}
def unprepare(core, shards):
    """The site's files back into the source archive, so that prepare(unprepare(core, shards)) gives them again. The
    sweeper merges a season's new matches into this and prepares the whole again."""
    TFi = {k: i for i, k in enumerate(core['tFields'])}; EFi = {k: i for i, k in enumerate(core['eFields'])}
    T = {tid: {'n': r[TFi['n']], 'c': r[TFi['c']], 'c2': r[TFi['c2']], 's': r[TFi['s']], 'city': r[TFi['city']], 'url': r[TFi['url']], 'major': r[TFi['major']]} for tid, r in core['tournaments'].items()}
    low_clay = {tid for tid, r in core['tournaments'].items() if r[TFi['surf']] == 'clay'}   # a source that spells the surface in lower case
    E = {eid: {'t': r[EFi['t']], 'c': r[EFi['c']], 'y': r[EFi['y']], 'date': r[EFi['date']], 'surface': 'clay' if r[EFi['surface']] == 'Clay' and r[EFi['t']] in low_clay else r[EFi['surface']], 'level': r[EFi['level']],
               'name': r[EFi['name']] or T[r[EFi['t']]]['n'], 'draw': r[EFi['draw']], 'team': bool(r[EFi['team']])} for eid, r in core['editions'].items()}
    games = [[m[0], eid, m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12], m[13]] for y in sorted(shards) for eid, rows in shards[y].items() for m in rows]
    C = [dict(zip(core['cFields'], r)) for r in core['champions']]
    return {'players': core['players'], 'tournaments': T, 'editions': E, 'champions': C, 'games': games, 'gameFields': GF,
            'coverage': core['coverage'], 'snapshot': core['snapshot'], 'sourceCommit': core['sourceCommit'], 'statFields': core['statFields']}

def write(core, shards):
    out = ROOT/'data'; out.mkdir(exist_ok=True); (out/'tennis_matches').mkdir(exist_ok=True)
    for f in (out/'tennis_matches').glob('*.json'): f.unlink()
    tot = 0
    for y, eds in sorted(shards.items()):
        b = json.dumps(eds, ensure_ascii=False, separators=(',', ':')).encode('utf-8'); (out/'tennis_matches'/f'{y}.json').write_bytes(b); tot += len(b)
    cb = json.dumps(core, ensure_ascii=False, separators=(',', ':')).encode('utf-8'); (out/'tennis.json').write_bytes(cb)
    return len(cb), tot

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit('usage: python tools/prepare_tennis.py <tennis_data.json or the prototype page>')
    D = load_archive(sys.argv[1], need=('games', 'players', 'tournaments', 'editions', 'champions', 'gameFields'))
    core, shards = prepare(D)
    cb, tot = write(core, shards)
    print(f'core {cb/1e6:.1f} MB · {len(core["ps"]):,} player-season rows · {len(core["rivals"]):,} players with rivals · shards {len(shards)} years, {tot/1e6:.1f} MB · matches {sum(len(m) for eds in shards.values() for m in eds.values()):,}')
