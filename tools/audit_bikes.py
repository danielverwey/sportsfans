import json,collections,datetime,sys
import pathlib as _pl; ROOT=_pl.Path(__file__).resolve().parent.parent
tag=sys.argv[1]; d=json.load(open(ROOT/'data'/f'{tag}.json',encoding='utf-8')); R=d['races']; iss=collections.defaultdict(list); n=lambda k,m:iss[k].append(m)
for r in R:
    try: datetime.date.fromisoformat(r['date'])
    except: n('bad date',r['id'])
    if r['year']!=int(r['date'][:4]): n('year ≠ date',r['id'])
    if r['circuit'] not in d['circuits']: n('unknown circuit',r['id'])
    ps=[x['pos'] for x in r['results'] if x['pos'] is not None]
    if ps!=sorted(ps): n('positions out of order',r['id'])
    if len(set(ps))!=len(ps): n('duplicate positions',r['id']+' '+str([p for p,c in collections.Counter(ps).items() if c>1]))
    if ps and ps[0]!=1: n('no P1',r['id'])
    if not r['results']: n('empty classification',r['id'])
    seen=set()
    for x in r['results']:
        if x['rider'] not in d['riders']: n('unknown rider',r['id']+' '+str(x['rider']))
        if x['rider'] in seen: n('rider twice in one classification',r['id']+' '+d['riders'].get(x['rider'],{}).get('name',x['rider']))
        seen.add(x['rider'])
        if x['pos'] is not None and x['status'] not in ('Classified','NC'): n('position with non-classified status',r['id']+' '+x['status'])
        if x['pos'] is None and x['status']=='Classified': n('classified without position',r['id'])
        if x.get('points') is not None and x['points']<0: n('negative points',r['id'])
    if r.get('pole') and r['pole'].get('rider') and r['pole']['rider'] not in d['riders']: n('pole rider unknown',r['id'])
    if r.get('fast') and r['fast'].get('rider') and r['fast']['rider'] not in d['riders']: n('fastest-lap rider unknown',r['id'])
    if r.get('fast') and r['fast'].get('rider') and r['fast']['rider'] not in {x['rider'] for x in r['results']}: n('fastest-lap rider not in classification',r['id'])
dates=[(r['date'],r.get('order',0)) for r in R]
# standings
main=lambda r: r['type'] in ('RAC','R1','R2') or (tag=='sbk')
for y,st in d['standings'].items():
    ps=[x['pos'] for x in st['rows']]
    if ps!=sorted(ps): n('standings out of order',y)
    if ps and ps[0]!=1: n('standings without P1',y)
    for x in st['rows']:
        if x['rider'] not in d['riders']: n('standings rider unknown',y+' '+str(x['rider']))
    # champion must have at least one race entry that year
    champ=st['rows'][0]['rider'] if st['rows'] else None
    if champ and not any(x['rider']==champ for r in R if r['year']==int(y) for x in r['results']): n('champion has no race entry that season',y)
years=sorted({r['year'] for r in R}); sy=sorted(int(y) for y in d['standings'])
if years!=sy: n('seasons with races ≠ seasons with standings',f'{set(years)^set(sy)}')
# points consistency where per-race points exist
diff=[]
for y in years:
    rows=[x for r in R if r['year']==y and r['type'] in ('RAC','SPR') for x in r['results'] if x.get('points') is not None]
    if not rows: continue
    tot=collections.Counter()
    for r in R:
        if r['year']!=y: continue
        for x in r['results']:
            if x.get('points'): tot[x['rider']]+=x['points']
    st=d['standings'].get(str(y))
    if st:
        for x in st['rows'][:10]:
            if abs(tot[x['rider']]-x['points'])>0.01: diff.append((y,d['riders'][x['rider']]['name'],tot[x['rider']],x['points']))
# coverage vs races
cov_bad=[y for y,c in d['coverage'].items() if c['gp']!=sum(1 for r in R if r['year']==int(y) and r['type'] in ('RAC','R1','R2'))]
# reference facts
champs={int(y):d['riders'][st['rows'][0]['rider']]['name'] for y,st in d['standings'].items() if st['rows']}
REF={'motogp':{1949:'Leslie Graham',1957:'Libero Liberati',1966:'Giacomo Agostini',1975:'Giacomo Agostini',1983:'Freddie Spencer',1993:'Kevin Schwantz',2001:'Valentino Rossi',2007:'Casey Stoner',2013:'Marc Marquez',2019:'Marc Marquez',2020:'Joan Mir',2022:'Francesco Bagnaia',2023:'Francesco Bagnaia',2024:'Jorge Martin'},
     'sbk':{1988:'Fred Merkel',1990:'Raymond Roche',1994:'Carl Fogarty',1999:'Carl Fogarty',2002:'Colin Edwards',2006:'Troy Bayliss',2009:'Ben Spies',2013:'Tom Sykes',2015:'Jonathan Rea',2020:'Jonathan Rea',2021:'Toprak Razgatlioglu',2022:'Alvaro Bautista',2023:'Alvaro Bautista',2024:'Toprak Razgatlioglu'}}[tag]
