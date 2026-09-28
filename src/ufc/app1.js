'use strict';
/* ============================================================
   APEX — an ode to the cage (UFC bouts since 1993). Application.
   Same grammar as the other odes: River · Arenas · Stage.
   The archive travels whole: every event, every bout, every fighter, every venue as the sources name it.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number.isInteger(n)?n.toLocaleString('en'):(Math.round(n*100)/100).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const day=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}):'—';
const dm=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}):'';
const clock=s=>s==null?'—':`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};

/* ---------- the archive ---------- */
const FIGHTERS=A.fighters; const pname=id=>FIGHTERS[id]?.name||id;
const BF=A.boutFields;
const BOUTS=A.bouts.map(row=>{const x=Object.fromEntries(BF.map((k,i)=>[k,row[i]]));x.year=x.y;x.fin=x.mk==='KO'||x.mk==='SUB';return x;});
const byBout=Object.fromEntries(BOUTS.map(b=>[b.id,b]));
const EVENTS=A.events.map(e=>({...e,year:e.y,bouts:e.bouts.map(id=>byBout[id]).filter(Boolean)}));
for(const e of EVENTS){e.main=e.bouts[0]||null;e.titles=e.bouts.filter(b=>b.title).length;e.fins=e.bouts.filter(b=>b.fin).length;for(const b of e.bouts)b.ev=e;}
const byEvent=Object.fromEntries(EVENTS.map(e=>[e.id,e]));
const VENUES=A.venues||{};
const DIVS=A.divisions; const DIV=Object.fromEntries(DIVS.map(d=>[d.key,d])); const divLabel=k=>DIV[k]?.label||k;
const DIV_COL={hw:'#ff3642',lhw:'#ff8a3d',mw:'#ffd23f',ww:'#79d455',lw:'#2fd0c2',fw:'#4da3ff',bw:'#8f7bff',flw:'#ff7ad9',wsw:'#ffb3c7',wflw:'#c9a0ff',wbw:'#9fe0ff',wfw:'#ffe08a',wat:'#f4c2ff',open:'#c9ccd1',shw:'#a3bacc',catch:'#8b9099'};
const color=k=>DIV_COL[k]||'#8b9099';
const teamVar=k=>`--team:${color(k)}`;
const MK={KO:['KO / TKO','#ff5a5f'],SUB:['Submission','#4da3ff'],DEC:['Decision','#c9ccd1'],DQ:['Disqualification','#ffb347'],NC:['No contest','#5b616b'],DRAW:['Draw','#8b9099'],OTHER:['Other','#8b9099']};
const mkLabel=k=>MK[k]?.[0]||k; const mkColor=k=>MK[k]?.[1]||'#8b9099';
const shortMethod=b=>b.mk==='DEC'?`Decision${b.dk?' · '+b.dk:''}`:b.mk==='KO'?`KO/TKO${b.det?' · '+b.det:''}`:b.mk==='SUB'?`Submission${b.det?' · '+b.det:''}`:b.mk==='NC'?`No contest${b.det?' · '+b.det:''}`:b.mk==='DRAW'?`Draw${b.det?' · '+b.det:''}`:b.method||'—';
const boutLine=b=>b.res==='W'?`${pname(b.w)} def. ${pname(b.w===b.a?b.b:b.a)}`:`${pname(b.a)} vs. ${pname(b.b)}`;

