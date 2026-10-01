'use strict';
/* ============================================================
   APEX — an ode to the World Cup. Application.
   Same grammar as the other odes: River · Stage · Grounds.
   The archive travels whole: every tournament, every match with its sheet where the sources hold one, every player.
   ============================================================ */
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const A=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const LIGHT_KEY='apex-whistle';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number.isInteger(n)?n.toLocaleString('en'):(Math.round(n*100)/100).toString();
const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};
const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};
const ordinal=n=>n+(['th','st','nd','rd'][(n%100>10&&n%100<14)?0:Math.min(n%10,4)%4]||'th');
const longDate=iso=>{if(!iso)return '';const d=new Date(iso+'T00:00:00Z');return isNaN(d)?iso:d.toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'});};

/* ---------- the archive ---------- */
const yspan=o=>o.first===o.last?String(o.first):`${o.first}–${o.last}`;
const TEAMS=A.teams, PL=A.players, ST=A.stadiums, REF=A.referees, MAN=A.managers, MAP=A.map, SL=A.stageLabel;
const SEX_NAME={M:'Men’s World Cup',W:'Women’s World Cup'}, SEX_SHORT={M:'men’s',W:'women’s'};
const pname=id=>PL[id]?.n||String(id).replace(/^X-/,'').replace(/-/g,' ');
const sname=id=>ST[id]?.name||'';
const MF=A.matchFields;
const MATCHES=A.matches.map(r=>{const m=Object.fromEntries(MF.map((k,i)=>[k,r[i]]));m.d=A.details[m.id]||{g:[],l:null,b:[],s:[],p:[]};m.year=m.y;m.ko=!['group','group2','final-round'].includes(m.stage);return m;});
const mById=Object.fromEntries(MATCHES.map(m=>[m.id,m]));
const TOUR=A.tournaments.map(t=>({...t,year:t.y,matches:[]}));const tById=Object.fromEntries(TOUR.map(t=>[t.id,t]));
for(const m of MATCHES){tById[m.t].matches.push(m);}
for(const t of TOUR)t.matches.sort((a,b)=>a.date.localeCompare(b.date)||(a.time||'').localeCompare(b.time||'')||a.id.localeCompare(b.id));
const proj=p=>[(p[1]+180)*3,(90-p[2])*3];
const STAGE_RANK={group:1,group2:2,'final-round':3,r32:4,r16:5,qf:6,sf:7,'3rd':8,final:9};
const stageLabel=(m)=>m.stage==='group'||m.stage==='group2'?(m.group||SL[m.stage]):SL[m.stage]||m.stage;
const scoreOf=m=>`${m.hs}–${m.as}`;
const resultLine=m=>`${scoreOf(m)}${m.et?' a.e.t.':''}${m.ph!=null?` · ${m.ph}–${m.pa} pens`:''}`;
const winnerName=m=>m.winner==='h'?m.home:m.winner==='a'?m.away:null;
const loserName=m=>m.winner==='h'?m.away:m.winner==='a'?m.home:null;
const sideOf=(m,team)=>m.home===team?'h':m.away===team?'a':null;
const resFor=(m,team)=>{const s=sideOf(m,team);if(!s)return null;const gf=s==='h'?m.hs:m.as,ga=s==='h'?m.as:m.hs;return gf>ga?'W':gf<ga?'L':'D';};
const minuteLabel=(mm,ss)=>`${mm}${ss?'+'+ss:''}’`;
const squadOf=(t,team)=>(A.squads[t]||{})[team]||[];

/* ---------- colours ---------- */
const NAT_COL=A.colours||{};
const hueCache={};
const color=n=>{if(NAT_COL[n])return NAT_COL[n];if(hueCache[n])return hueCache[n];let h=0;for(const ch of String(n||'?'))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[n]=hsl2hex(h%360,38,66);};
const teamVar=n=>`--team:${color(n)}`;

/* ---------- lens: the competition (men's or women's), then era + tournament as everywhere ---------- */
const state={sex:'M',era:'all',year:null,tab:'season',match:null,player:null,team:null,ground:null,host:null,lens:'titles',plens:'goals',glens:'count',heat:'wins',duelBy:'t',dA:null,dB:null,focusTeam:null,whole:false,find2:'',gridFind:'',gridSort:'matches',metric:'wins',showAll:false,mstage:null};
let S=[],byYear={},FIRST_YEAR=0,LAST_YEAR=0;
function rebuildSeasons(){S=[];for(const t of TOUR){if(t.sex!==state.sex)continue;S.push({year:t.year,t,matches:t.matches,teams:t.teams,cancelled:false});}byYear=Object.fromEntries(S.map(s=>[s.year,s]));FIRST_YEAR=S[0]?.year||1930;LAST_YEAR=S[S.length-1]?.year||A.lastYear[state.sex];seasonBest={};riverModel=null;aggCache={};if(!byYear[state.year])state.year=LAST_YEAR;}
const ERAS_ALL={M:[["founding","The first three",1930,1938,"Uruguay’s invitation of 1930, thirteen teams and a final against Argentina in the new Centenario; Italy at home in 1934, a straight knockout settled by a replay; Italy again in France in 1938, Leônidas and the Austrian withdrawal. The trophy was Jules Rimet’s, and the war took the next two."],
["postwar","The Maracanazo to Mexico",1950,1970,"Brazil built the Maracanã and lost the final round to Uruguay; the Miracle of Bern, West Germany over Hungary’s golden team; Sweden 1958 and a seventeen-year-old Pelé; Chile 1962 and Garrincha; England’s only title at Wembley, Hurst’s three; Mexico 1970, the first in colour, Brazil’s third and the Jules Rimet Trophy kept for good."],
["expansion","Sixteen to twenty-four",1974,1994,"Cruyff’s Netherlands beaten by Beckenbauer’s hosts in Munich; Argentina at home in 1978; Spain 1982, twenty-four teams and Rossi’s six; Maradona’s Mexico, the hand and the run; Italia ’90, the lowest-scoring of all; USA ’94, the first final without a goal and Baggio’s penalty over the bar."],
["thirtytwo","Thirty-two teams",1998,2022,"France at home with Zidane’s two headers; Korea and Japan, the first in Asia and Brazil’s fifth; Zidane’s last act in Berlin and Italy on penalties; Spain’s tiki-taka in Johannesburg; the 7–1 in Belo Horizonte and Götze’s volley; France again in Moscow; Qatar in winter, 3–3 and Messi’s shoot-out."],
["fortyeight","Forty-eight teams",2026,2026,"Three hosts, sixteen cities, twelve groups, a round of 32 and 104 matches: the largest World Cup yet, across the United States, Canada and Mexico, with Spain beating Argentina after extra time in East Rutherford."]],
W:[["founding","The first five",1991,2007,"China 1991 and the United States’ first title, Michelle Akers’ ten goals; Norway in Sweden in 1995; the Rose Bowl in 1999 with 90,000 watching Brandi Chastain’s penalty; 2003 moved to the United States at short notice and Germany’s first; China again in 2007 and Germany’s second, without conceding a goal."],
["growth","Twenty-four teams",2011,2019,"Japan’s penalties over the United States in Frankfurt, months after the tsunami; Canada 2015 with twenty-four teams, Carli Lloyd’s hat-trick in sixteen minutes; France 2019, the United States back to back and Megan Rapinoe’s Golden Boot."],
["thirtytwo","Thirty-two teams",2023,2023,"Australia and New Zealand across ten grounds and two time zones, thirty-two teams for the first time, Spain’s first title over England in Sydney; the record here is Wikipedia’s — results and grounds, no scorers yet."]]};
const ERA_SHORT={founding:'The first three',postwar:'Maracanazo to Mexico',expansion:'Sixteen to twenty-four',thirtytwo:'Thirty-two teams',fortyeight:'Forty-eight teams',growth:'Twenty-four teams'};
const ERA_TINY={founding:'First',postwar:'Postwar',expansion:'Expansion',thirtytwo:'32 teams',fortyeight:'48 teams',growth:'24 teams'};
const ERA_CHIPS={M:{founding:['Montevideo 1930','Italy twice','The Jules Rimet Trophy'],postwar:['The Maracanazo','Bern 1954','Pelé at seventeen'],expansion:['Cruyff and Beckenbauer','Maradona 1986','Baggio’s penalty'],thirtytwo:['France 98','Asia 2002','Messi 2022'],fortyeight:['Three hosts','104 matches','Spain 2026']},
  W:{founding:['China 1991','The Rose Bowl 1999','Germany twice'],growth:['Japan 2011','Lloyd’s hat-trick','Rapinoe 2019'],thirtytwo:['Thirty-two teams','Ten grounds','Spain 2023']}};
let ERAS=[];
function buildEras(){ERAS=ERAS_ALL[state.sex].map(e=>({id:e[0],name:e[1],from:e[2],to:e[3],text:e[4]}));for(const e of ERAS)e.ball={label:'The finals of the era',features:ERA_CHIPS[state.sex][e.id],svg:eraSvg(e)};}
function eraSvg(e){const pts=TOUR.filter(t=>t.sex===state.sex&&t.year>=e.from&&t.year<=e.to&&t.point).map(t=>({p:proj(t.point),y:t.year}));return `<svg viewBox="0 0 1080 540" aria-hidden="true" style="background:#0b0d12;border-radius:8px"><use href="#land" class="land" style="stroke-width:1.2"/>${pts.map(o=>`<circle cx="${o.p[0].toFixed(1)}" cy="${o.p[1].toFixed(1)}" r="9" fill="var(--accent)" stroke="#07080a" stroke-width="2"><title>${o.y}</title></circle>`).join('')}<text x="24" y="60" font-family="JetBrains Mono,monospace" font-size="28" letter-spacing="6" fill="#8b9099">${e.from}–${e.to}</text></svg>`;}
const eraOf=y=>ERAS.find(e=>y>=e.from&&y<=e.to)||(y<ERAS[0].from?ERAS[0]:ERAS[ERAS.length-1]);
const eraRange=()=>state.era==='all'?[FIRST_YEAR,LAST_YEAR]:(e=>[e.from,e.to])(ERAS.find(e=>e.id===state.era));
const inEraYear=y=>{const [a,b]=eraRange();return y>=a&&y<=b;};
const eraSeasons=()=>S.filter(s=>inEraYear(s.year));
const eraHeld=()=>eraSeasons();
const eraMatches=()=>eraSeasons().flatMap(s=>s.matches);
const lensLabel=()=>SEX_SHORT[state.sex]+' World Cup';
const eraLabel=()=>(state.era==='all'?`all eras · ${FIRST_YEAR}–${LAST_YEAR}`:(e=>`${e.name} · ${e.from}–${e.to}`)(ERAS.find(e=>e.id===state.era)))+' · '+lensLabel();

/* ---------- aggregates ---------- */
let aggCache={};
const recCmp=(a,b)=>b.titles-a.titles||b.finals-a.finals||b.wins-a.wins||b.played-a.played||String(a.id).localeCompare(String(b.id));
function teamAgg(){const key='t|'+state.sex+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const s of eraSeasons()){const t=s.t;for(const tn of t.teams){const a=map[tn]||(map[tn]={id:tn,played:0,wins:0,draws:0,losses:0,gf:0,ga:0,titles:0,finals:0,top4:0,tournaments:0,first:s.year,last:s.year,years:[],best:null,bestStage:0,shootW:0,shootL:0,byYear:{}});a.tournaments++;a.first=Math.min(a.first,s.year);a.last=Math.max(a.last,s.year);a.years.push(s.year);const pos=t.standings.indexOf(tn)+1;if(pos===1)a.titles++;if(pos===1||pos===2)a.finals++;if(pos>=1&&pos<=4)a.top4++;
      const ms=s.matches.filter(m=>m.home===tn||m.away===tn);let w=0,d=0,l=0,gf=0,ga=0,far=0;for(const m of ms){if(m.replay==='replayed')continue;const r=resFor(m,tn);const sd=sideOf(m,tn);gf+=sd==='h'?m.hs:m.as;ga+=sd==='h'?m.as:m.hs;if(r==='W')w++;else if(r==='D'){d++;if(m.ph!=null){if(winnerName(m)===tn)a.shootW++;else a.shootL++;}}else l++;far=Math.max(far,STAGE_RANK[m.stage]||0);}
      a.played+=ms.filter(m=>m.replay!=='replayed').length;a.wins+=w;a.draws+=d;a.losses+=l;a.gf+=gf;a.ga+=ga;const fin=pos||(far>=8?5:null);a.byYear[s.year]={pos,far,w,d,l,gf,ga,played:ms.length};if(!a.best||(pos&&(!a.best.pos||pos<a.best.pos))||(!pos&&!a.best.pos&&far>a.best.far))a.best={y:s.year,pos,far};a.bestStage=Math.max(a.bestStage,far);}}
  const out=Object.values(map);out.sort(recCmp);out.forEach((a,i)=>a.rank=i+1);return aggCache[key]=out;}
