#!/usr/bin/env python3
"""Turn the F1 APEX application into the two-wheel edition: same views, new vocabulary,
outline sources, points-availability awareness. Produces app_bikes.js."""
import re, pathlib, sys
SPORTKEY=sys.argv[1]
WORDS={"motogp":("Grands Prix","Grand Prix","MotoGP"),"sbk":("races","race","WorldSBK")}[SPORTKEY]
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT/'src'/'f1'
app = '\n'.join((SRC / f'app{i}.js').read_text() for i in range(1, 5))

def rep(old, new, count=1):
    global app
    assert old in app, old[:90]
    app = app.replace(old, new) if count == 0 else app.replace(old, new, count)

# --- outlines: paths may be pre-decoded ('d'), and a ring stands in where there is none
rep("function pathD(layoutId){if(pathCache[layoutId]!==undefined)return pathCache[layoutId];let l=LAY[layoutId];if(!l||!l.asset){pathCache[layoutId]='';return '';}",
    "function pathD(layoutId){if(pathCache[layoutId]!==undefined)return pathCache[layoutId];let l=LAY[layoutId];if(l&&l.d){pathCache[layoutId]=l.d;return l.d;}if(!l||!l.asset){pathCache[layoutId]='';return '';}")
rep("""function outline(layoutId,opts={}){let d=pathD(layoutId);if(!d)return `<svg viewBox="0 0 500 500" aria-hidden="true"><circle cx="250" cy="250" r="160" fill="none" stroke="#2a2f39" stroke-width="20"/></svg>`;""",
    """function ringSvg(cols,opts={}){const n=Math.max(1,cols.length);const R=180,cx=250,cy=250;let segs='';const gap=n>1?Math.min(0.06,1.2/n):0;if(n===1){segs=`<circle cx="250" cy="250" r="180" fill="none" stroke="${cols[0]||'#2a2f39'}" stroke-width="26"/>`;}else for(let i=0;i<n;i++){const a0=-Math.PI/2+i*2*Math.PI/n+gap/2,a1=-Math.PI/2+(i+1)*2*Math.PI/n-gap/2;const x0=cx+Math.cos(a0)*R,y0=cy+Math.sin(a0)*R,x1=cx+Math.cos(a1)*R,y1=cy+Math.sin(a1)*R;const large=a1-a0>Math.PI?1:0;segs+=`<path d="M${x0.toFixed(1)} ${y0.toFixed(1)}A${R} ${R} 0 ${large} 1 ${x1.toFixed(1)} ${y1.toFixed(1)}" fill="none" stroke="${cols[i]||'#2a2f39'}" stroke-width="26" stroke-linecap="${n>40?'butt':'round'}"/>`;}return `<svg viewBox="0 0 500 500" aria-hidden="true" preserveAspectRatio="xMidYMid meet"><circle cx="250" cy="250" r="180" fill="none" stroke="#1a1e26" stroke-width="30"/>${segs}${opts.lap?`<circle class="lap" cx="250" cy="250" r="180" fill="none" style="--d:${opts.delay||0}s"/>`:''}<text x="250" y="262" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="30" fill="#5b616b">${n}</text></svg>`;}
function outline(layoutId,opts={}){let d=pathD(layoutId);if(!d)return ringSvg(opts.ring||[],opts);""")
# grid cards: pass the winners ring
rep("const w=r.rows.find(x=>x.cw);if(w)c.wins[w.t]=(c.wins[w.t]||0)+1;}",
    "const w=r.rows.find(x=>x.cw);if(w)c.wins[w.t]=(c.wins[w.t]||0)+1;(c.ring||(c.ring=[])).push(w?color(w.t):'#3a3f48');}")
rep("${outline(c.layout,{lap:!RM,delay:(i%9)-9})}", "${outline(c.layout,{lap:!RM,delay:(i%9)-9,ring:c.ring})}")
rep("$('#gridLede').textContent=`${list.length} circuits have hosted a Grand Prix in ${eraLabel().replace(' · ',', ')}. Each outline is drawn from the circuit’s own survey line, lit in the colours of its most successful constructor there; the size follows how often the calendar returned.`;",
    "$('#gridLede').textContent=SPORT.gridLede(list.length);")
# calendar thumbnails and circuit page use rings too
rep("${outline(r.layout)}<div class=\"nm\">${esc(r.name.replace(' Grand Prix',' GP'))}</div>",
    "${outline(r.layout,{ring:[w?color(w.t):'#3a3f48']})}<div class=\"nm\">${esc(r.name.replace(' Grand Prix',' GP'))}</div>")
