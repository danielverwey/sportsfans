'use strict';
/* ============================================================
   APEX — an ode to the Mountain (the Isle of Man TT). Application.
   Same grammar as the other odes: River · Course · Stage.
   The archive is small enough to travel whole: every race, every result, the course and its named places.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number.isInteger(n)?n.toLocaleString('en'):(Math.round(n*100)/100).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const day=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}):'—';
const dm=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}):'';
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};
const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};

/* ---------- the archive ---------- */
const RIDERS=A.riders; const pname=id=>RIDERS[id]?.name||id; const crewName=ids=>(ids||[]).map(pname).join(' / ');
const RF=A.resultFields;
const RACES=A.races.map(r=>({...r,year:r.y,results:r.results.map(row=>{const x=Object.fromEntries(RF.map((k,i)=>[k,row[i]]));x.marque=x.marque||'Unrecorded';x.fin=x.status==='Classified';return x;})}));
for(const r of RACES){r.winner=r.results.find(x=>x.pos===1)||null;r.speed=r.winner?.mph||null;r.solo=r.kind==='solo';}
const byId=Object.fromEntries(RACES.map(r=>[r.id,r]));
const COURSE=A.course, COURSES=A.courses||{};
const FAMILIES=[...new Set(RACES.map(r=>r.family))];
const FAMILY_ORDER=['Senior','Junior','Lightweight','Ultra-Lightweight','Sidecar','Superbike','Superstock','Supersport','Supertwin','Production','Formula TT','Clubman’s','TT Zero','TTXGP','Sportbike','Historic classes'];
FAMILIES.sort((a,b)=>(FAMILY_ORDER.indexOf(a)+1||99)-(FAMILY_ORDER.indexOf(b)+1||99)||a.localeCompare(b));
const RECORDS=A.records||[];

/* ---------- marques: colours ---------- */
const MARQUE_COL={'Honda':'#f34d54','Yamaha':'#507dff','Suzuki':'#ffd23f','Kawasaki':'#79d455','BMW':'#66b5ff','Triumph':'#4dd0b0','Norton':'#c9ccd1','Ducati':'#ff3642','MV Agusta':'#e8c473','Moto Guzzi':'#a3bacc','BSA':'#c9a86a','Velocette':'#7fa08c','Paton':'#ff9ecb','AJS':'#b9cfdd','Mugen':'#ff9e5e','Rudge':'#d5c39f','New Imperial':'#b8a8d8','Excelsior':'#d9a066','Sunbeam':'#ffe08a','Vincent':'#9a9a9a','MotoCzysz':'#9fe0ff','Matchless':'#c1ac91','Rex-Acme':'#c7b3ff','Benelli':'#8fd18f','Mondial':'#e8a0a0','Gilera':'#e97a75','EMC':'#b0c4de','Douglas':'#a0b0a0','Scott':'#d8d8d8','Indian':'#c0392b','Aprilia':'#92df76','LCR':'#8fb8d8','Windle':'#d0b0ff','Ireson':'#b0e0c0','Baker':'#e0c8a0','Shelbourne':'#c0d8ff','DMR':'#ffc0a0','Cotton':'#c8b0a0','Levis':'#a0c0c8','Royal Enfield':'#c86464','Ariel':'#d0c090','NSU':'#a8b8c8','MZ':'#c0c8d0','Bultaco':'#e0a0a0','Morini':'#c8a0c8','Kreidler':'#a0d0d0','Seeley':'#b8c8b8','Padgett':'#c8c8a0','Harris':'#a8a8c8','Britten':'#ff8fb0','Aermacchi':'#c8b8a8','Bianchi':'#a0d8e8','Derbi':'#f0b0a0','Unrecorded':'#5b616b'};
const hueCache={};
const color=m=>{if(MARQUE_COL[m])return MARQUE_COL[m];if(hueCache[m])return hueCache[m];let h=0;for(const ch of String(m||'?'))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[m]=hsl2hex(h%360,40,64);};
const teamVar=m=>`--team:${color(m)}`;

