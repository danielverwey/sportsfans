'use strict';
/* ============================================================
   APEX — an ode to Formula 1. Application.
   Everything below reads from DATA; nothing writes to it.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const D=DATA.drivers, T=DATA.teams, S=DATA.seasons, ERAS=DATA.eras, CIRC=DATA.circuits, LAY=DATA.layouts;
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number.isInteger(n)?String(n):(Math.round(n*100)/100).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const name=id=>D[id]?.name||id, short=id=>D[id]?.short||id, code=id=>D[id]?.code||String(id).slice(0,3).toUpperCase();
const tn=id=>T[id]?.name||id;
/* Teams the source leaves on its placeholder lavender get a deterministic muted hue of their own, so the 1950s are not one purple blur. Presentation only: DATA is untouched. */
const hueCache={};const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};
const color=id=>{const c=T[id]?.color;if(c&&c.toLowerCase()!=='#b5a5ed')return c;if(hueCache[id])return hueCache[id];let h=0;for(const ch of String(id))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[id]=hsl2hex(h%360,38,58);};
const finished=x=>x.status==='Finished'||/^\+\d+ Lap/.test(x.status);
const lapSeconds=t=>{if(!t)return null;let v=t.replace(/^\+/,'').split(':').map(Number);if(v.some(n=>!Number.isFinite(n)))return null;return v.reduce((a,n)=>a*60+n,0);};
const fmtLap=s=>{if(s==null)return '—';let m=Math.floor(s/60),r=s-m*60;return (m?m+':':'')+(m?r.toFixed(3).padStart(6,'0'):r.toFixed(3));};
const byYear=Object.fromEntries(S.map(s=>[s.year,s]));
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to);
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const teamVar=id=>`--team:${color(id)}`;
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};

/* ---------- state ---------- */
const state={era:'all',year:S[S.length-1].year,tab:'season',race:1,driver:null,team:null,circuit:null,lens:'wins',heat:'wins',heatBy:'d',duelBy:'d',dA:null,dB:null,gridSort:'count',gridFind:'',focusTeam:null,whole:false};
const eraSeasons=()=>S.filter(s=>state.era==='all'||(s.year>=ERAS.find(e=>e.id===state.era).from&&s.year<=ERAS.find(e=>e.id===state.era).to));
const eraRaces=()=>eraSeasons().flatMap(s=>s.races.filter(r=>r.rows.length).map(r=>({...r,year:s.year})));
const eraLabel=()=>state.era==='all'?'All eras · 1950–2026':(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era));

/* ---------- standings, ordered (the source lists 1952 and 1953 without a published table) ---------- */
const stCache={};const isNum=p=>/^\d+$/.test(String(p));
function standingsOf(s){if(stCache[s.year])return stCache[s.year];let dr,derived=false;if(s.drivers.some(x=>isNum(x.p))){dr=[...s.drivers].sort((a,b)=>(isNum(a.p)?+a.p:1e9)-(isNum(b.p)?+b.p:1e9)||b.pts-a.pts);}else{derived=true;const m={};for(const r of s.races){for(const x of r.rows.concat(r.sprint)){let a=m[x.d]||(m[x.d]={id:x.d,pts:0,wins:0,teams:[]});a.pts+=x.pts;if(!a.teams.includes(x.t))a.teams.push(x.t);}for(const x of r.rows)if(x.dw&&m[x.d])m[x.d].wins++;}dr=Object.values(m).sort((a,b)=>b.pts-a.pts||b.wins-a.wins).map((x,i)=>({...x,p:String(i+1)}));}return stCache[s.year]={drivers:dr,derived};}

