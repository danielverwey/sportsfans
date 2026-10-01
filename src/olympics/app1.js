'use strict';
/* ============================================================
   APEX — an ode to the Games (the Summer Olympics). Application.
   Same grammar as the other odes: River · Stage · Hosts.
   The archive travels whole: every Games, every medal event, every award with its delegation and its named athletes.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
const WINTER=A.season==='winter';const GAMES_NAME=A.name||(WINTER?'Winter Olympics':'Summer Olympics');const GAMES_WORD=WINTER?'Winter Games':'Summer Games';const LIGHT_KEY=WINTER?'apex-flame-w':'apex-flame';
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
const ATH=A.athletes; const aname=id=>ATH[id]||String(id).replace(/_/g,' ');
const EF=A.eventFields, WF=A.awardFields;
const EVENTS=A.events.map(r=>{const e=Object.fromEntries(EF.map((k,i)=>[k,r[i]]));e.awards=[];return e;});
const evById=Object.fromEntries(EVENTS.map(e=>[e.id,e]));
const AWARDS=A.awards.map(r=>{const w=Object.fromEntries(WF.map((k,i)=>[k,r[i]]));const e=evById[w.e];if(e){w.ev=e;w.y=e.y;w.sport=e.sport;e.awards.push(w);}return w;}).filter(w=>w.ev);
const GAMES=A.games.map(g=>({...g,year:g.y,events:[]}));
const byYearAll=Object.fromEntries(GAMES.map(g=>[g.year,g]));
for(const e of EVENTS){const g=byYearAll[e.y];if(g)g.events.push(e);}
const SPORTS=A.sports; const NATIONS=A.nations; const MAP=A.map;
const MEDAL=['','gold','silver','bronze'], MEDALCAP=['','Gold','Silver','Bronze'], MK=['','g','s','b'];
const GENDER_LABEL={Men:'men’s',Women:'women’s',Mixed:'mixed',Open:'open'};
const LIN={};for(const e of EVENTS)(LIN[e.key]||(LIN[e.key]=[])).push(e);   // the same event across Games
for(const k in LIN)LIN[k].sort((a,b)=>a.y-b.y);
const linName=key=>{const es=LIN[key];if(!es)return key;const e=es[es.length-1];return e.event;};
const evLabel=(e,withGender=true)=>{const g=e.gender;const n=e.event;const has=/^(men|women|mixed|open)/i.test(n);return withGender&&!has&&g?`${GENDER_LABEL[g]==='open'?'Open':GENDER_LABEL[g].charAt(0).toUpperCase()+GENDER_LABEL[g].slice(1)} ${n}`:n;};
const proj=p=>[(p[1]+180)*3,(90-p[2])*3];

/* ---------- delegations: colours ---------- */
const NAT_COL=A.colours||{};
const hueCache={};
const color=n=>{if(NAT_COL[n])return NAT_COL[n];if(hueCache[n])return hueCache[n];let h=0;for(const ch of String(n||'?'))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[n]=hsl2hex(h%360,38,66);};
const teamVar=n=>`--team:${color(n)}`;
const MEDAL_COL={1:'#f2c666',2:'#c9d3dc',3:'#d19b79'};