/* ---------- lens: class family (the masthead select), then era + season as everywhere ---------- */
const state={family:'all',era:'all',year:null,tab:'season',race:null,rider:null,marque:null,cls:null,lens:'wins',plens:'wins',heat:'wins',duelBy:'r',dA:null,dB:null,focusTeam:null,whole:false,find2:'',place:null};
const inLens=r=>state.family==='all'?true:r.family===state.family;
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){const map={};for(const r of RACES){if(!inLens(r))continue;(map[r.year]||(map[r.year]={year:r.year,races:[]})).races.push(r);}S=Object.keys(map).map(Number).sort((a,b)=>a-b).map(y=>map[y]);byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1907;LAST_YEAR=S[S.length-1]?.year||2026;seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS=[["stjohns","St John’s and the first Mountain years",1907,1914,"The first Tourist Trophy on the St John’s Short Course in 1907, single- and twin-cylinder classes, then the move to the Mountain Course in 1911 and the arrival of Indian, Rudge and the first Senior and Junior TTs."],
["interwar","The inter-war TT",1920,1939,"Norton, Rudge, Sunbeam and Velocette; Stanley Woods’s ten wins, Jimmie Guthrie, the Lightweight class and the first 90 mph laps."],
["clypse","Works teams and the Clypse years",1947,1959,"The post-war revival, Geoff Duke and the Italian works teams — Gilera, MV Agusta, Moto Guzzi — the Clubman’s races, and the Clypse Course for the smaller classes and sidecars from 1954."],
["gp","The world championship round",1960,1976,"Hailwood, Agostini and Honda’s arrival; the TT as the British round of the world championship until the riders’ boycott took it off the calendar after 1976."],
["formula","Formula TT and the road-racing revival",1977,1989,"Formula TT world titles from 1977, Hailwood’s return in 1978, the production classes and Joey Dunlop’s first Formula One years."],
["dunlop","The Dunlop decades",1990,2004,"Joey Dunlop to his 26th win in 2000, Steve Hislop, Carl Fogarty’s 1992 lap record, David Jefferies and the first 120 mph laps."],
["modern","The modern TT",2005,2026,"Superbike, Superstock and Supersport classes, John McGuinness, Michael Dunlop past his uncle’s record, Peter Hickman’s 136 mph lap and the electric TT Zero."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={stjohns:'First TTs',interwar:'Inter-war',clypse:'Works & Clypse',gp:'Championship round',formula:'Formula TT',dunlop:'Dunlop decades',modern:'Modern TT'};
const ERA_TINY={stjohns:'First',interwar:'Inter-war',clypse:'Clypse',gp:'GP',formula:'Formula',dunlop:'Dunlop',modern:'Modern'};
const ERA_CHIPS={stjohns:['St John’s course 1907–10','Mountain Course 1911','Senior and Junior TTs'],interwar:['Norton and Rudge','Stanley Woods','Lightweight class'],clypse:['Italian works teams','Clypse Course 1954–59','Clubman’s races'],gp:['Hailwood, Agostini','Honda arrives','Championship round until 1976'],formula:['Formula TT titles','Hailwood’s return 1978','Production classes'],dunlop:['Joey Dunlop 26 wins','120 mph laps','Fogarty’s 1992 record'],modern:['Superbike, Superstock','Michael Dunlop’s record','136 mph lap']};
for(const e of ERAS)e.ball={label:'The mountain of the era',features:ERA_CHIPS[e.id],svg:mountainSvg(e)};
function mountainSvg(e){return `<svg viewBox="0 0 300 150" aria-hidden="true"><path d="M10 130 L60 92 L95 108 L150 48 L195 84 L230 70 L290 130 Z" fill="#12151b" stroke="#2e333d" stroke-width="2" stroke-linejoin="round"/><path d="M30 128 C70 118 90 122 120 104 C150 86 170 94 200 112 C230 130 250 126 280 128" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linecap="round" opacity=".9"/><circle cx="120" cy="104" r="5" fill="var(--accent)"/><line x1="10" y1="140" x2="290" y2="140" stroke="#2e333d" stroke-width="2"/><text x="150" y="30" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||ERAS[ERAS.length-1];
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraRaces=()=>eraSeasons().flatMap(s=>s.races);
const lensLabel=()=>state.family==='all'?'all classes':state.family;
const eraLabel=()=>(state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
let aggCache={};
function riderAgg(){const key='r|'+state.family+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const r of eraRaces())for(const x of r.results){for(const id of x.crew){let a=map[id]||(map[id]={id,starts:0,wins:0,pod:0,fin:0,first:r.year,last:r.year,best:null,bestRace:null,marques:{},years:new Set(),fams:{}});a.starts++;if(x.pos===1){a.wins++;a.fams[r.family]=(a.fams[r.family]||0)+1;}if(x.pos&&x.pos<=3)a.pod++;if(x.fin)a.fin++;if(x.mph&&(!a.best||x.mph>a.best)){a.best=x.mph;a.bestRace=r.id;}a.first=Math.min(a.first,r.year);a.last=Math.max(a.last,r.year);a.marques[x.marque]=(a.marques[x.marque]||0)+(x.pos===1?1:0);a.years.add(r.year);}}
  const out=Object.values(map).map(a=>({...a,name:pname(a.id),nyears:a.years.size,rate:pct(a.wins,a.starts),top:Object.entries(a.marques).sort((p,q)=>q[1]-p[1])[0]?.[0]||null}));return aggCache[key]=out;}
function marqueAgg(){const key='m|'+state.family+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const r of eraRaces())for(const x of r.results){const m=x.marque;let a=map[m]||(map[m]={id:m,starts:0,wins:0,pod:0,first:r.year,last:r.year,best:null,riders:new Set(),winners:new Set(),years:new Set()});a.starts++;if(x.pos===1){a.wins++;for(const id of x.crew)a.winners.add(id);}if(x.pos&&x.pos<=3)a.pod++;if(x.mph&&(!a.best||x.mph>a.best))a.best=x.mph;a.first=Math.min(a.first,r.year);a.last=Math.max(a.last,r.year);for(const id of x.crew)a.riders.add(id);a.years.add(r.year);}
  const out=Object.values(map).map(a=>({...a,nr:a.riders.size,nw:a.winners.size,ny:a.years.size,rate:pct(a.wins,a.starts)}));return aggCache[key]=out;}
const LENSES={wins:['Wins','TT races won in the lens.'],pod:['Podiums','Top-three finishes.'],starts:['Recorded starts','Results held in the archive; early decades often record the winner alone.'],nw:['Different winners','Riders who have won on the marque.'],best:['Fastest race','Fastest race average recorded on the marque, mph.'],ny:['Years','Years the marque appears in the results.']};
const PLENSES={wins:['Wins','TT races won in the lens.'],pod:['Podiums','Top-three finishes.'],starts:['Recorded starts','Results held in the archive; not complete careers in the early decades.'],best:['Fastest race','Fastest race average recorded, mph.'],nyears:['Years','TT weeks with a recorded result.'],rate:['Win rate %','Wins divided by recorded starts. Minimum 10 starts.']};
const riderOrder=(a,b)=>b.wins-a.wins||b.pod-a.pod||b.starts-a.starts;
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const map={};for(const r of s.races){const w=r.winner;if(!w)continue;for(const id of w.crew){const a=map[id]||(map[id]={id,wins:0,races:[],marques:{},senior:false});a.wins++;a.races.push(r);a.marques[w.marque]=(a.marques[w.marque]||0)+1;if(r.family==='Senior')a.senior=true;}}
  const ranked=Object.values(map).sort((a,b)=>b.wins-a.wins||(b.senior-a.senior)||a.id.localeCompare(b.id));const senior=s.races.find(r=>r.family==='Senior'&&r.winner)||null;const fastest=[...s.races].filter(r=>r.speed).sort((a,b)=>b.speed-a.speed)[0]||null;
  return seasonBest[s.year]={best:ranked[0]||null,ranked,senior,fastest};}
const marqueOfYear=s=>{const w={};for(const r of s.races)if(r.winner)w[r.winner.marque]=(w[r.winner.marque]||0)+1;return Object.entries(w).sort((a,b)=>b[1]-a[1])[0]?.[0]||null;};

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const s=byYear[state.year];const m=state.whole?marqueAgg().sort((a,b)=>b.wins-a.wins)[0]?.id:(s?marqueOfYear(s):null);acc=m?color(m):'#c9ccd1';sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);sel.options[0].textContent=`Marque of the year · ${m||'—'}`;}
  else{acc=color(v);sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the start (the opening, once per visit): riders leave the line at ten-second intervals ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-tt')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-tt','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2600);setTimeout(out,3400);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of wins by marque, year by year ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const r of s.races){if(!r.winner)continue;w[r.winner.marque]=(w[r.winner.marque]||0)+1;tot++;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({d:c.best?.id,t:c.senior?c.senior.winner.marque:marqueOfYear(s),rec:c.best?`${c.best.wins} win${c.best.wins===1?'':'s'}`:'',senior:c.senior,fastest:c.fastest,races:s.races.length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  // the x axis is calendar time, so the war years and 2001 and 2020–21 stay visible as gaps
  const y0v=years[i0],y1v=years[i1];const span=Math.max(1,y1v-y0v);const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/span;const xOf=y=>n===1?padL+(W-padL-padR)/2:padL+(y-y0v)*slotW;const x=i=>xOf(years[i]);
  const maxRaces=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.races));const thick=i=>plotH*(0.3+0.7*Math.sqrt(champs[i].races/maxRaces));const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  // consecutive-year runs are drawn as continuous bands; a gap year breaks the band
  const runs=[];let cur=[i0];for(let i=i0+1;i<=i1;i++){if(years[i]-years[i-1]>1){runs.push(cur);cur=[i];}else cur.push(i);}runs.push(cur);
  for(const t of drawTeams){let any=false;let d='';for(const run of runs){const up=[],down=[];for(const i of run){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
      if(run.length===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
      const dn=down.reverse();d+='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';}
    if(!any)continue;const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(tot)} wins ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} marques won a race</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.t?color(c.t):'#333'}" rx="1"><title>${years[i]} · ${c.senior?'Senior TT: '+esc(crewName(c.senior.winner.crew))+' ('+esc(c.senior.winner.marque)+')':c.d?esc(pname(c.d))+' · '+c.rec:'—'}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%20===0&&y-years[0]>=8&&years[years.length-1]-y>=4),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span style="position:absolute;left:${((xOf(y)-padL)/(W-padL-padR)*100).toFixed(2)}%">${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top5=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,5);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.races} race${c.races===1?'':'s'}${c.d?` · most wins <b style="color:var(--ink)">${esc(pname(c.d))}</b> ${c.rec}`:''}${c.fastest?` · fastest ${c.fastest.speed} mph`:''}</div>${c.senior?`<div class="row"><span><i class="sw" style="background:${color(c.senior.winner.marque)}"></i>Senior TT</span><span>${esc(crewName(c.senior.winner.crew))}</span></div>`:''}${top5.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${p} win${p===1?'':'s'}</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the week’s wins by marque · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