/* ---------- circuit outlines (decoded once, drawn many times) ---------- */
const pathCache={};
function pathD(layoutId){if(pathCache[layoutId]!==undefined)return pathCache[layoutId];let l=LAY[layoutId];if(!l||!l.asset){pathCache[layoutId]='';return '';}try{let svg=atob(l.asset.slice(l.asset.indexOf(',')+1));let m=/ d="([^"]+)"/.exec(svg);pathCache[layoutId]=m?m[1]:'';}catch(e){pathCache[layoutId]='';}return pathCache[layoutId];}
function outline(layoutId,opts={}){let d=pathD(layoutId);if(!d)return `<svg viewBox="0 0 500 500" aria-hidden="true"><circle cx="250" cy="250" r="160" fill="none" stroke="#2a2f39" stroke-width="20"/></svg>`;let lap=opts.lap?`<path class="lap" d="${d}" style="--d:${opts.delay||0}s"/>`:'';return `<svg viewBox="0 0 500 500" aria-hidden="true" preserveAspectRatio="xMidYMid meet"><path class="base" d="${d}"/><path class="glow" d="${d}"/><path class="line" d="${d}"/>${lap}</svg>`;}
function latestLayout(cid){let best=null;for(const s of S)for(const r of s.races)if(r.cid===cid&&r.layout)best=r.layout;return best||CIRC[cid]?.layouts?.slice(-1)[0];}

/* ---------- aggregates (same semantics as the prototype) ---------- */
function aggregates(rr,by='d'){const map={};const k=by==='d'?'d':'c';for(const r of rr){for(const x of r.rows){let a=map[x[by]]||(map[x[by]]={id:x[by],wins:0,podiums:0,gp:0,sprint:0,entries:0,fl:0,grid1:0,nf:0,teams:new Set(),drivers:new Set(),races:new Set(),seasons:new Set(),first:r.year,last:r.year});a.entries+=x[k+'e'];a.races.add(r.year+'-'+r.round);a.seasons.add(r.year);a.gp+=x.pts;a.wins+=x[k+'w'];a.podiums+=x[k+'p'];a.fl+=x[k+'f'];a.grid1+=x[k+'g'];a.nf+=x[k+'n'];a.teams.add(x.t);a.drivers.add(x.d);a.first=Math.min(a.first,r.year);a.last=Math.max(a.last,r.year);}for(const x of r.sprint){if(map[x[by]])map[x[by]].sprint+=x.pts;}}return Object.values(map);}
function enriched(rr,by){return aggregates(rr,by).map(a=>{const den=by==='d'?a.entries:a.races.size;return {...a,total:a.gp+a.sprint,winRate:pct(a.wins,den),podiumRate:pct(a.podiums,a.entries),finishRate:pct(a.entries-a.nf,a.entries)};});}
const LENSES={wins:['GP wins','Total Grand Prix victories. Sprints excluded.'],podiums:['GP podiums','Top-three Grand Prix classifications. Sprints excluded.'],fl:['Fastest laps','Rank-1 race laps, whether or not a bonus point was awarded.'],grid1:['Grid P1','First on the GP starting grid; not necessarily the official pole statistic.'],gp:['GP points','Awarded Grand Prix points, including applicable fastest-lap bonuses.'],sprint:['Sprint points','Awarded sprint points, shown separately from Grand Prix results.'],winRate:['Win rate %','GP wins divided by Grands Prix entered. Constructor denominator is race weekends, not car entries.'],podiumRate:['Podium rate %','Podium finishes divided by GP entries. Constructor denominator is individual car entries.'],finishRate:['Finish-status rate %','Finished or +N Lap(s), divided by GP entries. Other statuses include retirements, disqualifications and non-starts.']};
const HEATMETRICS={...LENSES,champPoints:['Championship points','Published season standings, including championship penalties and adjustments.'],entries:['GP car entries','Driver result entries or constructor car entries, including non-starts and non-qualifications.'],nf:['Non-finish statuses','Retirements, disqualifications and non-starts; higher values indicate more non-finish statuses.']};