const finishLabel=(pos,far)=>pos===1?'Champions':pos===2?'Runners-up':pos===3?'Third':pos===4?'Fourth':far>=9?'Final':far>=8?'Third place match':far>=7?'Semi-final':far>=6?'Quarter-final':far>=5?'Round of 16':far>=4?'Round of 32':far>=2?'Second group stage':'Group stage';
function playerAgg(){const key='p|'+state.sex+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};const get=(id,team,y)=>{let a=map[id]||(map[id]={id,goals:0,pens:0,own:0,apps:0,starts:0,subs:0,cards:0,reds:0,tournaments:new Set(),teams:{},first:y,last:y,hat:0,byYear:{}});a.first=Math.min(a.first,y);a.last=Math.max(a.last,y);if(team)a.teams[team]=(a.teams[team]||0)+1;return a;};
  for(const s of eraSeasons()){const sq=A.squads[s.t.id]||{};for(const tn in sq)for(const [pid] of sq[tn]){const a=get(pid,tn,s.year);a.tournaments.add(s.year);}
    for(const m of s.matches){const d=m.d;const cnt={};for(const g of d.g){const team=g[0]===1?(g[4]?m.away:m.home):(g[4]?m.home:m.away);const a=get(g[1],team,s.year);if(g[4])a.own++;else{a.goals++;cnt[g[1]]=(cnt[g[1]]||0)+1;if(g[5])a.pens++;const by=a.byYear[s.year]||(a.byYear[s.year]={goals:0,apps:0});by.goals++;}a.tournaments.add(s.year);}
      for(const pid in cnt)if(cnt[pid]>=3)map[pid].hat++;
      if(d.l){for(const sd of ['h','a']){const team=sd==='h'?m.home:m.away;for(const [pid,,,starter] of d.l[sd]){const a=get(pid,team,s.year);a.apps++;if(starter)a.starts++;else a.subs++;a.tournaments.add(s.year);const by=a.byYear[s.year]||(a.byYear[s.year]={goals:0,apps:0});by.apps++;}}}
      for(const b of d.b){const a=get(b[1],b[0]===1?m.home:m.away,s.year);a.cards++;if(b[4]!=='Y')a.reds++;}}}
  const out=Object.values(map).map(a=>({...a,name:pname(a.id),ntour:a.tournaments.size,years:[...a.tournaments].sort(),team:Object.entries(a.teams).sort((p,q)=>q[1]-p[1])[0]?.[0]||null}));
  out.sort((a,b)=>b.goals-a.goals||b.apps-a.apps||a.name.localeCompare(b.name));return aggCache[key]=out;}