/* ---------- lens: division (the masthead select), then era + season as everywhere ---------- */
const state={div:'all',era:'all',year:null,tab:'season',event:null,fighter:null,dv:null,venue:null,lens:'bouts',plens:'wins',heat:'bouts',dA:null,dB:null,focusTeam:null,whole:false,find2:'',gridFind:'',gridMin:3,gridSort:'count'};
const inLens=b=>state.div==='all'?true:state.div==='M'?b.sex==='M':state.div==='W'?b.sex==='W':b.div===state.div;
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){const map={};for(const e of EVENTS){const bs=e.bouts.filter(inLens);if(!bs.length)continue;const s=map[e.year]||(map[e.year]={year:e.year,events:[],bouts:[]});s.events.push(e);s.bouts.push(...bs);}
  S=Object.keys(map).map(Number).sort((a,b)=>a-b).map(y=>map[y]);byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1993;LAST_YEAR=S[S.length-1]?.year||2026;seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS=[["origins","The tournaments",1993,1996,"Eight-man tournaments with no weight classes, no rounds and no judges: Royce Gracie’s jiu-jitsu against everyone, Ken Shamrock, Dan Severn, Mark Coleman, and the first Superfight belt."],
["rules","Weight classes and the lean years",1997,2000,"Weight divisions from UFC 12, the first heavyweight and lightweight champions, rounds and gloves, and a promotion driven off pay-per-view and into small halls while the rules were written."],
["zuffa","Zuffa and the unified rules",2001,2004,"New owners in January 2001, the unified rules, Nevada sanctioning, Randy Couture, Chuck Liddell and Tito Ortiz, and the light-heavyweight rivalries that carried the sport to television."],
["tuf","The Ultimate Fighter boom",2005,2010,"Griffin–Bonnar and the reality-show finale of April 2005, Georges St-Pierre, Anderson Silva, Brock Lesnar, UFC 100 and a calendar that grew from a handful of cards to two dozen a year."],
["global","The global expansion",2011,2016,"Network television, Fight Nights on four continents, Jon Jones, the first women’s bout in 2013 and Ronda Rousey, Conor McGregor’s two belts, and the sale to WME–IMG in 2016."],
["espn","The streaming years",2017,2022,"Khabib Nurmagomedov, Amanda Nunes, Israel Adesanya, the move to streaming in 2019, then the empty Apex and Fight Island cards of the pandemic and the crowds’ return."],
["modern","The modern card",2023,2026,"Alex Pereira, Islam Makhachev, Ilia Topuria, Zhang Weili and Valentina Shevchenko; forty-odd cards a year, the Apex in Las Vegas as the promotion’s home stage."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={origins:'Tournaments',rules:'Weight classes',zuffa:'Zuffa & unified rules',tuf:'TUF boom',global:'Global expansion',espn:'Streaming years',modern:'Modern card'};
const ERA_TINY={origins:'Tourn.',rules:'Rules',zuffa:'Zuffa',tuf:'TUF',global:'Global',espn:'Stream',modern:'Modern'};
const ERA_CHIPS={origins:['No weight classes','Royce Gracie','Superfight belt'],rules:['Weight classes 1997','Rounds and gloves','First champions'],zuffa:['Zuffa, January 2001','Unified rules','Couture, Liddell, Ortiz'],tuf:['Griffin–Bonnar 2005','St-Pierre, Silva','UFC 100'],global:['Network television','Women’s bouts 2013','McGregor’s two belts'],espn:['Nurmagomedov, Nunes','Streaming 2019','Apex and Fight Island'],modern:['Pereira, Makhachev','Forty cards a year','The Apex']};
for(const e of ERAS)e.ball={label:'The cage of the era',features:ERA_CHIPS[e.id],svg:cageSvg(e)};
function cageSvg(e){return `<svg viewBox="0 0 300 150" aria-hidden="true"><ellipse cx="150" cy="92" rx="112" ry="34" fill="#12151b" stroke="#2e333d" stroke-width="2"/><g stroke="#2e333d" stroke-width="2" stroke-linecap="round"><line x1="38" y1="92" x2="38" y2="52"/><line x1="82" y1="120" x2="82" y2="80"/><line x1="150" y1="126" x2="150" y2="86"/><line x1="218" y1="120" x2="218" y2="80"/><line x1="262" y1="92" x2="262" y2="52"/></g><ellipse cx="150" cy="86" rx="112" ry="34" fill="none" stroke="var(--accent)" stroke-width="3" opacity=".9"/><text x="150" y="24" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||ERAS[ERAS.length-1];
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraBouts=()=>eraSeasons().flatMap(s=>s.bouts);
const eraEvents=()=>eraSeasons().flatMap(s=>s.events);
const lensLabel=()=>state.div==='all'?'all divisions':state.div==='M'?'men’s divisions':state.div==='W'?'women’s divisions':divLabel(state.div);
const eraLabel=()=>(state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
let aggCache={};
function fighterAgg(){const key='f|'+state.div+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const b of eraBouts()){for(const id of [b.a,b.b]){let a=map[id]||(map[id]={id,bouts:0,wins:0,losses:0,draws:0,nc:0,fin:0,ko:0,sub:0,dec:0,title:0,titleW:0,first:b.year,last:b.year,fastest:null,fastBout:null,divs:{},years:new Set(),bonus:0});a.bouts++;
    if(b.res==='W'){if(b.w===id){a.wins++;if(b.mk==='KO'){a.ko++;a.fin++;}else if(b.mk==='SUB'){a.sub++;a.fin++;}else if(b.mk==='DEC')a.dec++;if(b.secs!=null&&b.fin&&(a.fastest==null||b.secs<a.fastest)){a.fastest=b.secs;a.fastBout=b.id;}}else a.losses++;}else if(b.res==='D')a.draws++;else a.nc++;
    if(b.title){a.title++;if(b.w===id)a.titleW++;}a.first=Math.min(a.first,b.year);a.last=Math.max(a.last,b.year);a.divs[b.div]=(a.divs[b.div]||0)+1;a.years.add(b.year);}}
  for(const e of eraEvents())for(const bn of e.bonuses||[])for(const who of bn.who||[]){const id=fighterIdOf(who);if(id&&map[id])map[id].bonus++;}
  const out=Object.values(map).map(a=>({...a,name:pname(a.id),nyears:a.years.size,rate:pct(a.wins,a.wins+a.losses+a.draws),finrate:pct(a.fin,a.wins),top:Object.entries(a.divs).sort((p,q)=>q[1]-p[1])[0]?.[0]||null}));return aggCache[key]=out;}
const nameIndex={};for(const [id,f] of Object.entries(FIGHTERS))nameIndex[f.name.toLowerCase()]=id;
function fighterIdOf(who){if(FIGHTERS[who])return who;const s=String(who||'').toLowerCase();if(nameIndex[s])return nameIndex[s];const sl=s.replace(/’|'/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');return FIGHTERS[sl]?sl:null;}
function divAgg(){const key='d|'+state.div+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const b of eraBouts()){let a=map[b.div]||(map[b.div]={id:b.div,bouts:0,fin:0,ko:0,sub:0,dec:0,title:0,first:b.year,last:b.year,fighters:new Set(),years:new Set(),wins:{},secs:0,nsecs:0});a.bouts++;if(b.fin)a.fin++;if(b.mk==='KO')a.ko++;if(b.mk==='SUB')a.sub++;if(b.mk==='DEC')a.dec++;if(b.title)a.title++;a.first=Math.min(a.first,b.year);a.last=Math.max(a.last,b.year);a.fighters.add(b.a);a.fighters.add(b.b);a.years.add(b.year);if(b.w)a.wins[b.w]=(a.wins[b.w]||0)+1;if(b.secs!=null){a.secs+=b.secs;a.nsecs++;}}
  const out=Object.values(map).map(a=>({...a,nf:a.fighters.size,ny:a.years.size,finrate:pct(a.fin,a.bouts),avg:a.nsecs?Math.round(a.secs/a.nsecs):null,top:Object.entries(a.wins).sort((p,q)=>q[1]-p[1])[0]||null})).sort((a,b)=>(DIV[a.id]?.order??99)-(DIV[b.id]?.order??99));return aggCache[key]=out;}
const LENSES={bouts:['Bouts','Bouts fought in the division in the lens.'],fin:['Finishes','Bouts ended inside the distance — knockout, technical knockout or submission.'],finrate:['Finish rate %','Finishes as a share of bouts.'],title:['Title bouts','Bouts for a championship, as the notes record them.'],nf:['Fighters','Different fighters who fought in the division.'],ny:['Years','Years with a bout in the division.']};
const PLENSES={wins:['Wins','Bouts won in the lens.'],fin:['Finishes','Wins by knockout, technical knockout or submission.'],ko:['KO / TKO wins','Wins by knockout or technical knockout.'],sub:['Submission wins','Wins by submission.'],titleW:['Title-bout wins','Wins in bouts recorded as championship bouts.'],bouts:['Bouts','Bouts fought in the lens.'],rate:['Win rate %','Wins divided by wins, losses and draws. Minimum 8 bouts.'],bonus:['Bonus awards','Fight, performance, knockout and submission of the night, where the article lists them.']};
const fighterOrder=(a,b)=>b.wins-a.wins||b.fin-a.fin||b.titleW-a.titleW||b.bouts-a.bouts;
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const map={};for(const b of s.bouts){if(!b.w)continue;const a=map[b.w]||(map[b.w]={id:b.w,wins:0,fin:0,titleW:0,bouts:[],divs:{}});a.wins++;if(b.fin)a.fin++;if(b.title)a.titleW++;a.bouts.push(b);a.divs[b.div]=(a.divs[b.div]||0)+1;}
  const ranked=Object.values(map).sort((a,b)=>b.wins-a.wins||b.titleW-a.titleW||b.fin-a.fin||a.id.localeCompare(b.id));const titles=s.bouts.filter(b=>b.title);const fastest=s.bouts.filter(b=>b.fin&&b.secs!=null).sort((a,b)=>a.secs-b.secs)[0]||null;
  return seasonBest[s.year]={best:ranked[0]||null,ranked,titles,fastest,fins:s.bouts.filter(b=>b.fin).length};}
const divOfYear=s=>{const w={};for(const b of s.bouts)w[b.div]=(w[b.div]||0)+1;return Object.entries(w).sort((a,b)=>b[1]-a[1])[0]?.[0]||null;};

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const s=byYear[state.year];const d=state.whole?divAgg().sort((a,b)=>b.bouts-a.bouts)[0]?.id:(s?divOfYear(s):null);acc=d?color(d):'#c9ccd1';sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);sel.options[0].textContent=`Division of the year · ${d?divLabel(d):'—'}`;}
  else{acc=color(v);sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the opening (once per visit): the cage door closes ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-ufc')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-ufc','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2500);setTimeout(out,3300);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of the year’s bouts by division ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const b of s.bouts){w[b.div]=(w[b.div]||0)+1;tot++;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({d:c.best?.id,t:divOfYear(s),rec:c.best?`${c.best.wins} win${c.best.wins===1?'':'s'}`:'',titles:c.titles.length,fins:c.fins,events:s.events.length,bouts:s.bouts.length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>(DIV[a]?.order??99)-(DIV[b]?.order??99));riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const y0v=years[i0],y1v=years[i1];const span=Math.max(1,y1v-y0v);const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/span;const xOf=y=>n===1?padL+(W-padL-padR)/2:padL+(y-y0v)*slotW;const x=i=>xOf(years[i]);
  const maxB=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.bouts));const thick=i=>plotH*(0.22+0.78*Math.sqrt(champs[i].bouts/maxB));const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  const runs=[];let cur=[i0];for(let i=i0+1;i<=i1;i++){if(years[i]-years[i-1]>1){runs.push(cur);cur=[i];}else cur.push(i);}runs.push(cur);
  for(const t of drawTeams){let any=false;let d='';for(const run of runs){const up=[],down=[];for(const i of run){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
      if(run.length===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
      const dn=down.reverse();d+='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';}
    if(!any)continue;const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(divLabel(t))} · ${fmt(tot)} bouts ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} divisions</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.t?color(c.t):'#333'}" rx="1"><title>${years[i]} · ${c.events} events · ${c.bouts} bouts · ${c.titles} title bouts${c.d?' · most wins '+esc(pname(c.d))+' ('+c.rec+')':''}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%10===0&&y-years[0]>=4&&years[years.length-1]-y>=3),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span style="position:absolute;left:${((xOf(y)-padL)/(W-padL-padR)*100).toFixed(2)}%">${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(DIV[a]?.order??99)-(DIV[b]?.order??99)).filter(t=>scoreOf[t]>0).slice(0,16);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(divLabel(t))}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top6=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,6);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.events} event${c.events===1?'':'s'} · ${c.bouts} bouts · ${c.titles} title bout${c.titles===1?'':'s'} · ${pct(c.fins,c.bouts)}% finishes${c.d?` · most wins <b style="color:var(--ink)">${esc(pname(c.d))}</b> ${c.rec}`:''}</div>${top6.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(divLabel(t))}</span><span>${p} bout${p===1?'':'s'}</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the year’s bouts by division · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
