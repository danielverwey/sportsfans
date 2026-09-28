'use strict';
/* ============================================================
   APEX — an ode to the tour (tennis). Application.
   Same grammar as the other odes: River · Courts · Stage.
   Reads the core archive (players, tournaments, editions, the roll of honour, player-season figures);
   the matches of a season arrive per year from DETAILS (embedded offline, fetched on the site).
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const PACK=window.PACK||(()=>{const packed=atob(document.getElementById('archive-data').textContent.trim());const bytes=new Uint8Array(packed.length);for(let i=0;i<packed.length;i++)bytes[i]=packed.charCodeAt(i);return JSON.parse(pako.ungzip(bytes,{to:'string'}));})();
const A=PACK.core, DETAILS=PACK.details||{}, DETAIL_URL=PACK.detailUrl||null;
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number.isInteger(n)?n.toLocaleString('en'):(Math.round(n*10)/10).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const day=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}):'—';
const dm=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}):'—';
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};
const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};
const unpack=(fields,row)=>Object.fromEntries(fields.map((k,i)=>[k,row[i]]));

/* ---------- the archive ---------- */
const PLAYERS=A.players; const pname=id=>PLAYERS[id]?.n||id; const pnames=ids=>(ids||[]).map(pname).join(' / ');
const TOURN=Object.fromEntries(Object.entries(A.tournaments).map(([id,r])=>[id,{id,...unpack(A.tFields,r)}]));
const EDS=Object.fromEntries(Object.entries(A.editions).map(([id,r])=>{const e={id,...unpack(A.eFields,r)};e.team=!!e.team;if(!e.name)e.name=TOURN[e.t]?.n||e.id;return [id,e];}));
const CHAMPS=A.champions.map(r=>unpack(A.cFields,r));
const PS=A.ps.map(r=>unpack(A.psFields,r));
const RIVALS=A.rivals||{}, RECORDS=A.records||{}, IOC=A.ioc||{}, RIVER=A.river||{}, TITLESBY=A.titlesBy||{};
const MF=['id','w','l','s','r','n','mins','bo','ws','ls','wr','lr','st','src'];
const MAJORS=Object.values(TOURN).filter(t=>t.major).map(t=>t.id);
const natName=c=>IOC[c]||c||'Unlisted';
const SURF={Hard:'#3b82f6',Clay:'#d2622b',Grass:'#4caf50',Carpet:'#8b7bb5',Unknown:'#737d8c'};
const surfColor=s=>SURF[s]||SURF.Unknown;
const LEVEL={G:'Grand Slam',M:'Masters 1000',PM:'Premier Mandatory',P:'Premier',I:'International',W:'WTA Tour',A:'Tour',T1:'Tier I',T2:'Tier II',T3:'Tier III',T4:'Tier IV',T5:'Tier V',F:'Tour Finals',D:'Team competition',CC:'Team cup',O:'Olympic Games',E:'Exhibition',J:'Junior','50+H':'Senior','35+H':'Senior'};
const levelName=l=>LEVEL[l]||l;
const LEVEL_RANK={G:6,F:5,O:5,M:4,PM:4,P:3,T1:3,T2:2,W:2,A:2,I:2,T3:1,T4:1,T5:1,CC:1,D:1,E:0,J:0};

/* ---------- nations: colours ---------- */
const NAT_COL={'':'#4b5058',UNK:'#4b5058',USA:'#d62839',AUS:'#ffcc00',GBR:'#2c4ec7',FRA:'#7aa6ff',ESP:'#ff8c1a',GER:'#c9ccd1',FRG:'#c9ccd1',SWE:'#3ec6b8',ARG:'#9dd2f2',CZE:'#7b3fa0',TCH:'#7b3fa0',SUI:'#ff2e63',ITA:'#3aaa5c',RUS:'#c81e6e',URS:'#c81e6e',SRB:'#e8967a',BEL:'#b58900',NED:'#ff9e80',CRO:'#a8dadc',ROU:'#c5a3ff',POL:'#ff7b7b',JPN:'#f4f4f2',CAN:'#ff8a80',BRA:'#a4ff4f',CHN:'#ff5a36',RSA:'#0f9d58',NZL:'#9e9e9e',DEN:'#e57373',AUT:'#f06292',BLR:'#4db6ac',UKR:'#ffe082',KAZ:'#80deea',GRE:'#64b5f6',NOR:'#5c6bc0',CHI:'#ef9a9a',ECU:'#fff176',YUG:'#ba68c8',SVK:'#4dd0e1',BUL:'#aed581',SLO:'#90caf9',LAT:'#bf360c',TUN:'#d4e157',IND:'#ffab40',MEX:'#66bb6a',HUN:'#8d6e63',FIN:'#b3e5fc',ISR:'#42a5f5',ZIM:'#ffca28',TPE:'#26a69a',KOR:'#7e57c2',THA:'#ab47bc',EGY:'#ff7043',PER:'#ec407a',URU:'#29b6f6',COL:'#fdd835',VEN:'#ffee58',PAR:'#d81b60',MAR:'#c62828',POR:'#2e7d32'};
const hueCache={};
const natColor=c=>{if(NAT_COL[c])return NAT_COL[c];if(hueCache[c])return hueCache[c];let h=0;for(const ch of String(c||'?'))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[c]=hsl2hex(h%360,45,62);};
const color=natColor;
const teamVar=c=>`--team:${natColor(c)}`;
const pnat=id=>PLAYERS[id]?.ioc||'';
const pcolor=id=>natColor(pnat(id));

