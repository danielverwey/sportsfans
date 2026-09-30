"""Reading editions and footers, generated from the archives.

The reading edition is section IV of every atlas and its own page on the site: the archive as plain
tables, readable with scripts off. It used to be carried verbatim from the source prototypes; generating
it from the data lets the sweepers keep it current. The markup uses the same classes the atlas
stylesheets already style (#staticArchive, .staticnav, section.panel, .static-race, .static-track).
"""
import base64, html, json, re, collections, datetime
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)
def fmt(n):
    if n is None: return '—'
    if isinstance(n, float) and n.is_integer(): n = int(n)
    return f'{n:,}' if isinstance(n, int) else str(n)
def longdate(iso):
    try: return datetime.date.fromisoformat(iso[:10]).strftime('%-d %B %Y')
    except Exception: return iso

# ------------------------------------------------------------ Formula 1 (and any F1-shaped archive)
def reading_f1(D, *, sport='f1', noun='Grand Prix', nouns='Grands Prix', who='Driver', whos='Drivers', team='Constructor', teams='Constructors', title='Formula 1', source_label='Result data'):
    drivers, teamsd, circs, lay = D['drivers'], D['teams'], D['circuits'], D.get('layouts', {})
    seasons = D['seasons']; name = lambda d: drivers.get(d, {}).get('name', d); tname = lambda t: teamsd.get(t, {}).get('name', t)
    def standings(s):
        dr = s['drivers'] if any(str(x['p']).isdigit() for x in s['drivers']) else None; derived = dr is None
        if derived:
            m = {}
            for r in s['races']:
                for x in r['rows'] + r.get('sprint', []):
                    a = m.setdefault(x['d'], {'id': x['d'], 'pts': 0, 'wins': 0, 'teams': []}); a['pts'] += x['pts']
                    if x['t'] not in a['teams']: a['teams'].append(x['t'])
                for x in r['rows']:
                    if x['dw'] and x['d'] in m: m[x['d']]['wins'] += 1
            dr = sorted(m.values(), key=lambda a: (-a['pts'], -a['wins']))
            for i, a in enumerate(dr): a['p'] = str(i + 1)
        return dr, derived
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Season archive">' + ''.join(f'<a href="#static-{s["year"]}">{s["year"]}</a>' for s in reversed(seasons)) + '</nav>']
    # eras
    if D.get('eras'):
        out.append(f'<section class="panel"><p class="eyebrow">Era lens / {seasons[0]["year"]}–{seasons[-1]["year"]}</p><h2>The eras of {E(title)}</h2><p>Interpretive periods; technical changes overlap their boundaries. Open an era for its leaders and links to every season. Interactive era filtering is available when scripts are enabled.</p>')
        for e in D['eras']:
            ss = [s for s in seasons if e['from'] <= s['year'] <= e['to']]; rows = [r for s in ss for r in s['races'] if r['rows']]
            wins = collections.Counter(); twins = collections.Counter()
            for r in rows:
                for x in r['rows']:
                    if x['dw']: wins[x['d']] += 1
                    if x['cw']: twins[x['t']] += 1
            car = e.get('car') or e.get('bike') or {}
            out.append(f'<details><summary>{e["from"]}–{e["to"]} · {E(e["name"])}</summary>' + (f'<figure class="era-car">{car.get("svg", "")}<figcaption>{E(car.get("label", ""))}</figcaption></figure>' if car.get('svg') else '') + f'<p>{E(e.get("text", ""))}</p><h3>{E(who)} leaders</h3><div class="tablewrap"><table><thead><tr><th>{E(who)}</th><th>{E(noun)} wins</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(name(d))}</td><td>{n}</td></tr>' for d, n in wins.most_common(10)) + f'</tbody></table></div><h3>{E(team)} leaders</h3><div class="tablewrap"><table><thead><tr><th>{E(team)}</th><th>Wins</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(tname(t))}</td><td>{n}</td></tr>' for t, n in twins.most_common(10)) + '</tbody></table></div><p class="fine">Seasons: ' + ' · '.join(f'<a href="#static-{s["year"]}">{s["year"]}</a>' for s in ss) + '</p></details>')
        out.append('</section>')
    # seasons
    for s in reversed(seasons):
        dr, derived = standings(s); done = [r for r in s['races'] if r['rows']]; champ = dr[0] if dr else None; ct = s['teams'][0] if s.get('teams') else None
        y = s['year']; partial = str(y) == str(D.get('cutoff', ''))[-4:]
        lead = 'Leads the standings' if partial else ('Most race points (no published table)' if derived else 'World champion')
        champ_line = ''
        if champ:
            champ_line = f'<p>{lead}: <strong>{E(name(champ["id"]))}</strong>'
            if champ.get('teams'): champ_line += ' · ' + E(' / '.join(tname(t) for t in champ['teams']))
            if ct: champ_line += f' · {E(teams)}: <strong>{E(tname(ct["id"]))}</strong>'
            champ_line += '</p>'
        else: champ_line = '<p>No results yet.</p>'
        out.append(f'<section class="panel" id="static-{y}"><p class="eyebrow">{y} · {len(done)} {E(nouns)}</p><h2>{y} season</h2>' + champ_line)
        out.append(f'<details><summary>{E(who)} championship standings{" (derived from race points)" if derived else ""}</summary><div class="tablewrap"><table><thead><tr><th>Pos</th><th>{E(who)}</th><th>Points</th><th>{E(noun)} wins</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(a["p"])}</td><td>{E(name(a["id"]))}</td><td>{fmt(a["pts"])}</td><td>{a["wins"]}</td></tr>' for a in dr) + '</tbody></table></div></details>')
        if s.get('teams'):
            out.append(f'<details><summary>{E(team)} championship standings</summary><div class="tablewrap"><table><thead><tr><th>Pos</th><th>{E(team)}</th><th>Points</th><th>Wins</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(a["p"])}</td><td>{E(tname(a["id"]))}</td><td>{fmt(a["pts"])}</td><td>{a["wins"]}</td></tr>' for a in s['teams']) + '</tbody></table></div></details>')
        for r in s['races']:
            top3 = [name(x['d']) for x in sorted(r['rows'], key=lambda x: (x['p'] if isinstance(x['p'], int) else 999))[:3]] if r['rows'] else []
            w = next((x for x in r['rows'] if x['dw']), None); col = teamsd.get(w['t'], {}).get('color', '#8b9099') if w else '#5b616b'
            out.append(f'<details class="static-race" style="border-left:3px solid {col}"><summary><span class="muted">R{r["round"]:02d} · {E(r["date"])}</span><h3>{E(r["name"])}</h3><p>{E(" | ".join(top3)) if top3 else "not yet run"}</p></summary><p>{E(r.get("circuit", ""))} · {E(r.get("country", ""))}</p>')
            if r['rows']:
                out.append(f'<h4>{E(noun)} classification</h4><div class="tablewrap"><table><thead><tr><th>Pos</th><th>{E(who)}</th><th>{E(team)}</th><th>Grid</th><th>Laps</th><th>Time / status</th><th>Points</th><th>Fastest lap</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(x.get("label", x.get("p")))}</td><td>{E(name(x["d"]))}</td><td>{E(tname(x["t"]))}</td><td>{E(x.get("g") or "—")}</td><td>{E(x.get("laps", ""))}</td><td>{E(x.get("time") or x.get("status", ""))}</td><td>{fmt(x.get("pts", 0))}</td><td>{E(x.get("fl") or "")}</td></tr>' for x in r['rows']) + '</tbody></table></div>')
                if r.get('sprint'):
                    out.append(f'<h4>Sprint classification</h4><div class="tablewrap"><table><thead><tr><th>Pos</th><th>{E(who)}</th><th>{E(team)}</th><th>Points</th><th>Status</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(x.get("label", x.get("p")))}</td><td>{E(name(x["d"]))}</td><td>{E(tname(x["t"]))}</td><td>{fmt(x.get("pts", 0))}</td><td>{E(x.get("status", ""))}</td></tr>' for x in r['sprint']) + '</tbody></table></div>')
            if r.get('url'): out.append(f'<a href="{E(r["url"])}" target="_blank" rel="noopener">{E(source_label)} ↗</a>')
            out.append('</details>')
        out.append('</section>')
    # circuits
    by_c = collections.defaultdict(list)
    for s in seasons:
        for r in s['races']:
            if r['rows']: by_c[r['cid']].append((s['year'], r))
    out.append(f'<section class="panel" id="static-circuits"><p class="eyebrow">Circuit atlas · {seasons[0]["year"]}–{seasons[-1]["year"]}</p><h2>Circuits</h2><p>Venue totals cover this archive only. Outlines are the latest documented layout; historical layouts may differ.</p>')
    for cid, rr in sorted(by_c.items(), key=lambda kv: circs.get(kv[0], {}).get('name', kv[0])):
        c = circs.get(cid, {}); last = rr[-1][1]; l = lay.get(last.get('layout') or '', {}); img = ''
        d = l.get('d')
        if not d and l.get('asset'):
            try: d = re.search(r' d="([^"]+)"', base64.b64decode(l['asset'].split(',', 1)[1]).decode('utf-8', 'replace')).group(1)
            except Exception: d = None
        if d: img = f'<div class="trackart"><svg viewBox="0 0 500 500" width="220" height="220" role="img" aria-label="{E(c.get("name", cid))} outline"><path d="{E(d)}" fill="none" stroke="#cfd3da" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/></svg></div>'
        winners = collections.Counter(name(x['d']) for _, r in rr for x in r['rows'] if x['dw'])
        out.append(f'<details class="static-track"><summary>{E(c.get("name", cid))} · {E(c.get("country", ""))} · {len(rr)} {E(nouns)}</summary>{img}<div class="tablewrap"><table><thead><tr><th>Season</th><th>Race</th><th>Winner</th></tr></thead><tbody>' + ''.join(f'<tr><td>{y}</td><td>{E(r["name"])}</td><td>{E(name(next((x["d"] for x in r["rows"] if x["dw"]), "")))}</td></tr>' for y, r in reversed(rr)) + '</tbody></table></div><p class="fine">Most wins: ' + E(', '.join(f'{n} ({k})' for n, k in winners.most_common(3))) + '</p></details>')
    out.append('</section></div>')
    return '\n'.join(out)