/* ---------- lens: sport and event category (the masthead selects), then era + Games as everywhere ---------- */
const state={sport:'all',cat:'all',era:'all',year:null,tab:'season',event:null,athlete:null,nation:null,sportv:null,host:null,lens:'gold',plens:'gold',slens:'events',heat:'gold',duelBy:'n',dA:null,dB:null,focusTeam:null,whole:false,find2:'',gridFind:'',gridSort:'year',metric:'gold',evSport:null,showAll:false};
const inLens=e=>(state.sport==='all'||e.sport===state.sport)&&(state.cat==='all'||e.gender===state.cat);
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){S=[];for(const g of GAMES){const events=g.events.filter(inLens);if(!events.length&&!g.cancelled&&(state.sport!=='all'||state.cat!=='all'))continue;const awards=events.flatMap(e=>e.awards);S.push({year:g.year,g,events,awards,wins:awards.filter(w=>w.rank===1)});}byYear=Object.fromEntries(S.map(s=>[s.year,s]));const held=S.filter(s=>!s.g.cancelled);FIRST_YEAR=held[0]?.year||(WINTER?1924:1896);LAST_YEAR=held[held.length-1]?.year||A.lastYear;seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year]||byYear[state.year].g.cancelled)state.year=LAST_YEAR;}
const ERAS=(WINTER?[["founding","The founding Games",1924,1936,"Chamonix 1924, the International Winter Sports Week recognised as the first Winter Games; St. Moritz 1928, Lake Placid 1932 and Garmisch-Partenkirchen 1936, where alpine skiing arrived. Sonja Henie’s three figure skating golds; Norway on top of the first four tables but one."],["postwar","The postwar Games",1948,1964,"St. Moritz 1948 after two cancelled editions; Oslo 1952 and the first winter torch relay from Morgedal; Cortina d’Ampezzo 1956, the first on television and the Soviet Union’s debut; Squaw Valley 1960 with biathlon and women’s speed skating and no bobsleigh run; Innsbruck 1964, where luge began."],["coldwar","Boycotts and the Cold War",1968,1988,"Grenoble 1968 and Jean-Claude Killy’s three golds; Sapporo 1972, the first in Asia; Innsbruck again in 1976 after Denver withdrew; Lake Placid 1980, the Miracle on Ice and Eric Heiden’s five golds; Sarajevo 1984 and Torvill and Dean; Calgary 1988, the first sixteen-day Games."],["rhythm","A rhythm of its own",1992,2010,"Albertville 1992 with the Unified Team and a reunited Germany; Lillehammer only two years later, as the Winter Games moved to their own cycle; Nagano 1998 brought snowboarding, curling, women’s ice hockey and the NHL; Salt Lake City 2002 and the return of skeleton; Turin 2006; Vancouver 2010 and Canada’s fourteen golds at home."],["modern","The modern Games",2014,2026,"Sochi 2014 with a programme of 98 events; Pyeongchang 2018 and a unified Korean team; Beijing 2022, the first city to host both Games; Milano Cortina 2026 across two host cities, with ski mountaineering’s debut and 116 events."]]:[["founding","The founding Games",1896,1912,"Pierre de Coubertin’s revival: Athens in 1896 with 241 athletes, then Paris and St Louis spread over months beside their world’s fairs, London 1908 with the first purpose-built stadium, Stockholm 1912 with athletes from five continents and electric timing. Women first competed in 1900; the gold, silver and bronze of the earliest Games are retrospective labels."],
["interwar","Between the wars",1920,1936,"Antwerp raised the Olympic flag and swore the first oath after a cancelled 1916; Paris 1924 built the first village, Amsterdam 1928 opened athletics to women and lit a cauldron, Los Angeles 1932 crowded sixteen days, and Berlin 1936 carried the first torch relay while Jesse Owens won four golds."],
["postwar","The postwar Games",1948,1964,"The austerity Games of London 1948 after two cancelled editions; the Soviet Union’s first appearance at Helsinki 1952; Melbourne 1956 with its equestrian events in Stockholm; Rome 1960 and Abebe Bikila barefoot on the Appian Way; Tokyo 1964, the first Games in Asia."],
["coldwar","Boycotts and the Cold War",1968,1988,"Mexico City’s altitude and the raised fists; Munich 1972, Mark Spitz’s seven golds and the massacre; Nadia Comăneci’s perfect ten at Montreal 1976; the boycotts of Moscow 1980 and Los Angeles 1984 that hollowed two medal tables; Seoul 1988, the last Games of the Soviet Union and East Germany."],
["global","The global Games",1992,2008,"Barcelona with the Unified Team, South Africa’s return and the Dream Team; the centennial Games of Atlanta; Sydney 2000 and Cathy Freeman; Athens back where it began; Beijing 2008 with Usain Bolt’s three world records and Michael Phelps’s eight golds."],
["modern","The modern Games",2012,2024,"London for a third time; Rio 2016, the first Games in South America and the first Refugee team; Tokyo 2020 held in 2021 behind closed doors; Paris 2024, a century after its last, the first with as many women as men on the programme and breaking’s only appearance."]]).map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={founding:'The founding Games',interwar:'Between the wars',postwar:'Postwar',coldwar:'Boycotts & Cold War',global:'The global Games',rhythm:'A rhythm of its own',modern:'The modern Games'};
const ERA_TINY={founding:'Founding',interwar:'Interwar',postwar:'Postwar',coldwar:'Cold War',global:'Global',rhythm:'Own rhythm',modern:'Modern'};
const ERA_CHIPS=WINTER?{founding:['Chamonix 1924','Sonja Henie','Alpine skiing from 1936'],postwar:['The first torch relay','Cortina on television','Luge from 1964'],coldwar:['Sapporo, first in Asia','The Miracle on Ice','Calgary’s sixteen days'],rhythm:['Lillehammer, two years on','Snowboard and curling','Vancouver’s fourteen golds'],modern:['Sochi’s 98 events','Pyeongchang 2018','Milano Cortina 2026']}:{founding:['Athens 1896','Women from 1900','Stockholm 1912'],interwar:['The flag and the oath','The first village','The first torch relay'],postwar:['London 1948','The Soviet Union arrives','Tokyo 1964'],coldwar:['Munich 1972','Two boycotts','Seoul 1988'],global:['Barcelona 1992','Sydney 2000','Beijing 2008'],modern:['London 2012','Tokyo behind closed doors','Paris 2024']};
for(const e of ERAS)e.ball={label:'The hosts of the era',features:ERA_CHIPS[e.id],svg:eraSvg(e)};
function eraSvg(e){const pts=GAMES.filter(g=>!g.cancelled&&g.year>=e.from&&g.year<=e.to).flatMap(g=>g.points.map(p=>({p:proj(p),y:g.year})));return `<svg viewBox="0 0 1080 540" aria-hidden="true" style="background:#0b0d12;border-radius:8px"><use href="#land" class="land" style="stroke-width:1.2"/>${pts.map(o=>`<circle cx="${o.p[0].toFixed(1)}" cy="${o.p[1].toFixed(1)}" r="9" fill="var(--accent)" stroke="#07080a" stroke-width="2"><title>${o.y}</title></circle>`).join('')}<text x="24" y="60" font-family="JetBrains Mono,monospace" font-size="28" letter-spacing="6" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||(y<1896?ERAS[0]:ERAS[ERAS.length-1]);
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraHeld=()=>eraSeasons().filter(s=>!s.g.cancelled);
const eraAwards=()=>eraSeasons().flatMap(s=>s.awards);
const eraEvents=()=>eraSeasons().flatMap(s=>s.events);
const lensLabel=()=>(state.sport==='all'?'all sports':state.sport)+(state.cat==='all'?'':' · '+GENDER_LABEL[state.cat]+' events');
const eraLabel=()=>(state.era==='all'?`all eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
let aggCache={};
const medalCmp=(a,b)=>b.gold-a.gold||b.silver-a.silver||b.bronze-a.bronze||b.total-a.total||String(a.name||a.id).localeCompare(String(b.name||b.id));
function nationAgg(){const key='n|'+state.sport+'|'+state.cat+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const w of eraAwards()){let a=map[w.nation]||(map[w.nation]={id:w.nation,name:w.nation,gold:0,silver:0,bronze:0,total:0,first:w.y,last:w.y,years:new Set(),sports:{},byYear:{}});a[MEDAL[w.rank]]++;a.total++;a.first=Math.min(a.first,w.y);a.last=Math.max(a.last,w.y);a.years.add(w.y);const sp=a.sports[w.sport]||(a.sports[w.sport]={gold:0,total:0});sp.total++;if(w.rank===1)sp.gold++;const by=a.byYear[w.y]||(a.byYear[w.y]={gold:0,silver:0,bronze:0,total:0});by[MEDAL[w.rank]]++;by.total++;}
  const out=Object.values(map).map(a=>{const best=Object.entries(a.byYear).sort((p,q)=>q[1].gold-p[1].gold||q[1].total-p[1].total)[0];return {...a,games:a.years.size,nsports:Object.keys(a.sports).length,topSport:Object.entries(a.sports).sort((p,q)=>q[1].gold-p[1].gold||q[1].total-p[1].total)[0]?.[0]||null,best:best?{y:+best[0],...best[1]}:null};});
  out.sort(medalCmp);out.forEach((a,i)=>a.rank=i&&medalCmp(a,out[i-1])===0?out[i-1].rank:i+1);return aggCache[key]=out;}
