'use strict';
/* ============================================================
   APEX — an ode to the Test match. Application.
   Everything below reads from the embedded archive; nothing writes to it.
   Same grammar as the motorsport odes: River · Grounds · Stage.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
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

/* ---------- nations ---------- */
const TEN=A.teams, teamBy=Object.fromEntries(TEN.map(t=>[t.name,t])), TEN_NAMES=TEN.map(t=>t.name);
const OPP_COLOURS={'British & Irish Lions':'#e75863','Japan':'#f48f9a','Fiji':'#ecebe6','Samoa':'#618fff','Tonga':'#d65b5e','Georgia':'#a86572','Namibia':'#85a8ed','USA':'#b482a2','Portugal':'#d65965','South America':'#d6ba82','NZ Cavaliers':'#8faba3','World Invitation':'#c09aca','Canada':'#ef8d81','Romania':'#ecce59','Uruguay':'#8bcddd','Spain':'#c85a5b','Chile':'#d9705f','Germany':'#c9c2a0','Russia':'#c86a6a','Paraguay':'#d05a5a','Brazil':'#d7c95a','Zimbabwe':'#e0b45a','Czechia':'#7a8fd0','Morocco':'#c95c5c','Netherlands':'#f0a04b','Tunisia':'#d66a6a','Madagascar':'#6fb08a','Croatia':'#d46a7a','Ivory Coast':'#f0a860','Great Britain':'#9aa7d6'};
const CODES={'British & Irish Lions':'LIO','South America':'SAM','NZ Cavaliers':'CAV','World Invitation':'WXV','Great Britain':'GBR','USA':'USA','Czechia':'CZE','Ivory Coast':'CIV','Netherlands':'NED','Germany':'GER','Japan':'JPN','Fiji':'FIJ','Samoa':'SAM','Tonga':'TGA','Georgia':'GEO','Namibia':'NAM','Portugal':'POR','Canada':'CAN','Romania':'ROU','Uruguay':'URU','Spain':'ESP','Chile':'CHI','Russia':'RUS','Paraguay':'PAR','Brazil':'BRA','Zimbabwe':'ZIM','Morocco':'MAR','Tunisia':'TUN','Madagascar':'MAD','Croatia':'CRO'};
const hueCache={};
const NAT={};
function nat(n){if(NAT[n])return NAT[n];const t=teamBy[n];let color=t?t.accent:OPP_COLOURS[n];if(!color){let h=0;for(const ch of String(n))h=(h*31+ch.charCodeAt(0))>>>0;color=hsl2hex(h%360,35,60);}
  return NAT[n]={id:n,name:n,code:t?t.code:CODES[n]||n.replace(/[^A-Za-z]/g,'').slice(0,3).toUpperCase(),color,secondary:t?t.secondary:mixHex(color,'#f4f4f2',.5),kit:t?t.kit:color,trim:t?t.trim:color,nickname:t?t.nickname:'',tag:t?t.tag:'',titles:t?t.titles:[],ten:!!t};}
const color=n=>nat(n).color, code=n=>nat(n).code, tn=n=>n;
const teamVar=n=>`--team:${color(n)}`;

/* ---------- matches, seasons, grounds ---------- */
const isHomeFor=(m,side)=>m.country===side||(side==='Ireland'&&m.country==='Northern Ireland');
/* A side is counted for a match only where the archive recognises it for that side (the one exception is France v South Africa, 1907, recognised by France alone). */
const plays=(m,side)=>(m.home===side||m.away===side)&&(!teamBy[side]||m.eligible.includes(side));
const MATCHES=A.matches.map(m=>{const as=m.as_;const draw=m.hs===as;const winner=draw?null:m.hs>as?m.home:m.away;const loser=draw?null:winner===m.home?m.away:m.home;
  return {...m,as,draw,winner,loser,margin:Math.abs(m.hs-as),total:m.hs+as,recorded:!m.stadium.startsWith('ground-not-recorded'),points:m.scoreUnit!=='goals'};});