def footer_f1(D, carried: str) -> str:
    """The carried footer with its dated sentences refreshed from the archive."""
    last = max((r['date'] for s in D['seasons'] for r in s['races'] if r['rows']), default='')
    today = datetime.date.today().strftime('%-d %B %Y')
    return re.sub(r'Results snapshot: .*? The latest embedded race is [^.]*\.', f'Results snapshot: {E(D.get("cutoff", today))}. The latest embedded race is {longdate(last)}.', carried, count=1)

# ------------------------------------------------------------ Rugby
def reading_rugby(A):
    ten = [t['name'] for t in A['teams']]; M = A['matches']; coaches = collections.defaultdict(list)
    for c in A['coaches']: coaches[c['team']].append(c)
    out = [f'<section class="static-view"><div class="note"><strong>Offline reading edition.</strong> Your preview has not enabled JavaScript. Expand a nation below to read its match archive. Full interactive controls need a browser that runs the HTML file, or a hosted copy. This fallback is available in iPhone attachment previews.</div><h2>Ten nations · {M[0]["year"]}–{M[-1]["year"]}</h2><p class="small muted push">Scores show the named nation first. Historical recognition varies; † marks legacy fixtures. Before 1885, numeric scores count goals. Player and source notes are available in the interactive edition.</p>']
    for t in ten:
        ms = [m for m in M if t in m['eligible']]
        if not ms: continue
        out.append(f'<details><summary>{E(t)} · {len(ms)} records · {ms[0]["year"]}–{ms[-1]["year"]}</summary>')
        cs = sorted(coaches.get(t, []), key=lambda c: c['startYear'])
        if cs:
            def rec(r, word): return f'{r["n"]} {word} · {r["w"]} W / {r["d"]} D / {r["l"]} L' if r else None
            crow = lambda c: f'<tr><td>{E(c["name"])}</td><td>{E(c["tenure"])}</td><td>{rec(c.get("reported"), "matches") or "—"}</td><td>{rec(c.get("linkedRecord"), "linked matches") or "No match linkage captured"}</td></tr>'
            out.append('<div class="static-coaches"><h3>Coaching record</h3><p class="small muted">Published snapshots and linked archive statistics have different coverage. Early records can be incomplete.</p><div class="tablewrap"><table><thead><tr><th>Coach / panel</th><th>Tenure</th><th>Published record</th><th>Linked record</th></tr></thead><tbody>' + ''.join(crow(c) for c in cs) + '</tbody></table></div></div>')
        rows = []
        for m in reversed(ms):
            home = m['home'] == t; opp = m['away'] if home else m['home']; sc = f'{m["hs"]}–{m["as_"]}' if home else f'{m["as_"]}–{m["hs"]}'
            dag = ' †' if m['historical'] else ''; unit = ' (goals)' if m['scoreUnit'] == 'goals' else ''; ground = m['venue'] if not m['stadium'].startswith('ground-not-recorded') else ''
            rows.append(f'<tr><td>{E(m["date"])}</td><td>{E(opp)}{dag}</td><td>{sc}{unit}</td><td>{E(ground)}</td><td>{E(m.get("city") or "")}</td></tr>')
        out.append('<div class="tablewrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>Score</th><th>Ground</th><th>City</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></details>')
    out.append('</section>')
    return '\n'.join(out)