function groundAgg(){const key='g|'+state.sex+'|'+state.era;if(aggCache[key])return aggCache[key];const map={};
  for(const s of eraSeasons())for(const m of s.matches){if(!m.stadium)continue;const st=ST[m.stadium]||{name:'Unknown',city:'',country:''};const a=map[m.stadium]||(map[m.stadium]={id:m.stadium,name:st.name,city:st.city,country:st.country||'',cap:st.cap,count:0,finals:0,goals:0,first:s.year,last:s.year,years:new Set(),wins:{},matches:[]});a.count++;a.goals+=m.hs+m.as;a.first=Math.min(a.first,s.year);a.last=Math.max(a.last,s.year);a.years.add(s.year);if(m.stage==='final')a.finals++;const w=winnerName(m);if(w)a.wins[w]=(a.wins[w]||0)+1;a.matches.push(m);}
  const out=Object.values(map).map(a=>({...a,tournaments:a.years.size,top:Object.entries(a.wins).sort((p,q)=>q[1]-p[1]||p[0].localeCompare(q[0]))[0]?.[0]||null}));out.sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));return aggCache[key]=out;}
const LENSES={titles:['Titles','World Cups won; then finals, then wins.'],wins:['Wins','Matches won after extra time; shoot-outs are draws.'],played:['Matches','Matches played in the lens.'],gf:['Goals scored','Goals for, after extra time.'],tournaments:['Tournaments','Tournaments played.'],finals:['Finals','Finals reached.'],top4:['Top four','Finishes in the first four.']};
const PLENSES={goals:['Goals','Goals scored, own goals left out.'],apps:['Appearances','Matches played, from the line-ups the source holds (1970 onwards).'],ntour:['Tournaments','Tournaments in a squad.'],hat:['Hat-tricks','Three or more goals in one match.'],pens:['Penalties scored','Goals from the spot in play, not shoot-outs.']};
const GLENSES={count:['Matches','Matches staged in the lens.'],finals:['Finals','Finals staged.'],goals:['Goals','Goals seen there.'],tournaments:['Tournaments','Tournaments the ground served.']};
let seasonBest={};
function champOf(s){if(seasonBest[s.year]!==undefined)return seasonBest[s.year];const t=s.t;const scorers={};for(const m of s.matches)for(const g of m.d.g){if(g[4])continue;const team=g[0]===1?m.home:m.away;const a=scorers[g[1]]||(scorers[g[1]]={id:g[1],goals:0,team});a.goals++;}const top=Object.values(scorers).sort((a,b)=>b.goals-a.goals||pname(a.id).localeCompare(pname(b.id)));
  const goals=s.matches.reduce((n,m)=>n+m.hs+m.as,0);return seasonBest[s.year]={leader:t.winner||null,standings:t.standings,final:t.final?mById[t.final]:null,scorers:top,goals,matches:s.matches.length,teams:t.count};}