const byId=MATCHES;
const S=[];{const map={};for(const m of MATCHES){(map[m.year]||(map[m.year]={year:m.year,matches:[]})).matches.push(m);}for(const y of Object.keys(map).map(Number).sort((a,b)=>a-b))S.push(map[y]);}
const byYear=Object.fromEntries(S.map(s=>[s.year,s]));
const FIRST_YEAR=S[0].year,LAST_YEAR=S[S.length-1].year;
const GROUNDS={};for(const m of MATCHES){if(!m.recorded)continue;let g=GROUNDS[m.stadium]||(GROUNDS[m.stadium]={id:m.stadium,names:{},cities:{},countries:{}});g.names[m.venue]=(g.names[m.venue]||0)+1;if(m.city)g.cities[m.city]=(g.cities[m.city]||0)+1;if(m.country)g.countries[m.country]=(g.countries[m.country]||0)+1;}
for(const g of Object.values(GROUNDS)){const best=o=>Object.entries(o).sort((a,b)=>b[1]-a[1]||a[0].length-b[0].length)[0]?.[0]||'';g.name=Object.keys(g.names).sort((a,b)=>a.replace(/[^A-Za-z]/g,'').length-b.replace(/[^A-Za-z]/g,'').length||a.length-b.length)[0].replace(/[\s.\-]+$/,'');g.city=best(g.cities);g.country=best(g.countries);}
const groundName=id=>GROUNDS[id]?.name||(id.startsWith('ground-not-recorded')?'Ground not recorded':id);

/* ---------- players and coaches, linked to archive ids ---------- */
const perspIdx={};for(const t of new Set(MATCHES.flatMap(m=>[m.home,m.away])))perspIdx[t]=MATCHES.filter(m=>plays(m,t)).map(m=>m.id);
const HF=A.historyFields||['match','position','scoring','tries','shirt','bench'];const unpackH=r=>Array.isArray(r)?Object.fromEntries(HF.map((k,i)=>[k,r[i]])):r;
const PLAYERS=A.players.map(p=>({...p,games:p.history.map(unpackH).map(h=>{const mid=perspIdx[p.team]?.[h.match]??null;const m=mid!=null?byId[mid]:null;return {...h,mid,date:h.date||m?.date,opponent:h.opponent||(m?(m.home===p.team?m.away:m.home):'')};}).filter(h=>h.mid!=null)}));
const fullNameOf=p=>{if(!p.fullName||p.fullName===p.name)return '';const parts=p.name.split(' ');const sur=parts.slice(1).join(' ');if(p.fullName===parts[0])return '';return sur&&p.fullName.endsWith(sur)?p.fullName:p.fullName+(sur?' '+sur:'');};
const playerBy=Object.fromEntries(PLAYERS.map(p=>[p.id,p]));
const COACHES=A.coaches.map(c=>({...c,matches:c.matchIds.map(i=>byId[i]).filter(Boolean)}));
const coachBy=Object.fromEntries(COACHES.map(c=>[c.id,c]));
const gamesByMatch={};for(const p of PLAYERS)for(const g of p.games){(gamesByMatch[g.mid]||(gamesByMatch[g.mid]=[])).push({p,g});}

