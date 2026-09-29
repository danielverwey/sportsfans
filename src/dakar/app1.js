'use strict';
/* ============================================================
   APEX — an ode to the desert (the Dakar Rally). Application.
   Same grammar as the other odes: River · Stage · Routes.
   The archive is small enough to travel whole: every edition, every podium of every class, every route as named.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number.isInteger(n)?n.toLocaleString('en'):(Math.round(n*100)/100).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};
const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};

/* ---------- the archive ---------- */
const yspan=o=>o.first===o.last?String(o.first):`${o.first}–${o.last}`;
const PEOPLE=A.people; const pname=id=>PEOPLE[id]?.name||id; const crewName=ids=>(ids||[]).map(pname).join(' / ');
const RF=A.resultFields;
const EDS=A.editions.map(e=>({...e,year:e.y,results:e.results.map(row=>Object.fromEntries(RF.map((k,i)=>[k,row[i]])))}));
for(const e of EDS){e.winners=Object.fromEntries(e.results.filter(x=>x.rank===1).map(x=>[x.cat,x]));e.car=e.winners.Cars||e.winners.Bikes||null;}
const byYearAll=Object.fromEntries(EDS.map(e=>[e.year,e]));
const CATS=A.categories.map(c=>c.key); const CAT_NOTE=Object.fromEntries(A.categories.map(c=>[c.key,c.note]));
const MAP=A.map; const CITIES=MAP.cities; const BOX=MAP.boxes;
const proj=name=>{const c=CITIES[name];return c?[(c[0]+180)*3,(90-c[1])*3]:null;};

/* ---------- marques: colours ---------- */
const MARQUE_COL=Object.assign({'Land Rover':'#80ad88','Hino':'#ff9e5e','Perlini':'#c7b3ff','Schlesser':'#9fe0ff','DAF':'#ffe08a','MAN':'#a3bacc','Cagiva':'#e49a82','Husqvarna':'#d8d8d8','Hero':'#ff3642','Prodrive':'#c9ccd1','BRX':'#c9ccd1','Audi':'#e8e8e8','Praga':'#b8a8d8','Sunhill':'#c8b0a0','Pinch Racing':'#b0c4de','Nissan':'#c0392b','Ford':'#507dff','Lada':'#d5c39f','Sonacome':'#a0b0a0','LIAZ':'#d9a066','GINAF':'#b9cfdd','MAZ':'#8fd18f','OT3':'#ff9ecb','Fiat':'#c9a86a','Cotel':'#a8b8c8','Bourgoin':'#c0c8d0','Mega':'#e0a0a0','Hummer':'#c8a0c8','Barigo':'#a0d0d0','Suzuki':'#ffd23f','Aprilia':'#92df76','ACMAT':'#b8c8b8','Volvo':'#a8a8c8','Pegaso':'#e8a0a0'},A.colours||{});
const hueCache={};
const color=m=>{if(MARQUE_COL[m])return MARQUE_COL[m];if(hueCache[m])return hueCache[m];let h=0;for(const ch of String(m||'?'))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[m]=hsl2hex(h%360,40,64);};
const teamVar=m=>`--team:${color(m)}`;
const ERA_COL={'Africa':'#f2c654','South America':'#66d3df','Saudi Arabia':'#ff8b37'};