function athleteAgg(){const key='a|'+state.sport+'|'+state.cat+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const w of eraAwards()){for(const id of w.athletes){let a=map[id]||(map[id]={id,gold:0,silver:0,bronze:0,total:0,first:w.y,last:w.y,years:new Set(),sports:{},nations:{},events:new Set()});a[MEDAL[w.rank]]++;a.total++;a.first=Math.min(a.first,w.y);a.last=Math.max(a.last,w.y);a.years.add(w.y);a.sports[w.sport]=(a.sports[w.sport]||0)+1;a.nations[w.nation]=(a.nations[w.nation]||0)+1;a.events.add(w.ev.key);}}
  const out=Object.values(map).map(a=>({...a,name:aname(a.id),games:a.years.size,nsports:Object.keys(a.sports).length,nevents:a.events.size,sport:Object.entries(a.sports).sort((p,q)=>q[1]-p[1])[0]?.[0]||null,nation:Object.entries(a.nations).sort((p,q)=>q[1]-p[1])[0]?.[0]||null}));
  out.sort(medalCmp);return aggCache[key]=out;}
function sportAgg(){const key='s|'+state.sport+'|'+state.cat+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const e of eraEvents()){let a=map[e.sport]||(map[e.sport]={id:e.sport,name:e.sport,events:0,first:e.y,last:e.y,years:new Set(),nations:{},athletes:{},awards:0,lineages:new Set()});a.events++;a.first=Math.min(a.first,e.y);a.last=Math.max(a.last,e.y);a.years.add(e.y);a.lineages.add(e.key);for(const w of e.awards){a.awards++;const n=a.nations[w.nation]||(a.nations[w.nation]={gold:0,total:0});n.total++;if(w.rank===1)n.gold++;for(const id of w.athletes){const p=a.athletes[id]||(a.athletes[id]={gold:0,total:0});p.total++;if(w.rank===1)p.gold++;}}}
  const out=Object.values(map).map(a=>({...a,games:a.years.size,nlin:a.lineages.size,topNation:Object.entries(a.nations).sort((p,q)=>q[1].gold-p[1].gold||q[1].total-p[1].total)[0]||null,topAthlete:Object.entries(a.athletes).sort((p,q)=>q[1].gold-p[1].gold||q[1].total-p[1].total)[0]||null}));return aggCache[key]=out;}