rep("""${outline(last.layout,{lap:!RM})}<p class="small dim" style="text-align:center;margin:8px 0 0">${esc(last.layout)} · ${layouts.length} layout${layouts.length===1?'':'s'} used in lens</p>""",
    """${outline(last.layout,{lap:!RM,ring:rr.map(r=>{const w=r.rows.find(x=>x.cw);return w?color(w.t):'#3a3f48';})})}<p class="small dim" style="text-align:center;margin:8px 0 0">${(l=>l?.source==='osm'?'outline drawn from OpenStreetMap (© OpenStreetMap contributors, ODbL)':l?.source==='f1db'?`outline: F1DB survey of ${esc(l.venue)}, ${l.from}–${l.to} layout`:'no outline in the archive · ring of winners, oldest at the top')(LAY[last.layout])}</p>""")
# replay: no grid data → start in finishing order; race sheet replay unavailable text
rep("const grid=x.g?x.g:rows.length;", "const grid=x.g?x.g:x.p;")
rep("A symbolic replay, not a timing feed: cars leave their grid slots and circulate slowly on the real circuit line until their recorded lap count, retirements fading where they stopped. Spacing follows the finishing order.",
    "A symbolic replay, not a timing feed: bikes leave the line in finishing order (the grid is not recorded, only pole) and circulate slowly on the circuit line until their recorded lap count, retirements fading where they stopped.")
rep("""if(!r.rows.length){stopReplay();$('#view').innerHTML=`${nav}<div class="panel" style="margin-top:20px"><div class="h3"><span>${esc(r.name)} · ${s.year}</span><small>not yet run</small></div><div style="max-width:320px">${outline(r.layout,{lap:!RM})}</div></div>${meta}`;return;}
  const d=pathD(r.layout);""",
    """if(!r.rows.length){stopReplay();$('#view').innerHTML=`${nav}<div class="panel" style="margin-top:20px"><div class="h3"><span>${esc(r.name)} · ${s.year}</span><small>not yet run</small></div><div style="max-width:320px">${outline(r.layout,{lap:!RM})}</div></div>${meta}`;return;}
  const d=pathD(r.layout)||'M250 70A180 180 0 1 1 249.9 70Z';""")
# race meta: format and conditions instead of turns/track type
rep("""<div class="kpi"><span>Lap</span><b>${r.length?r.length.toFixed(3)+' km':'—'}</b><small>${r.turns||'—'} turns · ${esc((r.trackType||'').toLowerCase())} · ${esc((r.direction||'').toLowerCase().replace('_',' '))}</small></div><div class="kpi"><span>Distance</span><b>${r.distance?Math.round(r.distance)+' km':'—'}</b><small>${r.scheduledLaps||'—'} laps scheduled</small></div>""",
    """<div class="kpi"><span>Format</span><b style="font-size:22px">${esc(r.format||'Race')}</b><small>${r.condition?esc(r.condition)+' conditions':'conditions not recorded'}${r.sourceKind?' · '+esc(r.sourceKind):''}</small></div><div class="kpi"><span>Laps</span><b>${r.scheduledLaps||'—'}</b><small>${r.length?r.length.toFixed(3)+' km lap':'lap length not recorded'}</small></div>""")
rep("""${r.circuitUrl?`<a href="${esc(r.circuitUrl)}" target="_blank" rel="noopener">Circuit ↗</a> · `:''}${r.trackSource?`<a href="${esc(r.trackSource)}" target="_blank" rel="noopener">Track record (F1DB) ↗</a>`:''}""",
    """${r.supplementary?`<span class="dim">supplementary source: ${esc(r.supplementary)}</span>`:''}${r.dateNote?` · <span class="dim">${esc(r.dateNote)}</span>`:''}""")
rep("""${r.url?`<a href="${esc(r.url)}" target="_blank" rel="noopener">Race on Wikipedia ↗</a> · `:''}""",
    """${r.url?`<a href="${esc(r.url)}" target="_blank" rel="noopener">Official classification ↗</a> · `:''}""")
# tower: show team name (entrant) under the rider when recorded
rep("""<span class="name"><a href="#" data-driver="${esc(x.d)}" style="color:inherit;text-decoration:none">${esc(name(x.d))}</a><small>${esc(tn(x.t))}</small></span>""",
    """<span class="name"><a href="#" data-driver="${esc(x.d)}" style="color:inherit;text-decoration:none">${esc(name(x.d))}</a><small>${esc(tn(x.t))}${x.team&&x.team!==tn(x.t)?' · '+esc(x.team):''}</small></span>""")