/* ---------- lens: class (the masthead select), then era + season as everywhere ---------- */
const state={cat:'all',era:'all',year:null,tab:'season',pod:null,driver:null,marque:null,cls:null,lens:'wins',plens:'wins',heat:'wins',duelBy:'d',dA:null,dB:null,focusTeam:null,whole:false,find2:'',gridFind:'',gridSort:'year'};
const inLens=x=>state.cat==='all'?true:x.cat===state.cat;
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){S=[];for(const e of EDS){const rows=e.results.filter(inLens);if(!rows.length&&!e.cancelled&&state.cat!=='all')continue;S.push({year:e.year,ed:e,rows,wins:rows.filter(x=>x.rank===1)});}byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1979;LAST_YEAR=S[S.length-1]?.year||2026;seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS=[["sabine","Thierry Sabine’s Paris–Dakar",1979,1991,"Founded by Thierry Sabine after he lost his way in the Ténéré in 1977: the first rally left Paris in December 1978 and reached Dakar in January 1979. Yamaha and Honda on two wheels, Range Rover and then Peugeot on four, a truck class from 1980, and Sabine’s own death in a helicopter crash over Mali in 1986."],
["african","Cape Town, Granada and the last African years",1992,2008,"The finish went all the way to Cape Town in 1992 and the start to Granada, Arras, Marseille, Barcelona and Lisbon; Mitsubishi’s Pajero dominated the cars, KTM took every bike edition from 2001, Kamaz the trucks — and the 2008 rally was cancelled before the start over security in Mauritania."],
["southam","South America",2009,2019,"Argentina, Chile, Peru, Bolivia and Paraguay: Volkswagen, Mini and Peugeot in the cars, KTM’s run unbroken on the bikes, Kamaz’s Chagin and Nikolaev in the trucks, the quads a class of their own, and a 2019 edition run entirely in Peru."],
["saudi","Saudi Arabia",2020,2026,"Every edition since 2020 in Saudi Arabia: Honda ended KTM’s run in 2020, side-by-sides, Challenger, Stock and the Classic joined the podium lists, a hybrid Audi won in 2024, and the Empty Quarter brought back the marathon stage."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={sabine:'Sabine’s Paris–Dakar',african:'Last African years',southam:'South America',saudi:'Saudi Arabia'};
const ERA_TINY={sabine:'Paris–Dakar',african:'Africa',southam:'S. America',saudi:'Saudi'};
const ERA_CHIPS={sabine:['Paris, December 1978','Trucks from 1980','Sabine dies, 1986'],african:['Cape Town 1992','Mitsubishi’s Pajero','2008 cancelled'],southam:['Buenos Aires 2009','KTM unbroken','Peru alone, 2019'],saudi:['Jeddah 2020','Honda ends the run','The Empty Quarter']};
for(const e of ERAS)e.ball={label:'The dune of the era',features:ERA_CHIPS[e.id],svg:duneSvg(e)};
function duneSvg(e){return `<svg viewBox="0 0 300 150" aria-hidden="true"><circle cx="220" cy="62" r="22" fill="var(--accent)" opacity=".9"/><path d="M0 132 C60 96 110 90 150 104 C190 118 230 92 300 110 L300 150 L0 150 Z" fill="#12151b" stroke="#2e333d" stroke-width="2"/><path d="M0 132 C60 96 110 90 150 104 C190 118 230 92 300 110" fill="none" stroke="var(--accent)" stroke-width="2.5" opacity=".9"/><text x="150" y="28" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||ERAS[ERAS.length-1];
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraRows=()=>eraSeasons().flatMap(s=>s.rows.map(x=>({...x,year:s.year,ed:s.ed})));
const lensLabel=()=>state.cat==='all'?'all classes':state.cat;
const eraLabel=()=>(state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
let aggCache={};
function driverAgg(){const key='d|'+state.cat+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const x of eraRows()){for(const id of x.crew){const lead=x.crew[0]===id||x.driver===id;let a=map[id]||(map[id]={id,podiums:0,wins:0,leadWins:0,first:x.year,last:x.year,cats:{},marques:{},years:new Set()});a.podiums++;if(x.rank===1){a.wins++;if(lead)a.leadWins++;a.cats[x.cat]=(a.cats[x.cat]||0)+1;}a.first=Math.min(a.first,x.year);a.last=Math.max(a.last,x.year);a.marques[x.make]=(a.marques[x.make]||0)+(x.rank===1?1:0);a.years.add(x.year);}}
  const out=Object.values(map).map(a=>({...a,name:pname(a.id),nyears:a.years.size,ncats:Object.keys(a.cats).length,top:Object.entries(a.marques).sort((p,q)=>q[1]-p[1])[0]?.[0]||null,topCat:Object.entries(a.cats).sort((p,q)=>q[1]-p[1])[0]?.[0]||null}));return aggCache[key]=out;}
function marqueAgg(){const key='m|'+state.cat+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const x of eraRows()){const m=x.make;let a=map[m]||(map[m]={id:m,podiums:0,wins:0,first:x.year,last:x.year,cats:{},winners:new Set(),years:new Set()});a.podiums++;if(x.rank===1){a.wins++;a.cats[x.cat]=(a.cats[x.cat]||0)+1;a.winners.add(x.driver);}a.first=Math.min(a.first,x.year);a.last=Math.max(a.last,x.year);a.years.add(x.year);}
  const out=Object.values(map).map(a=>({...a,nw:a.winners.size,ny:a.years.size,ncats:Object.keys(a.cats).length}));return aggCache[key]=out;}
const LENSES={wins:['Class wins','Editions won in a class, in the lens.'],podiums:['Podiums','First, second and third places.'],nw:['Different winners','Drivers and riders who have won on the marque.'],ncats:['Classes won','Different classes the marque has won.'],ny:['Editions','Editions with a podium place.']};
const PLENSES={wins:['Wins','Class wins as driver, rider or crew.'],leadWins:['Wins at the wheel','Class wins as the lead driver or rider.'],podiums:['Podiums','First, second and third places.'],ncats:['Classes won','Different classes won.'],nyears:['Editions','Editions with a podium place.']};
const driverOrder=(a,b)=>b.wins-a.wins||b.podiums-a.podiums||a.first-b.first;
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const wins=s.wins;const marques={};for(const x of wins)marques[x.make]=(marques[x.make]||0)+1;const ranked=Object.entries(marques).sort((a,b)=>b[1]-a[1]);return seasonBest[s.year]={marque:ranked[0]?.[0]||null,marques:ranked,wins,car:s.ed.winners.Cars||null,bike:s.ed.winners.Bikes||null,truck:s.ed.winners.Trucks||null};}
const marqueOfYear=s=>champOf(s).marque;

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const s=byYear[state.year];const m=state.whole?marqueAgg().sort((a,b)=>b.wins-a.wins)[0]?.id:(s?marqueOfYear(s):null);acc=m?color(m):'#f2c654';sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);sel.options[0].textContent=`Marque of the year · ${m||'—'}`;}
  else{acc=color(v);sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the opening (once per visit): dawn on the dunes, the first rider away ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-dakar')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-dakar','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2600);setTimeout(out,3400);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of the year’s class wins by marque ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const x of s.wins){w[x.make]=(w[x.make]||0)+1;tot++;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({t:c.marque,car:c.car,bike:c.bike,route:s.ed.route,era:s.ed.era,cancelled:s.ed.cancelled,classes:tot,podiums:s.rows.length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const y0v=years[i0],y1v=years[i1];const span=Math.max(1,y1v-y0v);const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/span;const xOf=y=>n===1?padL+(W-padL-padR)/2:padL+(y-y0v)*slotW;const x=i=>xOf(years[i]);
  const maxC=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.classes));const thick=i=>plotH*(champs[i].classes?0.28+0.72*Math.sqrt(champs[i].classes/maxC):0.02);const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  const runs=[];let cur=[i0];for(let i=i0+1;i<=i1;i++){if(years[i]-years[i-1]>1){runs.push(cur);cur=[i];}else cur.push(i);}runs.push(cur);
  for(const t of drawTeams){let any=false;let d='';for(const run of runs){const up=[],down=[];for(const i of run){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
      if(run.length===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
      const dn=down.reverse();d+='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';}
    if(!any)continue;const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(tot)} class wins ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} winning marques</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.cancelled?'#2a2d33':ERA_COL[c.era]||'#333'}" rx="1"><title>${years[i]} · ${esc(c.route)}${c.cancelled?' · cancelled':c.car?' · cars: '+esc(pname(c.car.driver))+' ('+esc(c.car.make)+')':''}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%10===0&&y-years[0]>=4&&years[years.length-1]-y>=3),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span style="position:absolute;left:${((xOf(y)-padL)/(W-padL-padR)*100).toFixed(2)}%">${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const rows=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,6);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${esc(c.route)} · ${esc(c.era)}${c.cancelled?' · <b style="color:var(--ink)">cancelled before the start</b>':` · ${c.classes} classes · ${c.podiums} podium places`}</div>${c.car?`<div class="row"><span><i class="sw" style="background:${color(c.car.make)}"></i>Cars</span><span>${esc(pname(c.car.driver))} · ${esc(c.car.make)}</span></div>`:''}${c.bike?`<div class="row"><span><i class="sw" style="background:${color(c.bike.make)}"></i>Bikes</span><span>${esc(pname(c.bike.driver))} · ${esc(c.bike.make)}</span></div>`:''}${rows.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${p} class win${p===1?'':'s'}</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the year’s class wins by marque · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