/* ---------- theme ---------- */
function champTeam(season){let d=standingsOf(season).drivers[0];return d?.teams?.[0]||season.teams?.[0]?.id||null;}
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;if(v==='champion'){let t=state.whole?(enriched(eraRaces(),'t').sort((a,b)=>b.total-a.total)[0]?.id):champTeam(byYear[state.year]);acc=t?color(t):'#FF8000';sec='#1D1D1B';ter='#8b9099';ink=onColor(acc);sel.options[0].textContent=`Champion’s colours · ${t?tn(t):'—'}`;}else{let o=sel.selectedOptions[0];acc=v;sec=o.dataset.secondary;ter=o.dataset.tertiary;ink=o.dataset.ink;}root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- lights out ---------- */
function lightsOut(){const box=$('#lights'),row=$('#lightRow');let seen=false;try{seen=sessionStorage.getItem('apex-lights')==='1';}catch(e){}
  const out=()=>{box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-lights','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  row.innerHTML=Array.from({length:5},()=>`<div class="col"><span class="bulb"></span><span class="bulb"></span><span class="bulb live"></span><span class="bulb live"></span></div>`).join('');
  const cols=$$('#lightRow .col');let i=0;const step=()=>{if(!box.isConnected)return;if(i<5){cols[i++].classList.add('on');setTimeout(step,640);}else setTimeout(()=>{cols.forEach(c=>c.classList.remove('on'));setTimeout(out,180);},700+Math.random()*1400);};
  setTimeout(step,500);$('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;const ERA_SHORT={front:'Front-engine',mid:'Mid-engine',wings:'Wings',turbo:'Ground effect · turbo',electronic:'Electronics',v10:'V10',v8:'V8',hybrid:'Hybrid',ground:'GE return',active:'Active'};
function buildRiver(){
  const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const pts={};let tot=0;for(const r of s.races){for(const x of r.rows){pts[x.t]=(pts[x.t]||0)+x.pts;tot+=x.pts;}for(const x of r.sprint){pts[x.t]=(pts[x.t]||0)+x.pts;tot+=x.pts;}}
    for(const t in pts){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+pts[t];}
    shares.push(pts);totals.push(tot);champs.push({d:standingsOf(s).drivers[0]?.id,t:champTeam(s),races:s.races.filter(r=>r.rows.length).length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);
  riverModel={years,shares,totals,champs,teams,teamTotal};
}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  /* With an era lens on, the river zooms: only that era's seasons are drawn and they take the full width. */
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  const i0=era?years.indexOf(era.from):0,i1=era?years.indexOf(era.to):years.length-1,n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/(n-1);
  const x=i=>n===1?padL+(W-padL-padR)/2:padL+(i-i0)*slotW;
  const maxRaces=Math.max(...champs.slice(i0,i1+1).map(c=>c.races));
  const thick=i=>plotH*(era?0.45+0.55*champs[i].races/maxRaces:0.28+0.72*champs[i].races/maxRaces);
  const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};
  for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  for(const t of drawTeams){const up=[],down=[];let any=false;
    for(let i=i0;i<=i1;i++){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
    if(!any)continue;
    if(n===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
    const dn=down.reverse();const d='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';
    const tot=era?eraTotal[t]:teamTotal[t];bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(tn(t))} · ${fmt(Math.round(tot))} points ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';
  if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} constructors scored</text>`;}
  else for(const e of ERAS){const k=years.indexOf(e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const slot=(nxt&&years.indexOf(nxt.from)>=0?x(years.indexOf(nxt.from)):W)-xx;const label=ERA_SHORT[e.id]||e.name;const fits=label.length*6.6+8<=slot;eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${champs[i].t?color(champs[i].t):'#333'}" rx="1"><title>${years[i]} · ${esc(champs[i].d?name(champs[i].d):'—')} · ${esc(champs[i].t?tn(champs[i].t):'')}</title></rect>`;
    hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[1950,1960,1970,1980,1990,2000,2010,2020,2026];
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);
  if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(tn(t))}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top5=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,5);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.races} Grands Prix · champion <b style="color:var(--ink)">${esc(c.d?name(c.d):'—')}</b></div>${top5.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(tn(t))}</span><span>${totals[i]?Math.round(p/totals[i]*100):0}%</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of all points scored that season · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