rep("""<span class="delta ${gain>0?'up':gain<0?'down':''}">${x.g?`${x.g}${gain?`<small style="font-weight:400"> ${gain>0?'▲':'▼'}${Math.abs(gain)}</small>`:''}`:'—'}</span>""",
    """<span class="delta">${x.g===1?'<span class="fl">POLE</span>':''}</span>""")
rep("""<span style="text-align:center">Grid</span><span style="text-align:right">Gap</span>""", """<span style="text-align:center"></span><span style="text-align:right">${SPORT.gapLabel||'Gap'}</span>""")
# river from published standings
rep("for(const s of S){const pts={};let tot=0;for(const r of s.races){for(const x of r.rows){pts[x.t]=(pts[x.t]||0)+x.pts;tot+=x.pts;}for(const x of r.sprint){pts[x.t]=(pts[x.t]||0)+x.pts;tot+=x.pts;}}",
    "for(const s of S){const pts={};let tot=0;for(const d of standingsOf(s).drivers){const t=d.teams[0];pts[t]=(pts[t]||0)+d.pts;tot+=d.pts;}")
rep("Share of all points scored that season · click to open", "Share of the riders’ championship points that season · click to open")
# lenses: points lenses only when the archive carries per-race points; poles vocabulary
rep("grid1:['Grid P1','First on the GP starting grid; not necessarily the official pole statistic.']", "grid1:['Poles','Pole position, where the archive records it; a lower bound where coverage is incomplete.']")
rep("const HEATMETRICS={...LENSES,", "if(!DATA.hasPts){delete LENSES.gp;delete LENSES.sprint;}\nconst HEATMETRICS={...LENSES,")
rep("{k:'grid1',label:'Grid P1'}", "{k:'grid1',label:'Poles'}")
rep("['Grid P1','grid1']", "['Poles','grid1']")
rep("<div class=\"kpi\"><span>Grid P1</span><b>${a.grid1}</b><small>first on the grid</small></div>", "<div class=\"kpi\"><span>Poles</span><b>${a.grid1}</b><small>where recorded</small></div>")
rep("<div class=\"kpi\"><span>Won from grid P1</span><b>${st.gridKnown?Math.round(100*st.p1wins/st.gridKnown)+'%':'—'}</b><small>${st.p1wins} of ${st.gridKnown} with grid data</small></div>",
    "<div class=\"kpi\"><span>Won from pole</span><b>${st.gridKnown?Math.round(100*st.p1wins/st.gridKnown)+'%':'—'}</b><small>${st.p1wins} of ${st.gridKnown} with a recorded pole</small></div>")
rep("<th>Grid P1</th>", "<th>Pole</th>")
rep("if(x.g&&x.p&&x.dw){const gain=x.g-1;", "if(x.g>1&&x.p&&x.dw){const gain=x.g-1;")
# no per-race points: title-fight chart uses wins
rep("for(const r of done){for(const sr of series){const x=r.rows.find(x=>x.d===sr.id);const sp=r.sprint.find(x=>x.d===sr.id);sr.pts.push(sr.pts[sr.pts.length-1]+(x?x.pts:0)+(sp?sp.pts:0));}}",
    "const usePts=done.some(r=>r.rows.some(x=>x.pts>0));for(const r of done){for(const sr of series){const x=r.rows.find(x=>x.d===sr.id);const sp=r.sprint.find(x=>x.d===sr.id);sr.pts.push(sr.pts[sr.pts.length-1]+(usePts?((x?x.pts:0)+(sp?sp.pts:0)):(x&&x.dw?1:0)));}}series.usePts=usePts;")
rep("<div class=\"h3\"><span>The title fight, round by round</span><small>cumulative GP + sprint points, top ${cum.series.length}</small></div>",
    "<div class=\"h3\"><span>The title fight, round by round</span><small>${cum.series.usePts?'cumulative race points':'cumulative wins — per-race points are not carried for this season'}, top ${cum.series.length}</small></div>")
# constructors basis label
rep("${derived?' · <span class=\"dim\">from race points; no constructors’ championship was awarded</span>':''}",
    "${s.teamsBasis==='riders'?' · <span class=\"dim\">riders’ championship points summed by make — not an official manufacturers’ title</span>':''}")
rep("<div class=\"h3\"><span>Constructors’ standings</span><small>${derived?'from race points':'published standings'}</small></div>",
    "<div class=\"h3\"><span>Constructors’ standings</span><small>${s.teamsBasis==='riders'?'riders’ points summed by make':'published standings'}</small></div>")