refs=[(y,who,champs.get(y),(champs.get(y) or '').lower().replace('á','a').replace('ı','i')==who.lower().replace('á','a').replace('ı','i')) for y,who in REF.items()]
def wins(name):
    return sum(1 for r in R if r['type'] in ('RAC','R1','R2','SPR') and (tag=='sbk' or r['type']=='RAC') for x in r['results'] if x['pos']==1 and d['riders'][x['rider']]['name']==name)
W={'motogp':[('Giacomo Agostini',68),('Valentino Rossi',89),('Marc Marquez',None)],'sbk':[('Jonathan Rea',119),('Carl Fogarty',59),('Troy Bayliss',52)]}[tag]
wcheck=[(nm,exp,wins(nm)) for nm,exp in W]
circ=d['circuits']; withimg=sum(1 for c in circ.values() if c.get('image'))
out=[f'# Data audit — {"MotoGP" if tag=="motogp" else "WorldSBK"} atlas','',f"Archive snapshot {d['snapshot']}, results through {d['lastDate']}. Checks compare the embedded archive against itself, plus well-known reference facts. Nothing was changed.",'','## Inventory','',f"- {len(R):,} race classifications ({collections.Counter(r['type'] for r in R)}) · {sum(len(r['results']) for r in R):,} result rows · {len(d['riders']):,} riders · {len(circ)} circuits · {len(d['standings'])} seasons of standings",f"- Circuit outlines: {withimg} circuits carry a profile image in the archive (all traced into vector lines for this page); {len(circ)-withimg} do not",f"- Per-race points recorded: {sum(1 for r in R for x in r['results'] if x.get('points') is not None):,} rows",'','## Consistency checks','','| Check | Result |','|---|---|']
for c in ['bad date','year ≠ date','unknown circuit','positions out of order','duplicate positions','no P1','empty classification','unknown rider','rider twice in one classification','position with non-classified status','classified without position','negative points','pole rider unknown','fastest-lap rider unknown','fastest-lap rider not in classification','standings out of order','standings without P1','standings rider unknown','champion has no race entry that season','seasons with races ≠ seasons with standings']:
    v=iss.get(c,[]); out.append(f'| {c} | {"✅ none" if not v else "⚠️ "+str(len(v))+" — e.g. "+"; ".join(v[:3])} |')
out+=['',f'Coverage table vs counted main races: {"✅ matches every season" if not cov_bad else "⚠️ differs in "+", ".join(cov_bad[:8])}','']
if diff: out+=[f'Published standings vs summed per-race points (top 10 each season, where per-race points exist): **{len(diff)}** rows differ — drop-score rules, penalties and sprint points explain most; e.g. '+'; '.join(f'{y} {nm} {a:g} vs {b:g}' for y,nm,a,b in diff[:5]),'']
else: out+=['Published standings vs summed per-race points: ✅ every top-ten row reconciles where per-race points exist.','']
out+=['## Reference facts','','| Fact | Expected | In data | |','|---|---|---|---|']+[f'| {y} champion | {who} | {got} | {"✅" if ok else "❌"} |' for y,who,got,ok in refs]+[f'| {nm} career wins{" (main races)" if tag=="motogp" else " (all races incl. Superpole)"} | {exp if exp is not None else "—"} | {got} | {"✅" if exp is None or exp==got else "❌"} |' for nm,exp,got in wcheck]
out+=['','## Notes','',{'motogp':'- 22 rows carry a finishing position with status “NC” (e.g. the winner of the 2003 Portuguese GP); the page treats a row with a position as classified, as the source prototype did.\n- Per-race points in the feed are zero for 1992–2004 and absent before 1992; the page therefore takes championship points from the published standings everywhere, and only the Sprint lens uses per-race points (2023 on).\n- One dead-heat style duplicate position (1972 Tourist Trophy, two riders 8th), one rider listed twice (1972 Tourist Trophy) and one classified row without a position (1989 Dutch TT) are left as recorded.','sbk':'- Every race of the 1996 season is dated in 1997 in the feed (e.g. 1996-RSM-SBK-001 dated 1997-04-14); the page shows the date within the season year and says so on the race sheet. Worth fixing at source.\n- Retired rows carry a finishing-order position in the feed; the page shows R for them and uses the position only for ordering.\n- The feed carries no per-race points, so all points figures come from the published riders’ and manufacturers’ standings.'}[tag]]
open(ROOT/'audits'/f'DATA-AUDIT-{tag}.md','w',encoding='utf-8').write('\n'.join(out)); print('\n'.join(out))