const leaderOf=s=>champOf(s).leader;

/* ---------- theme ---------- */
function applyTheme(){let sel=$('#theme'),v=sel.value,root=document.documentElement,acc,sec,ter,ink;
  if(v==='champion'){const s=byYear[state.year];const n=state.whole?teamAgg()[0]?.id:(s?leaderOf(s):null);acc=n?color(n):'#f2db50';sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);sel.options[0].textContent=`Champions of the tournament · ${n||'—'}`;}
  else{acc=color(v);sec='#f4f4f2';ter='#0b0f14';ink=onColor(acc);}
  root.style.setProperty('--accent',acc);root.style.setProperty('--accent2',sec);root.style.setProperty('--accent3',ter);root.style.setProperty('--on-accent',ink);}

/* ---------- the opening (once per visit): the whistle ---------- */
function lightsOut(){const box=$('#lights');let seen=false;try{seen=sessionStorage.getItem(LIGHT_KEY)==='1';}catch(e){}
  const out=()=>{if(!box.isConnected)return;box.classList.add('out');setTimeout(()=>box.remove(),800);try{sessionStorage.setItem(LIGHT_KEY,'1');}catch(e){}};
  if(seen||RM){box.remove();return;}
  setTimeout(()=>box.classList.add('go'),400);setTimeout(()=>box.classList.add('over'),2800);setTimeout(out,3600);
  $('#skipLights').addEventListener('click',out);document.addEventListener('keydown',e=>{if(box.isConnected&&(e.key==='Enter'||e.key==='Escape'||e.key===' '))out();},{once:true});}