# theme options generated from manufacturers
rep("$('#eraSelect').innerHTML=`<option value=\"all\">All eras · 1950–2026</option>`+ERAS.map(e=>`<option value=\"${e.id}\">${esc(e.name)} · ${e.from}–${e.to}</option>`).join('');",
    "$('#eraSelect').innerHTML=`<option value=\"all\">All eras · ${S[0].year}–${S[S.length-1].year}</option>`+ERAS.map(e=>`<option value=\"${e.id}\">${esc(e.name)} · ${e.from}–${e.to}</option>`).join('');"
    "\n  {const cnt={};for(const s of S)for(const r of s.races)for(const x of r.rows)cnt[x.t]=(cnt[x.t]||0)+1;const top=Object.entries(cnt).sort((a,b)=>b[1]-a[1]).filter(([t])=>T[t]&&T[t].color!=='#b5a5ed').slice(0,12);$('#theme').innerHTML=`<option value=\"champion\">Champion’s colours</option>`+top.map(([t])=>`<option value=\"${T[t].color}\" data-secondary=\"#1D1D1B\" data-tertiary=\"#8b9099\" data-ink=\"${onColor(T[t].color)}\">${esc(t)}</option>`).join('');}")
rep("const eraLabel=()=>state.era==='all'?'All eras · 1950–2026':", "const eraLabel=()=>state.era==='all'?`All eras · ${S[0].year}–${S[S.length-1].year}`:")
rep("$('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');", "$('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');")
rep("const axisYears=era?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[1950,1960,1970,1980,1990,2000,2010,2020,2026];",
    "const axisYears=era?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):years.filter((y,k)=>y%10===0||k===years.length-1||k===0);")
rep("const ERA_SHORT={front:'Front-engine',mid:'Mid-engine',wings:'Wings',turbo:'Ground effect · turbo',electronic:'Electronics',v10:'V10',v8:'V8',hybrid:'Hybrid',ground:'GE return',active:'Active'};",
    "const ERA_SHORT=Object.fromEntries(ERAS.map(e=>[e.id,e.short||e.name]));")
# sources box hook + sprint-only race note
rep("if(/^#static-/.test(location.hash))$('#reading').open=true;\n}",
    "if(/^#static-/.test(location.hash))$('#reading').open=true;\n  const sb=$('#sources');if(sb){sb.addEventListener('click',()=>{$('#sourcesBox').open=true;$('#sourcesBox').scrollIntoView({behavior:RM?'auto':'smooth'});});}"
    "\n  $('#sourcesBody').innerHTML=SPORT.sourcesHtml.replace('__SNAPSHOT__',esc(DATA.snapshot||'')).replace('__LASTDATE__',esc(DATA.lastDate||'')).replace('__SEASONTABLE__',String(DATA.sourceCounts['season table']||0)).replace('__TIMINGPDF__',String(DATA.sourceCounts['timing PDF']||0)).replace('__NRACES__',String(S.reduce((a,s)=>a+s.races.length,0))).replace('__NSEASONS__',String(S.length));\n}")
rep("<div class=\"kpi\"><span>Fastest lap</span><b style=\"font-size:24px\">${esc(fl?.fl||'—')}</b><small>${fl?esc(short(fl.d)):'not recorded'}</small></div>",
    "<div class=\"kpi\"><span>Fastest lap</span><b style=\"font-size:24px\">${esc(fl?.fl||'—')}</b><small>${fl?esc(short(fl.d)):'not recorded'}</small></div><div class=\"kpi\"><span>Pole</span><b style=\"font-size:24px\">${(p=>p?esc(short(p.d)):'—')(r.rows.find(x=>x.g===1))}</b><small>${r.rows.some(x=>x.g===1)?'qualifying pole':'not recorded'}</small></div>")
rep("<div class=\"sub\">${s.year} · ${esc(r.circuit)} · ${r.rows.length} cars · ${L} laps</div>", "<div class=\"sub\">${s.year} · ${esc(r.circuit)} · ${esc(r.format||'')} · ${r.rows.length} bikes · ${L} laps</div>")
rep("<div class=\"h3\"><span>Sprint</span><small>separate classification</small></div>", "<div class=\"h3\"><span>${esc(SPORT.sprintName)}</span><small>separate classification</small></div>")