def footer_rugby(A, carried: str) -> str:
    return re.sub(r'Snapshot: [^·<]*', f'Snapshot: {longdate(A.get("asof", ""))} ', carried)

# ------------------------------------------------------------ Cricket
def reading_cricket(core):
    """Every international, year by year: date, format, sides, innings totals, result, ground."""
    V = core['venues']; games = core['games']; by = collections.defaultdict(list)
    for g in games: by[g['y']].append(g)
    sc = lambda g, t: ' & '.join(('forfeited' if i[5] else f"{i[1]}{'/' + str(i[2]) if i[2] < 10 else ''}{'d' if i[4] else ''}") for i in g.get('sc', []) if i[0] == t and not i[6])
    res = lambda g: 'No result' if g['result'] == 'no result' else 'Tied' if g['result'] == 'tie' else 'Drawn' if g['result'] == 'draw' else (f"{g['winner']} won by {g['margin']}" if g.get('margin') else f"{g['winner']} won")
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Year archive">' + ''.join(f'<a href="#static-{y}">{y}</a>' for y in sorted(by, reverse=True)) + '</nav>']
    out.append(f'<section class="panel"><p class="eyebrow">International cricket · {min(by)}–{max(by)}</p><h2>Every international, on the page</h2><p>{len(games):,} men’s and women’s Tests, one-day and T20 internationals. Innings totals are given where a scorecard is recorded: every men’s Test from 1877 and ODI from 1971, the T20Is and the women’s game from their first recorded cards. Player figures and full scorecards are in the interactive edition.</p></section>')
    for y in sorted(by, reverse=True):
        ms = by[y]; out.append(f'<section class="panel" id="static-{y}"><p class="eyebrow">{y} · {len(ms)} matches</p><h2>{y}</h2><div class="tablewrap"><table><thead><tr><th>Date</th><th>Format</th><th>Sides</th><th>Scores</th><th>Result</th><th>Ground</th></tr></thead><tbody>')
        for g in ms:
            a, b = g['teams']; ground = V.get(g['v'], {}).get('n', '') if g.get('v') else ''
            out.append(f'<tr><td>{E(g["date"])}</td><td>{E(g["f"])}{" (W)" if g["g"] == "W" else ""}</td><td>{E(a)} v {E(b)}</td><td>{E(sc(g, a))}{" · " if sc(g, a) and sc(g, b) else ""}{E(sc(g, b))}</td><td>{E(res(g))}</td><td>{E(ground)}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append('</div>'); return '\n'.join(out)

def footer_cricket(core):
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / CRICKET · THE INTERNATIONAL EDITION</div><p>An independent, fan-made record of international cricket. Match results and scorecards from 1877: ball by ball from the 2000s (Cricsheet), from historical scorecards before that; player figures and line-ups are added up from the cards, published careers are shown beside them. Latest included match: {E(longdate(core.get("lastDate", "")))}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(core.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with the ICC or any board is implied</span><span><a href="https://cricsheet.org/" target="_blank" rel="noopener">Cricsheet</a> (ODC-By) · <a href="https://www.kaggle.com/datasets/qammarshahzad/cricket-match-dataset-test-nations-18772025" target="_blank" rel="noopener">Historical results</a> · <a href="https://huggingface.co/bhuvaneshprasad" target="_blank" rel="noopener">Historical scorecards</a> · <a href="https://en.wikipedia.org/wiki/Lists_of_cricketers" target="_blank" rel="noopener">Wikipedia player lists</a> (CC BY-SA) · <a href="https://www.icc-cricket.com/" target="_blank" rel="noopener">ICC</a> · <a href="#top">Back to top ↑</a></span></div></footer>'

def _tennis_ctx(core):
    P = core['players']; T = {k: dict(zip(core['tFields'], v)) for k, v in core['tournaments'].items()}; E_ = {k: dict(zip(core['eFields'], v)) for k, v in core['editions'].items()}
    C = [dict(zip(core['cFields'], r)) for r in core['champions']]
    pn = lambda ids: ' / '.join(P.get(i, {}).get('n', i) for i in (ids or []))
    return P, T, E_, C, pn
def reading_tennis(core):
    """Every title, year by year: date, tournament, draw, surface, champion, finalist, score; then each major's roll of honour."""
    P, T, ED, C, pn = _tennis_ctx(core); by = collections.defaultdict(list)
    for c in C: by[c['y']].append(c)
    circ = {'MS': 'ATP singles', 'WS': 'WTA singles', 'MD': 'ATP doubles', 'WD': 'WTA doubles', 'XD': 'Mixed doubles'}
    majors = [k for k, t in T.items() if t.get('major')]
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Year archive">' + ''.join(f'<a href="#static-{y}">{y}</a>' for y in sorted(by, reverse=True)) + '</nav>']
    out.append(f'<section class="panel"><p class="eyebrow">Tennis · {min(by)}–{max(by)}</p><h2>Every title, on the page</h2><p>{len(C):,} tour-level titles: Wimbledon from 1877, the whole ATP and WTA calendar from the first open season of 1968, with champion, finalist and score as recorded. Draws, match statistics and head-to-heads are in the interactive edition.</p></section>')
    out.append('<section class="panel" id="static-majors"><p class="eyebrow">The majors</p><h2>Rolls of honour</h2>' + ''.join(f'<h3>{E(T[m]["n"])}</h3><div class="tablewrap"><table><thead><tr><th>Year</th><th>Draw</th><th>Champion</th><th>Runner-up</th><th>Score</th></tr></thead><tbody>' + ''.join(f'<tr><td>{c["y"]}</td><td>{E(circ.get(c["c"], c["c"]))}</td><td>{E(pn(c["w"]))}</td><td>{E(pn(c["l"])) or "—"}</td><td>{E(c["s"])}</td></tr>' for c in sorted([c for c in C if c['t'] == m], key=lambda c: (-c['y'], c['c']))) + '</tbody></table></div>' for m in majors) + '</section>')
    for y in sorted(by, reverse=True):
        cs = sorted(by[y], key=lambda c: (ED.get(c['id'], {}).get('date', f'{c["y"]}-00'), c['c']))
        out.append(f'<section class="panel" id="static-{y}"><p class="eyebrow">{y} · {len(cs)} titles</p><h2>{y}</h2><div class="tablewrap"><table><thead><tr><th>Date</th><th>Tournament</th><th>Draw</th><th>Surface</th><th>Champion</th><th>Runner-up</th><th>Score</th></tr></thead><tbody>')
        for c in cs:
            e = ED.get(c['id'], {}); out.append(f'<tr><td>{E(e.get("date", str(c["y"])))}</td><td>{E(T.get(c["t"], {}).get("n", c["t"]))}</td><td>{E(circ.get(c["c"], c["c"]))}</td><td>{E(e.get("surface", T.get(c["t"], {}).get("s", "")) or "")}</td><td>{E(pn(c["w"]))}</td><td>{E(pn(c["l"])) or "—"}</td><td>{E(c["s"])}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append('</div>'); return '\n'.join(out)

def footer_tennis(core):
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / TENNIS · THE TOUR EDITION</div><p>An independent, fan-made record of tennis. Wimbledon’s champions from 1877; every tour-level match of the ATP and WTA from 1968, with seedings, rankings and serve statistics where the source records them. Latest included event: {E(longdate(core.get("lastDate", "")))}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(core.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with the ATP, the WTA, the ITF or any tournament is implied</span><span><a href="https://github.com/JeffSackmann" target="_blank" rel="noopener">Jeff Sackmann / Tennis Abstract</a> (CC BY-NC-SA 4.0) · <a href="https://www.wimbledon.com/" target="_blank" rel="noopener">Wimbledon’s records</a> · <a href="#top">Back to top ↑</a></span></div></footer>'

# ------------------------------------------------------------ MotoGP and World Superbike (Wikipedia-built archives, adapted by tools/adapt_bikes.js)
BIKE_META = {'motogp': ('MotoGP', 'Grand Prix', 'Grands Prix', 'THE PREMIER-CLASS EDITION', 'premier-class world championship racing, 500cc from 1949 and MotoGP from 2002', 'the FIM, Dorna or any team'), 'sbk': ('World Superbike', 'race', 'races', 'THE WORLD SUPERBIKE EDITION', 'the Superbike World Championship from its first season in 1988', 'the FIM, WorldSBK or any team')}
def reading_bikes(tag, D):
    name, noun, nouns, *_ = BIKE_META[tag]
    return reading_f1(D, sport=tag, noun=noun, nouns=nouns, who='Rider', whos='Riders', team='Manufacturer', teams='Manufacturers', title=name, source_label='Result data')
def footer_bikes(tag, A):
    name, noun, nouns, edition, scope, unaff = BIKE_META[tag]
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / {E(name.upper())} · {edition}</div><p>An independent, fan-made record of {scope}. Every result, calendar and published standing is transcribed from Wikipedia’s season articles (CC BY-SA 4.0), with circuit outlines from OpenStreetMap; nothing from the series’ own results service or artwork is carried. Blank cells stay blank. Latest included {noun}: {E(longdate(A.get("lastDate", "")))}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(A.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with {unaff} is implied</span><span><a href="https://en.wikipedia.org/" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> (ODbL) · <a href="#top">Back to top ↑</a></span></div></footer>'

# ------------------------------------------------------------ Isle of Man TT
def reading_tt(core):
    """Every TT race, year by year: class, course, winner, machine, average speed, time."""
    RF = core['resultFields']; R = core['riders']; pn = lambda ids: ' / '.join(R.get(i, {}).get('name', i) for i in (ids or []))
    by = collections.defaultdict(list)
    for r in core['races']: by[r['y']].append(r)
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Year archive">' + ''.join(f'<a href="#static-{y}">{y}</a>' for y in sorted(by, reverse=True)) + '</nav>']
    out.append(f'<section class="panel"><p class="eyebrow">Isle of Man TT · {min(by)}–{max(by)}</p><h2>Every race, on the page</h2><p>{len(core["races"])} TT races over {len(by)} race weeks, with the winner, machine, course and race average as the sources record them. Full classifications, where the archive holds them, are in the interactive edition. Years without a TT — 1915–19, 1940–46, 2001 and 2020–21 — are absent, not empty.</p></section>')
    for y in sorted(by, reverse=True):
        rs = by[y]; out.append(f'<section class="panel" id="static-{y}"><p class="eyebrow">{y} · {len(rs)} races</p><h2>{y}</h2><div class="tablewrap"><table><thead><tr><th>Race</th><th>Course</th><th>Laps</th><th>Winner</th><th>Machine</th><th>Average (mph)</th><th>Time</th></tr></thead><tbody>')
        for r in rs:
            w = next((dict(zip(RF, x)) for x in r['results'] if x[1] == 1), None)
            out.append(f'<tr><td>{E(r["name"])}</td><td>{E(r["course"])}</td><td>{r["laps"] or ""}</td><td>{E(pn(w["crew"])) if w else "—"}</td><td>{E(w["machine"] or w["marque"] or "") if w else ""}</td><td>{w["mph"] if w and w["mph"] else ""}</td><td>{E(w["time"] or "") if w else ""}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append('</div>'); return '\n'.join(out)

def footer_tt(core):
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / ISLE OF MAN TT · THE MOUNTAIN EDITION</div><p>An independent, fan-made record of the Isle of Man TT from the first race of 1907. Winners and classifications transcribed from Wikipedia’s lists and race articles (CC BY-SA 4.0), the Mountain Course from OpenStreetMap; nothing from the event’s own results service or artwork is carried. Race averages are kept distinct from lap records. Latest included TT: {core.get("lastYear", "")}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(core.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with the Isle of Man TT Races, the ACU or the Isle of Man Government is implied</span><span><a href="https://de.wikipedia.org/wiki/Liste_der_Isle-of-Man-TT-Sieger" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) · <a href="https://www.openstreetmap.org/relation/188240" target="_blank" rel="noopener">OpenStreetMap</a> (ODbL) · <a href="#top">Back to top ↑</a></span></div></footer>'

# ------------------------------------------------------------ UFC (the cage edition)
def _ufc_rows(core):
    BF = core['boutFields']; return [dict(zip(BF, x)) for x in core['bouts']]
def reading_ufc(core):
    """Every event, year by year: date, venue, main event, and every bout of the card."""
    F = core['fighters']; pn = lambda i: F.get(i, {}).get('name', i); DL = {d['key']: d['label'] for d in core['divisions']}
    rows = _ufc_rows(core); by_e = collections.defaultdict(list)
    for b in rows: by_e[b['e']].append(b)
    by = collections.defaultdict(list)
    for e in core['events']: by[e['y']].append(e)
    who = lambda b: f'<b>{E(pn(b["w"]))}</b> def. {E(pn(b["b"] if b["w"] == b["a"] else b["a"]))}' if b['res'] == 'W' else f'{E(pn(b["a"]))} vs. {E(pn(b["b"]))}'
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Year archive">' + ''.join(f'<a href="#static-{y}">{y}</a>' for y in sorted(by, reverse=True)) + '</nav>']
    out.append(f'<section class="panel"><p class="eyebrow">UFC bouts · {min(by)}–{max(by)}</p><h2>Every card, on the page</h2><p>{len(core["events"])} events and {len(rows):,} bouts over {len(by)} years, each card in the order its source lists it — the main event first — with the weight class, the result, the method, the round and the time as recorded. Title bouts are marked. Nothing here is affiliated with the promotion; its names identify the events.</p></section>')
    for y in sorted(by, reverse=True):
        es = by[y]; out.append(f'<section class="panel" id="static-{y}"><p class="eyebrow">{y} · {len(es)} events · {sum(len(by_e[e["id"]]) for e in es)} bouts</p><h2>{y}</h2>')
        for e in sorted(es, key=lambda e: e['date'], reverse=True):
            bs = by_e[e['id']]
            place = ' · '.join(E(x) for x in (e['venue'], e['city'], e['country']) if x); att = f' · attendance {e["att"]:,}' if e.get('att') else ''
            out.append(f'<h3>{E(e["name"])}</h3><p class="small muted">{E(longdate(e["date"]))}{" · " + place if place else ""}{att}</p><div class="tablewrap"><table><thead><tr><th>Card</th><th>Weight class</th><th>Result</th><th>Method</th><th>R</th><th>Time</th><th>Note</th></tr></thead><tbody>')
            for b in bs: out.append(f'<tr><td>{E(b["card"])}</td><td>{E(b["wc"] or DL.get(b["div"], b["div"]))}</td><td>{who(b)}</td><td>{E(b["method"])}</td><td>{b["round"] if b["round"] is not None else ""}</td><td>{E(b["time"] or "")}</td><td>{"Title bout. " if b["title"] else ""}{E(b["notes"]) if b["notes"] and not b["title"] else ""}</td></tr>')
            out.append('</tbody></table></div>')
        out.append('</section>')
    out.append('</div>'); return '\n'.join(out)

def footer_ufc(core):
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / UFC BOUTS · THE CAGE EDITION</div><p>An independent, fan-made record of every UFC bout since the first tournament of 1993. Results, methods, rounds, times, venues and bonus awards transcribed from Wikipedia’s event articles (CC BY-SA 4.0); fighter nationality, birth date and height from Wikidata (CC0); nothing from the promotion’s own site, its statistics partner or its artwork is carried. Latest included event: {E(longdate(core.get("lastDate", "")))}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(core.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with the UFC, Zuffa or TKO Group Holdings is implied; their names are used only to identify the events</span><span><a href="https://en.wikipedia.org/wiki/List_of_UFC_events" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) · <a href="https://www.wikidata.org/" target="_blank" rel="noopener">Wikidata</a> (CC0) · <a href="#top">Back to top ↑</a></span></div></footer>'

# ------------------------------------------------------------ Dakar Rally (the desert edition)
def reading_dakar(core):
    """Every edition, newest first: route, era, and the first three of every class."""
    RF = core['resultFields']; P = core['people']; pn = lambda i: P.get(i, {}).get('name', i)
    eds = sorted(core['editions'], key=lambda e: -e['y']); c = core['coverage']
    out = ['<div id="staticArchive"><nav class="staticnav" aria-label="Year archive">' + ''.join(f'<a href="#static-{e["y"]}">{e["y"]}</a>' for e in eds) + '</nav>']
    out.append(f'<section class="panel"><p class="eyebrow">Dakar Rally · {eds[-1]["y"]}–{eds[0]["y"]}</p><h2>Every edition, on the page</h2><p>{c["held"]} editions run and one cancelled, {c["podiums"]} podium places across {c["categories"]} classes, each edition with its route as the source names it, its era, and the first three of every class — the lead driver or rider, the crew, and the make. Africa from 1979, South America from 2009, Saudi Arabia from 2020.</p></section>')
    for e in eds:
        rows = [dict(zip(RF, x)) for x in e['results']]
        tail = ' · cancelled' if e['cancelled'] else f' · {len(e["cats"])} classes'
        out.append(f'<section class="panel" id="static-{e["y"]}"><p class="eyebrow">{e["y"]} · {E(e["era"])}{tail}</p><h2>{e["y"]}</h2><p class="small muted">{E(e["route"])}</p>')
        if e['cancelled']: out.append('<p>The rally was cancelled before the start and has no results.</p></section>'); continue
        out.append('<div class="tablewrap"><table><thead><tr><th>Class</th><th>Place</th><th>Driver / rider</th><th>Crew</th><th>Make</th></tr></thead><tbody>')
        for r in rows:
            crew = ' / '.join(pn(i) for i in r['crew'] if i != r['driver'])
            out.append(f'<tr class="{"win" if r["rank"] == 1 else ""}"><td>{E(r["cat"])}</td><td>{r["rank"]}</td><td><b>{E(pn(r["driver"]))}</b></td><td>{E(crew)}</td><td>{E(r["make"])}</td></tr>')
        out.append('</tbody></table></div></section>')
    out.append('</div>'); return '\n'.join(out)

def footer_dakar(core):
    return f'<footer><div class="footer-top"><div><div class="brand" style="font-size:11px">APEX / DAKAR RALLY · THE DESERT EDITION</div><p>An independent, fan-made record of the Dakar Rally from the first Paris–Dakar of 1979. Routes, eras and the podium of every class transcribed from Wikipedia’s Dakar Rally article (CC BY-SA 4.0) at a recorded revision; the land silhouette from Natural Earth (public domain). Routes are drawn schematically between their named towns, not stage by stage. Latest included edition: {core.get("lastYear", "")}. This is a dated snapshot, not a live feed.</p></div><button class="js-only" id="sources">Sources &amp; coverage ↗</button></div><div class="footer-bottom"><span>Snapshot: {E(longdate(core.get("snapshot", "")))} · Self-contained offline HTML · No affiliation with the Amaury Sport Organisation or the Dakar Rally is implied; the name identifies the event</span><span><a href="https://en.wikipedia.org/wiki/Dakar_Rally" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) · <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a> (public domain) · <a href="#top">Back to top ↑</a></span></div></footer>'
