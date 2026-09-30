'use strict';
/* ============================================================
   APEX — an ode to the international game (cricket). Application.
   Same grammar as the other odes: River · Grounds · Stage.
   Reads the core archive (results, player-season figures, registers, titles);
   scorecards arrive per season from DETAILS (embedded offline, fetched on the site).
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

/* ---------- sides ---------- */
const TEAMS=A.teams, MAJOR=Object.keys(TEAMS).filter(k=>TEAMS[k].major);
const hueCache={};
const nat=n=>{const t=TEAMS[n];if(t)return {id:n,name:t.n||n,code:t.abbr||n.slice(0,3).toUpperCase(),color:t.c,secondary:t.c2||t.c,major:!!t.major,flag:t.flag};if(hueCache[n])return hueCache[n];let h=0;for(const ch of String(n))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[n]={id:n,name:n,code:n.replace(/[^A-Za-z]/g,'').slice(0,3).toUpperCase(),color:hsl2hex(h%360,35,60),secondary:'#cfd3da',major:false};};
const color=n=>nat(n).color, code=n=>nat(n).code;
const teamVar=n=>`--team:${color(n)}`;
const FORMATS=['Test','ODI','T20I'];

/* ---------- matches ---------- */
const MATCHES=A.games.map(m=>({...m,year:m.y,home:m.teams[0],away:m.teams[1],draw:m.result==='draw'||m.result==='tie',nr:m.result==='no result',loser:m.winner?(m.teams[0]===m.winner?m.teams[1]:m.teams[0]):null,recorded:!!(m.v&&A.venues[m.v]&&!A.venues[m.v].locationOnly),marginN:(()=>{const mm=/^(\d+)\s+(run|wicket)/.exec(m.margin||'');return mm?{n:+mm[1],by:mm[2]}:null;})()}));
const byId=Object.fromEntries(MATCHES.map(m=>[m.id,m]));
const VENUES=A.venues; const groundName=id=>VENUES[id]?.n||'Ground not recorded';
const PLAYERS=A.players; const pname=id=>PLAYERS[id]?.n||id;
const PS=A.ps.map(r=>Object.fromEntries(A.psFields.map((k,i)=>[k,r[i]])));
const CHAMPS=A.champions;