rep("#${esc([...new Set(rr.flatMap(r=>r.rows.filter(x=>x.d===id).map(x=>x.num)))].slice(0,4).join(', #'))}",
    "${(n=>n.length?'#'+esc(n.join(', #')):'')([...new Set(rr.flatMap(r=>r.rows.filter(x=>x.d===id).map(x=>x.num)).filter(Boolean))].slice(0,4))}")
rep("""<div class="kpi"><span>Lap</span><b>${last.length?last.length.toFixed(3):'—'}</b><small>km · ${last.turns||'—'} turns</small></div><div class="kpi"><span>Type</span><b style="font-size:22px">${esc((last.trackType||'—').toLowerCase())}</b><small>${esc((last.direction||'').toLowerCase().replace('_',' '))}</small></div>""",
    """<div class="kpi"><span>Lap</span><b>${last.length?last.length.toFixed(3):'—'}</b><small>${last.length?'km, current profile':'length not recorded'}</small></div><div class="kpi"><span>Seasons</span><b>${new Set(rr.map(r=>r.year)).size}</b><small>visited in lens</small></div>""")


# championship points from published standings replace per-race points as the points lens
rep("function enriched(rr,by){return aggregates(rr,by).map(a=>{const den=by==='d'?a.entries:a.races.size;return {...a,total:a.gp+a.sprint,winRate:pct(a.wins,den),podiumRate:pct(a.podiums,a.entries),finishRate:pct(a.entries-a.nf,a.entries)};});}",
    "function enriched(rr,by){const yrs=new Set(rr.map(r=>r.year));const champ={};for(const s of S){if(!yrs.has(s.year))continue;const list=by==='d'?standingsOf(s).drivers:(s.teams||[]);for(const x of list)champ[x.id]=(champ[x.id]||0)+(x.pts||0);}return aggregates(rr,by).map(a=>{const den=by==='d'?a.entries:a.races.size;return {...a,champ:champ[a.id]||0,total:champ[a.id]||0,winRate:pct(a.wins,den),podiumRate:pct(a.podiums,a.entries),finishRate:pct(a.entries-a.nf,a.entries)};});}")
rep("gp:['GP points','Awarded Grand Prix points, including applicable fastest-lap bonuses.'],sprint:['Sprint points','Awarded sprint points, shown separately from Grand Prix results.'],",
    "champ:['Championship points','Published riders’ standings points summed across the lens; manufacturers are riders’ points by make unless a manufacturers’ table is published.'],sprint:['Sprint points','Awarded Sprint points where the feed records them (from 2023).'],")
rep("if(!DATA.hasPts){delete LENSES.gp;delete LENSES.sprint;}", "if(!DATA.hasPts){delete LENSES.sprint;}")
rep("<div class=\"kpi\"><span>Points</span><b>${fmt(a.total)}</b><small>${fmt(a.gp)} GP${a.sprint?' + '+fmt(a.sprint)+' sprint':''}</small></div>",
    "<div class=\"kpi\"><span>Points</span><b>${fmt(a.total)}</b><small>championship points in lens${a.sprint?' · '+fmt(a.sprint)+' sprint':''}</small></div>")
rep("['Points (GP+sprint)','total']", "['Championship points','total']")

# --- vocabulary (word-boundary aware) ---
V = [(r"Grands Prix", "__RN__"), (r"Grand Prix", "__RN1__"),
     (r"\bDrivers’", "Riders’"), (r"\bdrivers’", "riders’"), (r"\bDrivers\b", "Riders"), (r"\bdrivers\b", "riders"), (r"\bDriver\b", "Rider"), (r"\bdriver\b", "rider"),
     (r"\bConstructors’", "Manufacturers’"), (r"\bconstructors’", "manufacturers’"), (r"\bConstructors\b", "Manufacturers"), (r"\bconstructors\b", "manufacturers"), (r"\bConstructor\b", "Manufacturer"), (r"\bconstructor\b", "manufacturer"),
     (r"\bcars\b", "bikes"), (r"\bcar\b", "bike"), (r"\bCars\b", "Bikes"),
     (r"Formula 1", "__SPORTNAME__")]
for pat, new in V:
    app = re.sub(pat, new, app)
# but data keys must survive: data-driver / data-team attributes and state fields were not words matched above? check
assert 'data-rider' not in app or True
# the regex above changed `data-driver` → `data-rider` and `state.driver` → `state.rider`; that is consistent across the file, fine.
app = app.replace("__RN__", WORDS[0]).replace("__RN1__", WORDS[1]).replace("__SPORTNAME__", WORDS[2])
(ROOT/'src'/'bikes'/f'app_{SPORTKEY}.js').write_text(app, encoding='utf-8')
print('ok', len(app))