/* ---------- the River: share of the tournament's wins (or goals) by team ---------- */
function smooth(pts){if(pts.length<3)return pts.map((p,i)=>(i?'L':'')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join('');let d='';for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=`C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;}return d;}
let riverModel=null;
function buildRiver(){const years=S.map(s=>s.year),shares=[],totals=[],champs=[];const teamFirst={},teamTotal={};
  for(const s of S){const w={};let tot=0;for(const m of s.matches){if(m.replay==='replayed')continue;if(state.metric==='wins'){const win=winnerName(m);if(win&&m.hs!==m.as){w[win]=(w[win]||0)+1;tot++;}}else{w[m.home]=(w[m.home]||0)+m.hs;w[m.away]=(w[m.away]||0)+m.as;tot+=m.hs+m.as;}}
    for(const t in w){if(!w[t])continue;if(teamFirst[t]===undefined)teamFirst[t]=s.year;teamTotal[t]=(teamTotal[t]||0)+w[t];}
    const c=champOf(s);shares.push(w);totals.push(tot);champs.push({t:c.leader,standings:c.standings,hosts:s.t.hosts,city:s.t.point?s.t.point[0]:'',matches:s.matches.length,goals:c.goals,teams:c.teams,final:c.final});}
  const teams=Object.keys(teamFirst).sort((a,b)=>teamFirst[a]-teamFirst[b]||teamTotal[b]-teamTotal[a]);riverModel={years,shares,totals,champs,teams,teamTotal};}
function drawRiver(){
  if(!riverModel)buildRiver();const {years,shares,totals,champs,teams,teamTotal}=riverModel;
  const svg=$('#riverSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  if(!years.length){svg.innerHTML='';$('#riverAxis').innerHTML='';$('#riverLegend').innerHTML='';return;}
  const era=state.era==='all'?null:ERAS.find(e=>e.id===state.era);
  let i0=era?years.findIndex(y=>y>=era.from):0,i1=era?years.length-1-[...years].reverse().findIndex(y=>y<=era.to):years.length-1;if(i0<0||i1<i0){i0=0;i1=years.length-1;}const n=i1-i0+1;
  const padL=8,padR=era?64:56,top=40,bottom=26,plotH=H-top-bottom;
  const y0v=years[i0],y1v=years[i1];const span=Math.max(4,y1v-y0v);const slotW=n===1?(W-padL-padR)*.42:(W-padL-padR)/span*4;const xOf=y=>n===1?padL+(W-padL-padR)/2:padL+(y-y0v)/span*(W-padL-padR);const x=i=>xOf(years[i]);
  const maxC=Math.max(1,...champs.slice(i0,i1+1).map(c=>c.matches));const thick=i=>plotH*(champs[i].matches?0.22+0.78*Math.sqrt(champs[i].matches/maxC):0.02);const y0=i=>top+(plotH-thick(i))/2;
  const cum=years.map(()=>0);let bands='';const eraTotal={};for(let i=i0;i<=i1;i++)for(const t in shares[i])eraTotal[t]=(eraTotal[t]||0)+shares[i][t];
  const drawTeams=era?teams.filter(t=>eraTotal[t]>0):teams;
  const runs=[];let cur=[i0];for(let i=i0+1;i<=i1;i++){if(years[i]-years[i-1]>4){runs.push(cur);cur=[i];}else cur.push(i);}runs.push(cur);
  for(const t of drawTeams){let any=false;let d='';for(const run of runs){const up=[],down=[];for(const i of run){const sh=totals[i]?(shares[i][t]||0)/totals[i]:0;const a=y0(i)+cum[i]*thick(i);const b=a+sh*thick(i);cum[i]+=sh;up.push([x(i),a]);down.push([x(i),b]);if(sh>0)any=true;}
      if(run.length===1){const w=slotW/2;up.unshift([up[0][0]-w,up[0][1]]);up.push([up[1][0]+w,up[1][1]]);down.unshift([down[0][0]-w,down[0][1]]);down.push([down[1][0]+w,down[1][1]]);}
      const dn=down.reverse();d+='M'+up[0][0].toFixed(1)+' '+up[0][1].toFixed(1)+smooth(up)+'L'+dn[0][0].toFixed(1)+' '+dn[0][1].toFixed(1)+smooth(dn)+'Z';}
    if(!any)continue;const tot=era?eraTotal[t]:teamTotal[t];
    bands+=`<path class="band${state.focusTeam===t?' focus':''}" data-t="${esc(t)}" d="${d}" fill="${color(t)}" stroke="#07080a" stroke-width=".5"><title>${esc(t)} · ${fmt(tot)} ${state.metric==='wins'?'wins':'goals'} ${era?'in this era':'since '+years[shares.findIndex(s=>s[t])]}</title></path>`;}
  let eras='';if(era){eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(era.name)} · ${era.from}–${era.to} · ${drawTeams.length} teams</text>`;}
  else for(const e of ERAS){const k=years.findIndex(y=>y>=e.from);if(k<0)continue;const xx=x(k);const nxt=ERAS[ERAS.indexOf(e)+1];const nk=nxt?years.findIndex(y=>y>=nxt.from):-1;const slot=(nk>=0?x(nk):W)-xx;const fitW=l=>l.length*7.9+10<=slot;let label=ERA_SHORT[e.id]||e.name;if(!fitW(label))label=ERA_TINY[e.id]||'';const fits=!!label&&fitW(label);eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-6}" x2="${xx.toFixed(1)}" y2="${H-bottom+4}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(label)}</text>`:''}`;}
  let strip='',hits='';for(let i=i0;i<=i1;i++){const w=slotW;const c=champs[i];strip+=`<rect x="${(x(i)-w/2).toFixed(1)}" y="${H-bottom+8}" width="${Math.max(1,w-1).toFixed(1)}" height="8" fill="${c.t?color(c.t):'#333'}" rx="1"><title>${years[i]} · ${esc(c.hosts.join(' / '))}${c.t?' · champions: '+esc(c.t):''}</title></rect>`;hits+=`<rect class="yearhit" data-y="${years[i]}" x="${(x(i)-w/2).toFixed(1)}" y="0" width="${w.toFixed(1)}" height="${H}"/>`;}
  const si=years.indexOf(state.year);const selX=n>1&&!state.whole&&si>=i0&&si<=i1?x(si):-10;
  svg.innerHTML=`<g id="bands">${bands}</g>${eras}<g>${strip}</g><line class="cursor" id="riverCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom+4}"/><line x1="${selX.toFixed(1)}" y1="${top-4}" x2="${selX.toFixed(1)}" y2="${H-bottom+16}" stroke="var(--accent)" stroke-width="2" pointer-events="none"/><g id="hits">${hits}</g>`;
  $('#riverStage').classList.toggle('hasfocus',!!state.focusTeam);
  const axisYears=years.slice(i0,i1+1).filter((y,k,arr)=>arr.length<=14||k%Math.ceil(arr.length/12)===0||k===arr.length-1);
  $('#riverAxis').innerHTML=axisYears.map(y=>`<span style="position:absolute;left:${((xOf(y)-padL)/(W-padL-padR)*100).toFixed(2)}%">${y}</span>`).join('');
  const legend=$('#riverLegend');const scoreOf=era?eraTotal:teamTotal;const topN=[...drawTeams].sort((a,b)=>(scoreOf[b]||0)-(scoreOf[a]||0)).slice(0,14);if(state.focusTeam&&!(scoreOf[state.focusTeam]>0))state.focusTeam=null;
  legend.innerHTML=topN.map(t=>`<button type="button" data-t="${esc(t)}" class="${state.focusTeam===t?'on':''}"><i style="background:${color(t)}"></i>${esc(t)}</button>`).join('');
  if(!legend.dataset.built){legend.dataset.built='1';legend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();});}
  const tip=$('#riverTip'),stage=$('#riverStage');
  svg.onmousemove=e=>{const hit=e.target.closest('.yearhit');if(!hit){tip.classList.remove('show');$('#riverCursor').style.opacity=0;return;}const y=+hit.dataset.y,i=years.indexOf(y);const cx=x(i);const cur=$('#riverCursor');cur.setAttribute('x1',cx);cur.setAttribute('x2',cx);cur.style.opacity=1;
    const rows=Object.entries(shares[i]).sort((a,b)=>b[1]-a[1]).slice(0,6);const c=champs[i];const f=c.final;
    tip.innerHTML=`<div class="yr">${y}</div><div class="small muted" style="margin:2px 0 8px">${esc(c.hosts.join(' / '))} · ${c.teams} teams · ${c.matches} matches · ${c.goals} goals</div>${f?`<div class="row"><span><i class="sw" style="background:${color(c.t||'?')}"></i>${esc(f.home)} ${f.hs}–${f.as} ${esc(f.away)}</span><span class="dim">${f.et?'a.e.t.':''}${f.ph!=null?` ${f.ph}–${f.pa} pens`:''}</span></div>`:c.t?`<div class="row"><span><i class="sw" style="background:${color(c.t)}"></i>${esc(c.t)}</span><span class="dim">champions</span></div>`:''}${rows.map(([t,p])=>`<div class="row"><span><i class="sw" style="background:${color(t)}"></i>${esc(t)}</span><span>${p} ${state.metric==='wins'?'win':'goal'}${p===1?'':'s'}</span></div>`).join('')}<div class="small dim" style="margin-top:8px">Share of the tournament’s ${state.metric==='wins'?'wins':'goals'} by team · click to open</div>`;
    const r=stage.getBoundingClientRect();let px=e.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.style.top='12px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#riverCursor').style.opacity=0;};
  svg.onclick=e=>{const b=e.target.closest('.band');const hit=e.target.closest('.yearhit');if(hit){const y=+hit.dataset.y;if(byYear[y])setSeason(y,true);}else if(b){state.focusTeam=state.focusTeam===b.dataset.t?null:b.dataset.t;drawRiver();}};
}