/* ---------- lens: gender + format (the masthead selects), then era + season as everywhere ---------- */
const state={gender:'M',fmt:'all',era:'all',year:null,tab:'season',match:null,nation:null,player:null,ground:null,lens:'wins',plens:'runs',heat:'rate',duelBy:'n',dA:null,dB:null,gridSort:'count',gridFind:'',gridMin:5,focusTeam:null,whole:false,find2:''};
const inLens=m=>m.g===state.gender&&(state.fmt==='all'||m.f===state.fmt);
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){const map={};for(const m of MATCHES){if(!inLens(m))continue;(map[m.year]||(map[m.year]={year:m.year,matches:[]})).matches.push(m);}S=Object.keys(map).map(Number).sort((a,b)=>a-b).map(y=>map[y]);byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1877;LAST_YEAR=S[S.length-1]?.year||2026;seasonBest={};riverModel=null;if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS=[["origins","The first Tests",1877,1914,"Test cricket only, from the first match at Melbourne in 1877: timeless and multi-day Tests, the Ashes from 1882, South Africa's entry in 1889."],
["interwar","Between the wars",1920,1947,"Bradman’s decades and Bodyline; West Indies, New Zealand and India join Test cricket."],
["postwar","Post-war",1948,1970,"Tours by air, the tied Test of 1960, Pakistan's entry, and South Africa's last Test before isolation in 1970."],
["oneday","The one-day age",1971,1991,"The first one-day international in 1971, World Cups in 1975, 1979, 1983 and 1987, Sri Lanka's first Test in 1982."],
["colour","Coloured clothing",1992,2004,"White balls and coloured clothing, South Africa's return, Zimbabwe and Bangladesh at Test level."],
["t20","The T20 revolution",2005,2015,"The first T20 international in 2005, T20 World Cups from 2007, decision reviews, franchise leagues reshaping the calendar."],
["three","Three formats",2016,2026,"The World Test Championship, Afghanistan and Ireland at Test level from 2018, the women's game at full strength across all three formats."]].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_SHORT={origins:'First Tests',interwar:'Between the wars',postwar:'Post-war',oneday:'One-day age',colour:'Coloured clothing',t20:'T20 revolution',three:'Three formats'}
const ERA_TINY={origins:'Origins',interwar:'Interwar',postwar:'Post-war',oneday:'One-day',colour:'Colour',t20:'T20',three:'3 formats'};
const ERA_CHIPS={origins:['Tests only','Ashes from 1882','Timeless Tests'],interwar:['Tests only','Bodyline 1932–33','Three new Test nations'],postwar:['Tests only','Tied Test 1960','Isolation from 1970'],oneday:['ODI from 1971','World Cup from 1975','Sri Lanka Tests 1982'],colour:['White ball, coloured kit','South Africa back, 1991','Zimbabwe, Bangladesh Tests'],t20:['T20I from 2005','T20 World Cup 2007','Decision reviews'],three:['World Test Championship','Afghanistan, Ireland Tests 2018','Women’s game at full strength']};
for(const e of ERAS)e.ball={label:'The game of the era',features:ERA_CHIPS[e.id],svg:ballSvg(e)};
function ballSvg(e){return `<svg viewBox="0 0 300 150" aria-hidden="true"><g stroke="#cfd3da" stroke-width="5" stroke-linecap="round" fill="none"><path d="M64 138V60M80 138V60M96 138V60"/><path d="M62 58h20M78 58h20" stroke-width="4"/></g><g transform="translate(200 80)"><circle r="40" fill="var(--accent)" opacity=".9"/><path d="M-40 0a40 40 0 0 1 80 0" fill="none" stroke="#07080a" stroke-width="2.5" opacity=".6" transform="rotate(-30)"/><path d="M-40 0a40 40 0 0 0 80 0" fill="none" stroke="#07080a" stroke-width="2.5" opacity=".6" transform="rotate(-30)"/><path d="M-36-18 -34-14M-30-27 -27-23M-22-33 -20-29M-13-37 -12-33M-3-39 -3-35M7-39 7-35M17-37 16-33M26-33 24-29M33-27 30-23" stroke="#07080a" stroke-width="2" opacity=".5"/></g><line x1="10" y1="140" x2="290" y2="140" stroke="#2e333d" stroke-width="2"/><text x="150" y="30" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="10" letter-spacing="2" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||ERAS[ERAS.length-1];
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraMatches=()=>eraSeasons().flatMap(s=>s.matches);
const lensLabel=()=>`${state.gender==='M'?'Men':'Women'} · ${state.fmt==='all'?'all formats':state.fmt}`;
const eraLabel=()=>(state.era==='all'?`All eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
const resClass=(m,side)=>m.nr?'N':m.draw?'D':m.winner===side?'W':'L';
function natStats(ms){const map={};for(const m of ms){for(const side of m.teams){const opp=side===m.teams[0]?m.teams[1]:m.teams[0];let a=map[side]||(map[side]={id:side,p:0,w:0,l:0,d:0,nr:0,first:m.year,last:m.year,grounds:new Set(),opps:new Set(),cups:0,big:null,cur:0,best:0,hi:0,byF:{}});
  a.p++;const r=resClass(m,side);if(r==='W'){a.w++;a.cur++;if(a.cur>a.best)a.best=a.cur;if(m.marginN&&(!a.big||(m.marginN.by==='run'&&m.marginN.n>(a.big.marginN?.by==='run'?a.big.marginN.n:0))))a.big=m;}else if(r==='L'){a.l++;a.cur=0;}else if(r==='D'){a.d++;a.cur=0;}else a.nr++;
  const f=a.byF[m.f]||(a.byF[m.f]={p:0,w:0,l:0,d:0});f.p++;if(r==='W')f.w++;else if(r==='L')f.l++;else if(r==='D')f.d++;
  for(const sc of m.sc||[])if(sc[0]===side&&!sc[6]&&sc[1]>a.hi)a.hi=sc[1];
  a.first=Math.min(a.first,m.year);a.last=Math.max(a.last,m.year);if(m.recorded)a.grounds.add(m.v);a.opps.add(opp);}}
  const cupsOf=id=>CHAMPS.filter(c=>c.g===state.gender&&c.w.includes(id)&&inEraYear(c.y)&&(state.fmt==='all'||c.f===state.fmt)).length;
  return Object.values(map).map(a=>({...a,wins:a.w,rate:pct(a.w,a.p),streak:a.best,cups:cupsOf(a.id),decided:a.p-a.nr}));}
const LENSES={wins:['Wins','Matches won in the lens.'],rate:['Win rate %','Wins divided by all matches, draws and no-results included. Minimum 10 matches.'],p:['Matches','Matches played in the lens.'],cups:['ICC titles','World Cups, T20 World Cups, Champions Trophies and World Test Championships won.'],streak:['Longest winning run','Consecutive wins inside the lens.'],hi:['Highest total','Highest innings total in the lens, from the recorded scorecards.']};
const PLENSES={runs:['Runs','Runs scored, from the recorded player-season figures.'],wickets:['Wickets','Wickets taken.'],games:['Matches','Matches with recorded figures.'],hundreds:['Hundreds','Centuries.'],fifties:['Fifties','Half-centuries, excluding centuries.'],batavg:['Batting average','Runs per dismissal. Minimum 20 innings.'],bowlavg:['Bowling average','Runs conceded per wicket, lowest first. Minimum 20 wickets.'],catches:['Catches','Catches in the field.']};
const recordOrder=(a,b)=>(b.w-b.l)-(a.w-a.l)||b.rate-a.rate||b.w-a.w;
const rankRecords=(ms,minP)=>{const st=natStats(ms);const maxP=Math.max(0,...st.map(a=>a.p));const min=Math.min(Math.max(minP,Math.round(maxP*0.4)),maxP);return st.filter(a=>a.p>=min).sort(recordOrder);};
const bestRecord=(ms,minP)=>rankRecords(ms,minP)[0]||null;
let seasonBest={};function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const b=bestRecord(s.matches,3);const cups=CHAMPS.filter(c=>c.y===s.year&&c.g===state.gender&&(state.fmt==='all'||c.f===state.fmt));return seasonBest[s.year]={best:b,cups};}

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const n=state.whole?bestRecord(eraMatches(),10)?.id:champOf(byYear[state.year]).best?.id;const t=n?nat(n):null;acc=t?t.color:'#007749';sec=t?t.secondary:'#FFB81C';ter='#0b1713';ink=onColor(acc);sel.options[0].textContent=`Best record’s colours · ${n||'—'}`;}
  else{const t=nat(v);acc=t.color;sec=t.secondary;ter='#0b1713';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the toss (the opening, once per visit) ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem('apex-toss')==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem('apex-toss','1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2400);setTimeout(out,3300);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const m of s.matches){if(m.nr)continue;if(m.draw){w[m.home]=(w[m.home]||0)+.5;w[m.away]=(w[m.away]||0)+.5;}else if(m.winner)w[m.winner]=(w[m.winner]||0)+1;tot+=1;}
    for(const t in w){if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({d:c.best?.id,t:c.cups[0]?.w[0]||c.best?.id,rec:c.best?`${c.best.w}–${c.best.l}–${c.best.d}`:'',cups:c.cups,races:s.matches.length});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/(n-1);const x=i=>n===1?padL+(W-padL-padR)/2:padL+(i-i0)*slotW;
  const maxRaces=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.races));const thick=i=>plotH*(era?0.45+0.55*champs[i].races/maxRaces:0.18+0.82*Math.sqrt(champs[i].races/maxRaces));const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  for(const t of drawTeams){const up=[],down=[];let any=false;for(let i=i0;i<=i1;i++){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}if(!any)continue;
    if(n===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
    const dn=down.reverse();const d='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(Math.round(tot))} wins ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} sides won a match</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.cups.length?color(c.cups[0].w[0]):c.t?mixHex(color(c.t),'#12141a',.45):'#333'}" rx="1"><title>${years[i]} · ${c.cups.length?c.cups.map(cp=>cp.label+': '+cp.w.join(' & ')).join(' · '):'best record '+esc(c.d||'—')+' '+c.rec}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=era||n<=40?years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1):[years[0]].concat(years.filter(y=>y%20===0&&y-years[0]>=8&&years[years.length-1]-y>=4),[years[years.length-1]]);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span>${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const top5=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,5);const c=champs[i];
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${c.races} matches · best record <b style="color:var(--ink)">${esc(c.d||'—')}</b> ${c.rec}${c.cups.map(cp=>` · <b style="color:var(--ink)">${esc(cp.w.join(' & '))}</b> ${esc(cp.label.replace(/^(Men|Women)’s /,''))}`).join('')}</div>${top5.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${totals[i]?Math.round(p/totals[i]*100):0}%</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of decided matches won that year · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){setSeason(+hit.dataset.y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