const LENSES={gold:['Gold medals','Gold medals won by the delegation, in the lens; ties in the table count for each delegation.'],total:['All medals','Gold, silver and bronze together.'],games:['Games on the podium','Games at which the delegation won a medal.'],nsports:['Sports','Different sports the delegation has medalled in.'],silver:['Silver medals','Silver medals alone.'],bronze:['Bronze medals','Bronze medals alone.']};
const PLENSES={gold:['Gold medals','Gold medals as an individual or in a team, pair or relay.'],total:['All medals','Gold, silver and bronze together.'],games:['Games','Games at which the athlete won a medal.'],nevents:['Different events','Different events medalled in.'],nsports:['Sports','Different sports medalled in.']};
const SLENSES={events:['Medal events','Events with medals in the lens.'],games:['Games','Games at which the sport was contested.'],awards:['Medals awarded','Gold, silver and bronze awards.'],nlin:['Different events','Events by their lineage: the 100 metres is one event across every Games.']};
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const map={};for(const w of s.awards){const a=map[w.nation]||(map[w.nation]={id:w.nation,name:w.nation,gold:0,silver:0,bronze:0,total:0});a[MEDAL[w.rank]]++;a.total++;}const ranked=Object.values(map).sort(medalCmp);ranked.forEach((a,i)=>a.rank=i&&medalCmp(a,ranked[i-1])===0?ranked[i-1].rank:i+1);return seasonBest[s.year]={leader:ranked[0]?.id||null,table:ranked,nations:ranked.length,medallists:new Set(s.awards.flatMap(w=>w.athletes)).size};}
const leaderOf=s=>champOf(s).leader;

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const s=byYear[state.year];const n=state.whole?nationAgg()[0]?.id:(s?leaderOf(s):null);acc=n?color(n):'#f2c666';sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);sel.options[0].textContent=`Nation of the Games · ${n||'—'}`;}
  else{acc=color(v);sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the opening (once per visit): the cauldron is lit ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem(LIGHT_KEY)==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem(LIGHT_KEY,'1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2800);setTimeout(out,3600);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of the Games' medals by delegation ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;const rows=state.metric==='gold'?s.wins:s.awards;for(const x of rows){w[x.nation]=(w[x.nation]||0)+1;tot++;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({t:c.leader,table:c.table.slice(0,3),city:s.g.city,country:s.g.country,cancelled:s.g.cancelled,events:s.events.length,medals:s.awards.length,nations:c.nations});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const y0v=years[i0],y1v=years[i1];const span=Math.max(4,y1v-y0v);const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/span*4;const xOf=y=>n===1?padL+(W-padL-padR)/2:padL+(y-y0v)/span*(W-padL-padR);const x=i=>xOf(years[i]);
  const maxC=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.events));const thick=i=>plotH*(champs[i].events?0.22+0.78*Math.sqrt(champs[i].events/maxC):0.02);const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  const runs=[];let cur=[i0];for(let i=i0+1;i<=i1;i++){if(years[i]-years[i-1]>4){runs.push(cur);cur=[i];}else cur.push(i);}runs.push(cur);
  for(const t of drawTeams){let any=false;let d='';for(const run of runs){const up=[],down=[];for(const i of run){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
      if(run.length===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
      const dn=down.reverse();d+='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';}
    if(!any)continue;const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(tot)} ${state.metric==='gold'?'gold medals':'medals'} ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} delegations on the podium</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.cancelled?'#2a2d33':c.t?color(c.t):'#333'}" rx="1"><title>${years[i]} · ${esc(c.city)}${c.cancelled?' · cancelled':c.t?' · on top: '+esc(c.t):''}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%20===0&&y-years[0]>=8&&years[years.length-1]-y>=8),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span style="position:absolute;left:${((xOf(y)-padL)/(W-padL-padR)*100).toFixed(2)}%">${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const rows=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,6);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${esc(c.city)}${c.country?' · '+esc(c.country):''}${c.cancelled?' · <b style="color:var(--ink)">cancelled</b>':` · ${c.events} medal events · ${c.medals} medals · ${c.nations} delegations on the podium`}</div>${c.table.map(t=>`<div class="row"><span><i class="sw" style="background:${color(t.id)}"></i>${esc(t.id)}</span><span>${t.gold} · ${t.silver} · ${t.bronze}</span></div>`).join('')}${rows.filter(([t])=>!c.table.some(x=>x.id===t)).slice(0,3).map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${p} ${state.metric==='gold'?'gold':'medal'}${p===1?'':'s'}</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the Games’ ${state.metric==='gold'?'gold medals':'medals'} by delegation · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){const y=+hit.dataset.y;if(byYear[y]&&!byYear[y].g.cancelled)setSeason(y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