/* ---------- lens: tour + draw (the masthead selects), then era + season as everywhere ---------- */
const state={tour:'M',disc:'S',era:'all',year:null,tab:'season',edition:null,match:null,nation:null,player:null,tourn:null,lens:'t',plens:'t',heat:'t',duelBy:'p',dA:null,dB:null,gridSort:'count',gridFind:'',gridMin:10,focusTeam:null,whole:false,find2:'',bracketRound:null};
const circs=()=>(state.tour==='all'?['M','W']:[state.tour]).map(t=>t+state.disc);
const inLens=c=>circs().includes(c);
const tourLabel=()=>state.tour==='M'?'ATP':state.tour==='W'?'WTA':'ATP & WTA';
const lensLabel=()=>`${tourLabel()} · ${state.disc==='S'?'singles':'doubles'}`;

/* seasons: every year with a title or an edition in the lens */
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){const map={};const get=y=>map[y]||(map[y]={year:y,editions:[],titles:[],matches:0});
  for(const e of Object.values(EDS)){if(!inLens(e.c))continue;const s=get(e.y);s.editions.push(e);s.matches+=e.n||0;}
  for(const c of CHAMPS){if(!inLens(c.c))continue;get(c.y).titles.push(c);}
  S=Object.keys(map).map(Number).sort((a,b)=>a-b).map(y=>map[y]);for(const s of S){s.editions.sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:0);s.titles.sort((a,b)=>(EDS[a.id]?.date||a.y+'-00')<(EDS[b.id]?.date||b.y+'-00')?-1:1);}
  byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1877;LAST_YEAR=S[S.length-1]?.year||2026;seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS=[["lawn","The lawn-tennis age",1877,1913,"Wimbledon from 1877, the US Championships from 1881, the Renshaw and Doherty brothers, the first Davis Cup in 1900; a game of amateurs on grass."],
["musketeers","Lenglen, Tilden and the Musketeers",1914,1945,"Suzanne Lenglen and Bill Tilden, the Four Musketeers at Roland-Garros, Helen Wills Moody, and Don Budge’s first Grand Slam in 1938."],
["amateur","The last amateur years",1946,1967,"Australia’s Davis Cup dynasty under Harry Hopman, Maureen Connolly’s Slam of 1953, Laver’s first in 1962; the professionals barred from the majors until 1968."],
["open","The Open era",1968,1984,"Professionals admitted from Roland-Garros 1968; Laver’s second Slam, Court, King and the founding of the WTA in 1973; Borg, Connors, Evert and Navrátilová; the tie-break and the last wooden racquets."],
["power","The power game",1985,1994,"Becker at seventeen, Lendl, Edberg, Graf’s Golden Slam of 1988 and Seles; graphite, carpet and the indoor season."],
["sampras","Sampras, Agassi and the Williams sisters",1995,2003,"Sampras’s fourteen majors, Agassi’s career Slam, Hingis, and the arrival of Venus and Serena Williams; the ATP Masters Series from 1990 comes of age."],
["big","The Big Three and Serena",2004,2015,"Federer, Nadal and Djokovic take almost every major between them; Serena Williams’s second act; Hawk-Eye from 2006 and the rise of hard courts."],
["reign","The long reign",2016,2021,"Djokovic and Nadal past twenty majors, Federer’s late Wimbledons, Osaka, Barty and Świątek; a tie-break in every final set from 2019."],
["new","The new generation",2022,2026,"Alcaraz and Sinner, Świątek and Sabalenka; the ten-point tie-break at 6–6 in the fifth at every major; the tour after the Big Three."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={lawn:'Lawn-tennis age',musketeers:'Lenglen, Tilden, Musketeers',amateur:'Last amateur years',open:'Open era',power:'Power game',sampras:'Sampras, Agassi, Williams',big:'Big Three, Serena',reign:'Long reign',new:'New generation'};
const ERA_TINY={lawn:'Lawn',musketeers:'Musketeers',amateur:'Amateur',open:'Open era',power:'Power',sampras:'Sampras',big:'Big Three',reign:'Reign',new:'New'};
const ERA_CHIPS={lawn:['Wimbledon 1877','US Championships 1881','Davis Cup 1900'],musketeers:['Lenglen, Tilden','Roland-Garros 1925','First Grand Slam 1938'],amateur:['Hopman’s Australia','Connolly’s Slam 1953','Amateurs only'],open:['Open tennis 1968','WTA founded 1973','The tie-break'],power:['Becker 1985','Golden Slam 1988','Graphite and carpet'],sampras:['Sampras 14 majors','Masters Series','Williams sisters'],big:['Federer, Nadal, Djokovic','Serena’s second act','Hawk-Eye 2006'],reign:['Twenty majors','Final-set tie-breaks','Osaka, Barty, Świątek'],new:['Alcaraz, Sinner','Świątek, Sabalenka','Ten-point tie-break']};
for(const e of ERAS)e.ball={label:'The game of the era',features:ERA_CHIPS[e.id],svg:ballSvg(e)};
function ballSvg(e){return `<svg viewBox="0 0 300 150" aria-hidden="true"><g transform="translate(90 78) rotate(-35)"><ellipse rx="40" ry="50" fill="none" stroke="#cfd3da" stroke-width="5"/><g stroke="#3a3f48" stroke-width="1.2"><path d="M-30-30v60M-18-42v84M-6-48v96M6-48v96M18-42v84M30-30v60M-38-24h76M-40-12h80M-40 0h80M-40 12h80M-38 24h76"/></g><path d="M-8 50l-6 58h28l-6-58z" fill="#cfd3da"/></g><g transform="translate(215 80)"><circle r="34" fill="var(--accent)" opacity=".92"/><path d="M-30-16c18-8 42-2 46 20M30 16c-18 8-42 2-46-20" fill="none" stroke="#07080a" stroke-width="2.5" opacity=".55"/></g><line x1="10" y1="140" x2="290" y2="140" stroke="#2e333d" stroke-width="2"/><text x="150" y="30" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||ERAS[ERAS.length-1];
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraTitles=()=>eraSeasons().flatMap(s=>s.titles);
const eraEditions=()=>eraSeasons().flatMap(s=>s.editions);
const eraLabel=()=>(state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates from the player-season rows ---------- */
let aggCache={};
function psRows(){const key='ps|'+circs().join()+'|'+state.era;if(aggCache[key])return aggCache[key];const [y0,y1]=eraRange();return aggCache[key]=PS.filter(r=>inLens(r.c)&&r.y>=y0&&r.y<=y1);}
function playerAgg(){const key='pa|'+circs().join()+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const r of psRows()){let a=map[r.p]||(map[r.p]={id:r.p,w:0,l:0,t:0,f:0,mj:0,hw:0,hl:0,cw:0,cl:0,gw:0,gl:0,iw:0,il:0,first:r.y,last:r.y,years:0,best:0,bestY:null});for(const k of ['w','l','t','f','mj','hw','hl','cw','cl','gw','gl','iw','il'])a[k]+=r[k]||0;a.first=Math.min(a.first,r.y);a.last=Math.max(a.last,r.y);a.years++;if(r.t>a.best||(r.t===a.best&&r.w>0&&a.bestY==null)){a.best=r.t;a.bestY=r.y;}}
  const out=Object.values(map).map(a=>({...a,p:a.w+a.l,rate:pct(a.w,a.w+a.l),nat:pnat(a.id),name:pname(a.id)}));return aggCache[key]=out;}
function natAgg(){const key='na|'+circs().join()+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const r of psRows()){const c=pnat(r.p);let a=map[c]||(map[c]={id:c,w:0,l:0,t:0,f:0,mj:0,players:new Set(),first:r.y,last:r.y,winners:new Set()});a.w+=r.w;a.l+=r.l;a.t+=r.t;a.f+=r.f;a.mj+=r.mj;a.players.add(r.p);if(r.t)a.winners.add(r.p);a.first=Math.min(a.first,r.y);a.last=Math.max(a.last,r.y);}
  const out=Object.values(map).map(a=>({...a,name:natName(a.id),p:a.w+a.l,rate:pct(a.w,a.w+a.l),np:a.players.size,nw:a.winners.size}));return aggCache[key]=out;}
const LENSES={t:['Titles','Tour-level titles won by the nation’s players in the lens.'],mj:['Majors','Grand Slam titles.'],w:['Match wins','Matches won by the nation’s players (from 1968).'],rate:['Win rate %','Wins divided by matches played. Minimum 200 matches.'],np:['Players','Players who appeared in the lens.'],nw:['Title winners','Different players who won a title.']};
const PLENSES={t:['Titles','Tour-level titles in the lens.'],mj:['Majors','Grand Slam titles.'],f:['Finals','Finals reached, won or lost.'],w:['Match wins','Matches won (results recorded from 1968).'],rate:['Win rate %','Wins divided by matches played. Minimum 100 matches.'],cw:['Clay wins','Match wins on clay.'],gw:['Grass wins','Match wins on grass.'],hw:['Hard-court wins','Match wins on hard courts.']};
const playerOrder=(a,b)=>b.t-a.t||b.mj-a.mj||b.f-a.f||b.w-a.w;
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const map={};for(const c of s.titles){for(const p of c.w){const a=map[p]||(map[p]={id:p,t:0,mj:0,f:0,w:0});a.t++;if(MAJORS.includes(c.t))a.mj++;a.f++;}for(const p of c.l){const a=map[p]||(map[p]={id:p,t:0,mj:0,f:0,w:0});a.f++;}}
  for(const r of PS){if(r.y!==s.year||!inLens(r.c))continue;const a=map[r.p]||(map[r.p]={id:r.p,t:0,mj:0,f:0,w:0});a.w+=r.w;a.l=(a.l||0)+r.l;}
  const ranked=Object.values(map).sort(playerOrder);const majors=s.titles.filter(c=>MAJORS.includes(c.t));return seasonBest[s.year]={best:ranked[0]||null,ranked,majors};}

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const b=state.whole?playerAgg().sort(playerOrder)[0]:champOf(byYear[state.year]).best;const c=b?pnat(b.id):null;acc=c?natColor(c):'#c8e06a';sec='#f4f4f2';ter='#0b120b';ink=onColor(acc);sel.options[0].textContent=`Champion’s colours · ${b?pname(b.id):'—'}`;}
  else if(SURF[v]){acc=SURF[v];sec='#f4f4f2';ter='#0b120b';ink=onColor(acc);}
  else{acc=natColor(v);sec='#f4f4f2';ter='#0b120b';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the serve (the opening, once per visit) ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-serve')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-serve','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2400);setTimeout(out,3300);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of titles by nation, year by year ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const c of s.titles){const share=1/Math.max(1,c.w.length);for(const p of c.w){const n=pnat(p);w[n]=(w[n]||0)+share;}tot+=1;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({d:c.best?.id,t:c.best?pnat(c.best.id):null,rec:c.best?`${c.best.t} title${c.best.t===1?'':'s'}${c.best.mj?' · '+c.best.mj+' major'+(c.best.mj===1?'':'s'):''}`:'',majors:c.majors,races:s.titles.length,matches:s.matches});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/(n-1);const x=i=>n===1?padL+(W-padL-padR)/2:padL+(i-i0)*slotW;
  const maxRaces=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.races));const thick=i=>plotH*(era?0.45+0.55*champs[i].races/maxRaces:0.14+0.86*Math.sqrt(champs[i].races/maxRaces));const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  for(const t of drawTeams){const up=[],down=[];let any=false;for(let i=i0;i<=i1;i++){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}if(!any)continue;
    if(n===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
    const dn=down.reverse();const d='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${natColor(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(natName(t))} · ${fmt(Math.round(tot))} titles ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} nations won a title</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.t?natColor(c.t):'#333'}" rx="1"><title>${years[i]} · ${c.d?pname(c.d)+' · '+c.rec:'—'}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%20===0&&y-years[0]>=8&&years[years.length-1]-y>=4),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${natColor(t)}"></i>${esc(natName(t))}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top5=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,5);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.races} titles${c.matches?' · '+fmt(c.matches)+' matches':''}${c.d?` · most titles <b style="color:var(--ink)">${esc(pname(c.d))}</b> ${c.rec}`:''}</div>${c.majors.slice(0,4).map(m=>`<div class="row"><span><i class="sw" style="background:${pcolor(m.w[0])}"></i>${esc(TOURN[m.t]?.n||m.t)}</span><span>${esc(pnames(m.w))}</span></div>`).join('')}${top5.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${natColor(t)}"></i>${esc(natName(t))}</span><span>${totals[i]?Math.round(p/totals[i]*100):0}%</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the year’s titles by nation · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