/* ---------- eras ---------- */
const PTS=y=>({try:y>=1992?5:y>=1971?4:3,con:2,pen:3,drop:y>=1948?3:4,ptry:y>=2017?7:(y>=1992?5:y>=1971?4:3)});
const ERAS=[["origins","Early internationals",1871,1913,"The earliest internationals: the Home Nations from 1871, the first touring sides from the southern hemisphere, France from 1906. Before 1886 the archive counts goals rather than points."],
["interwar","Tours & interwar years",1914,1948,"Long tours by sea, the Five Nations resumed after each war, and international schedules with long gaps; the Springboks and All Blacks meet only on tour."],
["postwar","Post-war rugby",1949,1969,"Annual championships in Europe, tours of months rather than weeks, and the drop goal reduced to three points in 1948."],
["transition","Changing game",1970,1986,"The try rises to four points in 1971; South Africa’s isolation deepens; the first talk of a World Cup."],
["worldcup","World Cup beginnings",1987,1995,"The first three men’s Rugby World Cups, the five-point try from 1992, and the end of amateurism in 1995."],
["pro","Professional era",1996,2011,"The Tri Nations, the Six Nations with Italy from 2000, expanding November and June windows, and four more World Cups."],
["modern","Modern internationals",2012,2026,"The Rugby Championship with Argentina, the seven-point penalty try from 2017, and the most recent completed internationals."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={origins:'Early internationals',interwar:'Tours · interwar',postwar:'Post-war',transition:'Changing game',worldcup:'World Cup begins',pro:'Professional',modern:'Modern'};
for(const e of ERAS){const a=PTS(e.from),b=PTS(e.to);const chip=(k,l)=>a[k]===b[k]?`${l} ${a[k]}`:`${l} ${a[k]} → ${b[k]}`;const feats=[e.from<1886?'Goals decide before 1886':null,chip('try','Try'),chip('con','Conversion'),chip('pen','Penalty'),chip('drop','Drop goal'),e.to>=2017?`Penalty try ${b.ptry}`:null].filter(Boolean);
  e.ball={label:'Scoring values of the era',features:feats,svg:ballSvg(e)};}
function ballSvg(e){const id='g'+e.id;return `<svg viewBox="0 0 300 150" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" x2="1"><stop offset="0" stop-color="var(--accent)" stop-opacity=".9"/><stop offset="1" stop-color="var(--accent)" stop-opacity=".35"/></linearGradient></defs>
  <path d="M60 140V38M100 140V38M60 78h40" stroke="#cfd3da" stroke-width="5" stroke-linecap="round" fill="none"/><path d="M200 140V38M240 140V38M200 78h40" stroke="#cfd3da" stroke-width="5" stroke-linecap="round" fill="none" opacity=".35"/>
  <line x1="10" y1="140" x2="290" y2="140" stroke="#2e333d" stroke-width="2"/>
  <g transform="translate(150 70) rotate(-28)"><ellipse rx="46" ry="27" fill="url(#${id})" stroke="var(--accent)" stroke-width="2.5"/><path d="M-30 0h60M-18-8v16M-6-9v18M6-9v18M18-8v16" stroke="#07080a" stroke-width="2.5" stroke-linecap="round" opacity=".7"/></g>
  <text x="150" y="128" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to);

/* ---------- state ---------- */
const state={era:'all',year:LAST_YEAR,tab:'season',match:null,nation:null,player:null,ground:null,coach:null,lens:'wins',plens:'caps',heat:'rate',duelBy:'n',dA:null,dB:null,gridSort:'count',gridFind:'',gridMin:3,focusTeam:null,whole:false,find2:''};
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraMatches=()=>eraSeasons().flatMap(s=>s.matches);
const eraLabel=()=>state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era));

/* ---------- aggregates ---------- */
function natStats(ms){const map={};for(const m of ms){for(const side of [m.home,m.away]){if(!plays(m,side))continue;const opp=side===m.home?m.away:m.home;const pf=side===m.home?m.hs:m.as,pa=side===m.home?m.as:m.hs;let a=map[side]||(map[side]={id:side,p:0,w:0,d:0,l:0,pf:0,pa:0,np:0,home:0,hw:0,first:m.year,last:m.year,grounds:new Set(),opps:new Set(),cups:0,big:null,streak:0,best:0,cur:0});
  a.p++;if(m.draw){a.d++;a.cur=0;}else if(m.winner===side){a.w++;a.cur++;if(a.cur>a.best)a.best=a.cur;}else{a.l++;a.cur=0;}if(m.points){a.pf+=pf;a.pa+=pa;a.np++;if(m.winner===side&&(!a.big||m.margin>a.big.margin))a.big=m;}if(isHomeFor(m,side)){a.home++;if(m.winner===side)a.hw++;}a.first=Math.min(a.first,m.year);a.last=Math.max(a.last,m.year);if(m.recorded)a.grounds.add(m.stadium);a.opps.add(opp);if(m.stage==='Final'&&m.winner===side)a.cups++;}}
  return Object.values(map).map(a=>({...a,wins:a.w,rate:pct(a.w,a.p),ppm:a.np?Math.round(a.pf/a.np*10)/10:0,margin:a.np?Math.round((a.pf-a.pa)/a.np*10)/10:0,homeRate:pct(a.hw,a.home),streak:a.best}));}
const LENSES={wins:['Wins','Test matches won.'],rate:['Win rate %','Wins divided by all Tests, draws included. Minimum 10 Tests in the lens.'],p:['Tests','Matches played in the lens.'],pf:['Points for','Points scored; matches scored in goals (before 1886) are excluded.'],ppm:['Points per Test','Points for divided by points-era Tests. Minimum 10 Tests.'],margin:['Average margin','Points for minus points against, per points-era Test. Minimum 10 Tests.'],cups:['World Cups','Finals won.'],streak:['Longest winning run','Consecutive Test wins inside the lens.']};
const PLENSES={caps:['Caps','Test appearances, career totals as published.'],tries:['Tries','Career Test tries as published.'],points:['Points','Career Test points as published; unavailable for some careers.']};
const bestRecord=(ms,minP)=>{const st=natStats(ms);const maxP=Math.max(0,...st.map(a=>a.p));const min=Math.min(minP,maxP);return st.filter(a=>a.p>=min).sort((a,b)=>b.rate-a.rate||b.w-a.w||b.margin-a.margin)[0]||null;};
const seasonBest={};function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const b=bestRecord(s.matches,3);const final=s.matches.find(m=>m.stage==='Final');return seasonBest[s.year]={best:b,cup:final?{winner:final.winner,final}:null};}

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const n=state.whole?bestRecord(eraMatches(),10)?.id:champOf(byYear[state.year]).best?.id;const t=n?nat(n):null;acc=t?t.color:'#5cd4a1';sec=t?t.secondary:'#e4bb65';ter=t?t.kit:'#006341';ink=onColor(acc);sel.options[0].textContent=`Best record’s colours · ${n||'—'}`;}
  else{const t=nat(v);acc=t.color;sec=t.secondary;ter=t.kit;ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- kick-off (the opening, once per visit) ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-kickoff')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-kickoff','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2300);setTimeout(out,3300);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const m of s.matches){if(m.draw){if(plays(m,m.home))w[m.home]=(w[m.home]||0)+.5;if(plays(m,m.away))w[m.away]=(w[m.away]||0)+.5;}else if(plays(m,m.winner))w[m.winner]=(w[m.winner]||0)+1;tot+=1;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({d:c.best?.id,t:c.best?.id,rec:c.best?`${c.best.w}–${c.best.l}–${c.best.d}`:'',cup:c.cup?.winner,races:s.matches.length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  const i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1,n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/(n-1);const x=i=>n===1?padL+(W-padL-padR)/2:padL+(i-i0)*slotW;
  const maxRaces=Math.max(...champs.slice(i0,i1+1).map(c=>c.races));const thick=i=>plotH*(era?0.45+0.55*champs[i].races/maxRaces:0.22+0.78*champs[i].races/maxRaces);const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  for(const t of drawTeams){const up=[],down=[];let any=false;for(let i=i0;i<=i1;i++){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}if(!any)continue;
    if(n===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
    const dn=down.reverse();const d='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(Math.round(tot))} wins ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} sides won a Test</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const slot=(nxt?x(years.findIndex(y=>y>=nxt.from)):W)-xx;const label=ERA_SHORT[e.id]||e.name;const fits=label.length*6.6+8<=slot;eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${champs[i].t?color(champs[i].t):'#333'}" rx="1"><title>${years[i]} · best record ${esc(champs[i].d||'—')} ${champs[i].rec}${champs[i].cup?' · World Cup: '+esc(champs[i].cup):''}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[1871,1890,1910,1930,1950,1970,1990,2010,2026];
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top5=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,5);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.races} Tests · best record <b style="color:var(--ink)">${esc(c.d||'—')}</b> ${c.rec}${c.cup?` · <b style="color:var(--ink)">${esc(c.cup)}</b> world champions`:''}</div>${top5.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${totals[i]?Math.round(p/totals[i]*100):0}%</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of all Tests won that year · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
