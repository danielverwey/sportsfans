'use strict';
/* ============================================================
   TEN NATIONS — an ode to the Test match. Application.
   The archive is read from the embedded JSON block and never written to.
   ============================================================ */
const A=JSON.parse(document.getElementById('archive-data').textContent);
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n==null?'—':Number(n).toLocaleString('en-GB');
const pct=n=>n==null?'—':n.toFixed(1)+'%';
const yr=d=>d?+d.slice(0,4):null;
const day=d=>d?new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}):'—';
const TEAMS=A.teams, TEN=TEAMS.map(t=>t.name), teamBy=Object.fromEntries(TEAMS.map(t=>[t.name,t]));
const OPP_COLOURS={'New Zealand':'#b6c1c9','Australia':'#f4c04c','England':'#edf1f2','Ireland':'#4ec679','Wales':'#e25b63','Scotland':'#6f8bd4','France':'#578cfa','Argentina':'#83cff0','British & Irish Lions':'#e75863','Italy':'#539be5','Japan':'#f48f9a','Fiji':'#ecebe6','Samoa':'#618fff','Tonga':'#d65b5e','Georgia':'#a86572','Namibia':'#85a8ed','USA':'#b482a2','Portugal':'#d65965','South America':'#d6ba82','NZ Cavaliers':'#8faba3','World Invitation':'#c09aca','Canada':'#ef8d81','Romania':'#ecce59','Uruguay':'#8bcddd','Pacific Islands':'#8cbbcb','Spain':'#c85a5b','South Africa':'#5cd4a1'};
const hueCache={};const hsl2hex=(h,s,l)=>{s/=100;l/=100;const k=n=>(n+h/30)%12,a=s*Math.min(l,1-l),f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));return '#'+[f(0),f(8),f(4)].map(v=>Math.round(v*255).toString(16).padStart(2,'0')).join('');};
const colourOf=n=>{if(teamBy[n])return teamBy[n].accent;if(OPP_COLOURS[n])return OPP_COLOURS[n];if(hueCache[n])return hueCache[n];let h=0;for(const ch of String(n))h=(h*31+ch.charCodeAt(0))>>>0;return hueCache[n]=hsl2hex(h%360,35,60);};
const mixHex=(a,b,t)=>{const p=h=>{const m=/^#?([0-9a-f]{6})$/i.exec(h);if(!m)return [128,128,128];const n=parseInt(m[1],16);return [n>>16,n>>8&255,n&255];};const x=p(a),y=p(b);return '#'+x.map((v,i)=>Math.round(v*t+y[i]*(1-t)).toString(16).padStart(2,'0')).join('');};
const lum=hex=>{let m=/^#?([0-9a-f]{6})$/i.exec(hex||'');if(!m)return .5;let n=parseInt(m[1],16),r=(n>>16)/255,g=(n>>8&255)/255,b=(n&255)/255;const f=c=>c<=.03928?c/12.92:((c+.055)/1.055)**2.4;return .2126*f(r)+.7152*f(g)+.0722*f(b);};
const onColor=hex=>lum(hex)>.42?'#07080a':'#f4f4f2';
const ERAS=[["all","All eras · 1871–2026",1871,2026,"All available records."],["origins","Early internationals · 1871–1913",1871,1913,"The earliest internationals. Pre-1885 scores count goals rather than modern points."],["interwar","Tours & interwar years · 1914–1948",1914,1948,"Touring sides and the interwar record; international schedules contain long gaps."],["postwar","Post-war rugby · 1949–1969",1949,1969,"Follow national teams through post-war tours and annual championships."],["transition","Changing game · 1970–1986",1970,1986,"Changing scoring values and, in South Africa, the effects of apartheid-era isolation."],["worldcup","World Cup beginnings · 1987–1995",1987,1995,"The first three men’s Rugby World Cups and the transition to professionalism."],["pro","Professional era · 1996–2011",1996,2011,"The Tri Nations, Six Nations and expanding international schedules."],["modern","Modern internationals · 2012–2026",2012,2026,"The Rugby Championship era and the most recent completed internationals."]].map(e=>({id:e[0],name:e[1].split(' · ')[0],label:e[1],from:e[2],to:e[3],text:e[4]}));
const ERA_LIST=ERAS.slice(1);

/* ---------- state ---------- */
const state={team:'South Africa',era:'all',scope:'all',tab:'matches',match:null,opp:null,player:null,ground:null,coach:null,cup:null,q:'',result:'all',loc:'all',sort:'newest',page:0,playerSort:'caps',heatMetric:'matches',heatBy:'opponent',duelBy:'nation',dA:'New Zealand',dB:'Australia',pA:null,pB:null,focusOpp:null,tideMode:'margin'};
const era=()=>ERAS.find(e=>e.id===state.era)||ERAS[0];
const eraLabel=()=>era().label;
const inEra=m=>{const e=era();return m.year>=e.from&&m.year<=e.to;};
const inScope=m=>state.scope==='all'||(state.scope==='standard'?!m.historical:m.historical);

/* ---------- perspective: the archive seen from one nation ---------- */
const perspCache={};
function perspective(name){if(perspCache[name])return perspCache[name];const ms=A.matches.filter(m=>m.eligible.includes(name)).map(m=>{const home=m.home===name;const opp=home?m.away:m.home;return {...m,archiveId:m.id,opponent:opp,pf:home?m.hs:m.as_,pa:home?m.as_:m.hs,isHome:home,
  location:m.country===name||(name==='Ireland'&&m.country==='Northern Ireland')?'Home':m.country===opp?'Away':m.country?'Neutral':'Unknown',
  tries:m.scoring?m.scoring[home?0:6]+m.scoring[home?5:11]:null,triesAgainst:m.scoring?m.scoring[home?6:0]+m.scoring[home?11:5]:null,
  res:(home?m.hs:m.as_)>(home?m.as_:m.hs)?'W':(home?m.hs:m.as_)<(home?m.as_:m.hs)?'L':'D'};});
  return perspCache[name]=ms;}
const T=()=>teamBy[state.team];
const M=()=>perspective(state.team);
const lensMatches=()=>M().filter(m=>inEra(m)&&inScope(m));
const P=()=>A.players.filter(p=>p.team===state.team);
const COACHES=()=>A.coaches.filter(c=>c.team===state.team);
const byArchiveId=Object.fromEntries(A.matches.map(m=>[m.id,m]));
function aggregate(ms){let w=0,l=0,d=0,pf=0,pa=0,np=0;for(const m of ms){w+=m.res==='W';l+=m.res==='L';d+=m.res==='D';if(m.scoreUnit!=='goals'){pf+=m.pf;pa+=m.pa;np++;}}return {n:ms.length,w,l,d,pf,pa,np,rate:ms.length?100*w/ms.length:null,margin:np?(pf-pa)/np:null};}
const recStr=a=>`${a.w}–${a.l}${a.d?'–'+a.d:''}`;

/* ---------- theme ---------- */
function applyTheme(){const t=T(),r=document.documentElement;r.style.setProperty('--accent',t.accent);r.style.setProperty('--accent2',t.secondary);r.style.setProperty('--kit',t.kit);r.style.setProperty('--trim',t.trim);r.style.setProperty('--on-accent',onColor(t.accent));document.title=`APEX / ${t.name} · An Ode to the Test Match`;}

/* ---------- curtain ---------- */
function curtain(){const c=$('#curtain');let seen=false;try{seen=sessionStorage.getItem('ten-curtain')==='1';}catch(e){}
  if(seen||RM){c.remove();return;}
  c.innerHTML=TEAMS.map((t,i)=>`<i style="--c:${t.kit};--i:${i}"></i>`).join('')+`<div class="cap">Ten nations</div>`;
  setTimeout(()=>{c.remove();try{sessionStorage.setItem('ten-curtain','1');}catch(e){}},2400);}

/* ---------- jerseys ---------- */
function jersey(t){const arg=t.name==='Argentina';return `<svg viewBox="0 0 80 75" aria-hidden="true"><path d="M25 7 10 17 2 34 18 42 22 32 22 69 58 69 58 32 62 42 78 34 70 17 55 7 49 9 31 9Z" fill="${t.kit}" stroke="${t.accent}" stroke-width="1.1"/>${arg?'<path d="M22 25h36v9H22zM22 44h36v9H22zM22 61h36v8H22z" fill="#fffdf7"/>':''}<path d="m29 8 11 11L51 8" fill="none" stroke="${t.trim}" stroke-width="5"/><path d="M5 31 18 38M62 38 75 31" stroke="${t.trim}" stroke-width="4"/><text x="47" y="30" text-anchor="middle" font-size="7" font-family="Arial,sans-serif" font-weight="bold" fill="${t.trim}">${t.code}</text></svg>`;}
function drawJerseys(){$('#jerseyRow').innerHTML=TEAMS.map(t=>`<button type="button" class="jersey${t.name===state.team?' on':''}" data-team="${esc(t.name)}" style="--jc:${t.accent}" aria-pressed="${t.name===state.team}">${t.titles.length?`<span class="stars">${'★'.repeat(t.titles.length)}</span>`:''}${jersey(t)}<b>${esc(t.name)}</b><small>${esc(t.nickname)} · ${t.count}</small></button>`).join('');}

/* ---------- hero ---------- */
function drawHero(){const t=T(),ms=lensMatches(),all=M(),a=aggregate(ms),last=all[all.length-1];
  $('#heroName').textContent=t.name;
  $('#heroLede').innerHTML=`<b>${esc(t.nickname)}</b> — ${esc(t.tag.toLowerCase())}. ${fmt(all.length)} recorded internationals since ${t.from}${t.titles.length?`, world champions in ${t.titles.join(', ')}`:''}. In ${esc(eraLabel().replace(' · ',', '))}: <b>${a.w} won, ${a.l} lost${a.d?', '+a.d+' drawn':''}</b> — a ${pct(a.rate)} win rate.`;
  $('#edition').innerHTML=`<span><span class="live"></span><b>${fmt(A.matches.length)}</b> Test matches</span><span><b>${fmt(A.players.length)}</b> careers</span><span><b>${fmt(A.coaches.length)}</b> coaches</span><span>through <b>${day(A.through)}</b></span>`;
  $('#latest').innerHTML=`<span class="t">${esc(t.name)}</span><span class="sc">${last.pf}<i>–</i>${last.pa}</span><span class="t r">${esc(last.opponent)}</span><span class="sub">Latest · ${day(last.date)} · ${esc(last.venue)}, ${esc(last.city||last.country||'')} · ${esc(last.competitionRaw||last.competition)} · <span class="${last.res}">${last.res==='W'?'won':last.res==='L'?'lost':'drawn'}</span></span>`;
  $('#latest').dataset.match=last.archiveId;}

/* ---------- the Ring: your nation at the centre, every rival on a rope ---------- */
function drawWeb(){const t=T();const ms=lensMatches();const ropeColour=o=>{const c=colourOf(o);return Math.abs(lum(c)-lum(t.accent))<.12?(teamBy[o]?.trim&&Math.abs(lum(teamBy[o].trim)-lum(t.accent))>=.12?teamBy[o].trim:mixHex(c,'#7a8890',.35)):c;};const by={};for(const m of ms){(by[m.opponent]||(by[m.opponent]=[])).push(m);}
  const rows=Object.entries(by).map(([o,l])=>({o,l,a:aggregate(l)})).sort((p,q)=>q.a.n-p.a.n).slice(0,12);
  const svg=$("#webSvg"),W=780,H=640,cx=390,cy=320,R0=92,R1=228;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  const max=Math.max(1,...rows.map(r=>r.a.n));const all=aggregate(ms);
  let ropes='',nodes='';rows.forEach((r,i)=>{const ang=-Math.PI/2+i*2*Math.PI/rows.length;const deg=ang*180/Math.PI;const len=R1-R0;const w=5+30*Math.sqrt(r.a.n/max);const dec=r.a.w+r.a.l;const share=dec?r.a.w/dec:.5;const split=len*share;const oc=ropeColour(r.o);
    ropes+=`<g class="rope" data-opp="${esc(r.o)}" transform="rotate(${deg.toFixed(2)} ${cx} ${cy}) translate(${cx+R0} ${cy})" style="--k:${i}"><rect x="0" y="${(-w/2).toFixed(1)}" width="${split.toFixed(1)}" height="${w.toFixed(1)}" fill="${t.accent}" rx="2"/><rect x="${split.toFixed(1)}" y="${(-w/2).toFixed(1)}" width="${(len-split).toFixed(1)}" height="${w.toFixed(1)}" fill="${oc}" rx="2"/><rect x="${(split-1).toFixed(1)}" y="${(-w/2-3).toFixed(1)}" width="2" height="${(w+6).toFixed(1)}" fill="#070a09"/><title>${esc(t.name)} v ${esc(r.o)} · ${r.a.n} matches · ${recStr(r.a)}</title></g>`;
    const nx=cx+Math.cos(ang)*(R1+26),ny=cy+Math.sin(ang)*(R1+26);const lx=cx+Math.cos(ang)*(R1+52),ly=cy+Math.sin(ang)*(R1+52);const anchor=Math.cos(ang)>.3?'start':Math.cos(ang)<-.3?'end':'middle';const ten=!!teamBy[r.o];
    nodes+=`<g class="node${ten?' ten':''}" data-opp="${esc(r.o)}" ${ten?`data-team="${esc(r.o)}"`:''}><circle cx="${nx.toFixed(1)}" cy="${ny.toFixed(1)}" r="17" fill="${oc}" stroke="#070a09" stroke-width="2"/><text x="${nx.toFixed(1)}" y="${(ny+4).toFixed(1)}" text-anchor="middle" class="code" fill="${onColor(oc)}">${esc(teamBy[r.o]?.code||r.o.slice(0,3).toUpperCase())}</text><text x="${lx.toFixed(1)}" y="${(ly+(Math.sin(ang)>.7?14:Math.sin(ang)<-.7?-8:4)).toFixed(1)}" text-anchor="${anchor}" class="nl">${esc(r.o)}</text><text x="${lx.toFixed(1)}" y="${(ly+(Math.sin(ang)>.7?27:Math.sin(ang)<-.7?5:17)).toFixed(1)}" text-anchor="${anchor}" class="nr">${recStr(r.a)} · ${Math.round(r.a.rate)}%</text></g>`;});
  svg.innerHTML=`<circle cx="${cx}" cy="${cy}" r="${R1}" fill="none" stroke="#1f2a26" stroke-dasharray="3 6"/><g id="ropes">${ropes}</g><g id="nodes">${nodes}</g><g id="hub"><circle cx="${cx}" cy="${cy}" r="${R0-6}" fill="${t.kit}" stroke="${t.accent}" stroke-width="3"/><text x="${cx}" y="${cy-14}" text-anchor="middle" class="hubcode" fill="${onColor(t.kit)}">${esc(t.code)}</text><text x="${cx}" y="${cy+12}" text-anchor="middle" class="hubrec" id="hubRec" fill="${onColor(t.kit)}">${recStr(all)}</text><text x="${cx}" y="${cy+30}" text-anchor="middle" class="hubsub" id="hubSub" fill="${onColor(t.kit)}">${ms.length} matches · ${pct(all.rate)}</text></g>`;
  $('#webKey').innerHTML=`Each rope is a rivalry, thick for many meetings. It is coloured in <b style="color:${t.accent}">${esc(t.name)}</b>'s colour as far as their share of the decided matches, then in the rival's. Hover a rope, click it to open the rivalry; click one of the ten nations' badges to wear their colours.`;
  const stage=$('#webStage');
  svg.onmousemove=e=>{const g=e.target.closest('[data-opp]');const o=g?.dataset.opp;stage.classList.toggle('dim',!!o);$$('#webSvg .rope,#webSvg .node').forEach(x=>x.classList.toggle('hot',x.dataset.opp===o));
    if(o){const r=rows.find(r=>r.o===o);$('#hubRec').textContent=recStr(r.a);$('#hubSub').textContent=`v ${o} · ${r.a.n} · ${pct(r.a.rate)}`;}else{$('#hubRec').textContent=recStr(all);$('#hubSub').textContent=`${ms.length} matches · ${pct(all.rate)}`;}};
  svg.onmouseleave=()=>{stage.classList.remove('dim');$$('#webSvg .hot').forEach(x=>x.classList.remove('hot'));$('#hubRec').textContent=recStr(all);$('#hubSub').textContent=`${ms.length} matches · ${pct(all.rate)}`;};
  svg.onclick=e=>{const n=e.target.closest('.node[data-team]');const g=e.target.closest('[data-opp]');if(n&&e.target.closest('circle,.code')){setTeam(n.dataset.team);return;}if(g){state.opp=g.dataset.opp;go('rivals',true);}};
}

/* ---------- the Tide: one column per year, one block per match ---------- */
function drawTide(){const ms=lensMatches();const svg=$('#tideSvg'),box=svg.getBoundingClientRect(),W=Math.max(320,box.width),H=Math.max(200,box.height);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  const e=era();const years=[];for(let y=e.from;y<=e.to;y++)years.push(y);const by={};for(const m of ms){(by[m.year]||(by[m.year]=[])).push(m);}
  const padL=8,padR=8,top=34,bottom=22;const cw=(W-padL-padR)/years.length;const bw=Math.max(2,cw-Math.min(3,cw*.25));
  const val=m=>state.tideMode==='margin'?(m.scoreUnit==='goals'?1:Math.max(1,Math.abs(m.pf-m.pa))):1;
  let maxUp=1,maxDn=1;for(const y of years){const l=by[y]||[];maxUp=Math.max(maxUp,l.filter(m=>m.res!=='L').reduce((s,m)=>s+val(m),0));maxDn=Math.max(maxDn,l.filter(m=>m.res==='L').reduce((s,m)=>s+val(m),0));}
  const plotH=H-top-bottom-16;const scale=plotH/(maxUp+maxDn);const mid=top+8+maxUp*scale;const gap=state.tideMode==='margin'?1:Math.min(2,scale*.15);
  let bars='';years.forEach((y,yi)=>{const l=by[y];if(!l)return;const x=padL+yi*cw+(cw-bw)/2;let up=0,dn=0;for(const m of l){const h=Math.max(1.5,val(m)*scale-gap);const idx=ms.indexOf(m);const focus=state.focusOpp?(m.opponent===state.focusOpp?' hot':' cold'):'';const c=m.res==='W'?'var(--accent)':m.res==='L'?'var(--loss)':'var(--draw)';
      if(m.res==='L'){bars+=`<rect class="tb${focus}" data-i="${idx}" x="${x.toFixed(1)}" y="${(mid+1+dn).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" fill="${c}" rx=".5"/>`;dn+=h+gap;}
      else{up+=h;bars+=`<rect class="tb${focus}" data-i="${idx}" x="${x.toFixed(1)}" y="${(mid-1-up).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" fill="${c}" rx=".5"/>`;up+=gap;}}});
  let eras='';if(state.era==='all')for(const er of ERA_LIST){const xx=padL+(er.from-e.from)*cw;const nxt=ERA_LIST[ERA_LIST.indexOf(er)+1];const slot=(nxt?padL+(nxt.from-e.from)*cw:W)-xx;const fits=er.name.length*6.6+8<=slot;eras+=`<line class="era-line" x1="${xx.toFixed(1)}" y1="${top-8}" x2="${xx.toFixed(1)}" y2="${H-bottom}"/>${fits?`<text class="era-label" x="${(xx+5).toFixed(1)}" y="${top-14}">${esc(er.name)}</text>`:''}`;}
  else eras=`<text class="era-label" x="${padL}" y="${top-14}" style="fill:var(--accent)">${esc(e.label)} · ${ms.length} matches</text>`;
  const a=aggregate(ms);
  svg.innerHTML=`${eras}<line class="zero" x1="0" x2="${W}" y1="${mid.toFixed(1)}" y2="${mid.toFixed(1)}"/><g>${bars}</g><line class="cursor" id="tideCursor" x1="0" y1="${top-4}" x2="0" y2="${H-bottom}"/>`;
  $('#tideStage').classList.toggle('hasfocus',!!state.focusOpp);
  $('#tideLede').textContent=`${T().name}: ${ms.length} matches in ${eraLabel().replace(' · ',', ')}, one column per year. Each block is a match — wins stack up in ${T().name}'s colour, defeats stack down in red, draws sit on the line${state.tideMode==='margin'?'; block height is the margin':''}. Pick an opponent below to light up only those matches.`;
  const ticks=[];const span=e.to-e.from;const step=span>100?20:span>40?10:span>15?5:1;for(let y=Math.ceil(e.from/step)*step;y<=e.to;y+=step)ticks.push(y);if(ticks[0]!==e.from)ticks.unshift(e.from);if(ticks[ticks.length-1]!==e.to)ticks.push(e.to);
  $('#tideAxis').innerHTML=ticks.map(y=>`<span>${y}</span>`).join('');
  const opps=Object.entries(ms.reduce((o,m)=>{o[m.opponent]=(o[m.opponent]||0)+1;return o;},{})).sort((p,q)=>q[1]-p[1]).slice(0,14);
  $('#tideLegend').innerHTML=`<span class="tally-key"><b style="color:var(--accent)">▲ won ${a.w}</b>${a.d?` · <b style="color:var(--draw)">drawn ${a.d}</b>`:''} · <b style="color:var(--loss)">▼ lost ${a.l}</b> · highlight an opponent:</span>`+opps.map(([n,c])=>`<button type="button" data-o="${esc(n)}" class="${state.focusOpp===n?'on':''}"><i style="background:${colourOf(n)}"></i>${esc(n)} <span class="dim">${c}</span></button>`).join('');
  const tip=$('#tideTip'),stage=$('#tideStage');
  svg.onmousemove=ev=>{const b=ev.target.closest('.tb');const cur=$('#tideCursor');if(!b){tip.classList.remove('show');cur.style.opacity=0;return;}const m=ms[+b.dataset.i];const xx=+b.getAttribute('x')+bw/2;cur.setAttribute('x1',xx);cur.setAttribute('x2',xx);cur.style.opacity=1;
    tip.innerHTML=`<div class="eyebrow" style="color:var(--muted)">${day(m.date)} · <span class="${m.res}">${m.res==='W'?'won':m.res==='L'?'lost':'drawn'}</span></div><div class="sc">${m.pf}<i>–</i>${m.pa}</div><div style="font:700 13px var(--display);text-transform:uppercase;letter-spacing:.04em">${esc(T().name)} v ${esc(m.opponent)}</div><div class="row">${esc(m.venue)}${m.city?', '+esc(m.city):''} · ${m.location.toLowerCase()}</div><div class="row">${esc(m.competitionRaw||m.competition)}${m.scoreUnit==='goals'?' · scored in goals':''}</div><div class="row dim">click to open the match</div>`;
    const r=stage.getBoundingClientRect();let px=ev.clientX-r.left;px=Math.max(150,Math.min(r.width-150,px));tip.style.left=px+'px';tip.classList.add('show');};
  svg.onmouseleave=()=>{tip.classList.remove('show');$('#tideCursor').style.opacity=0;};
  svg.onclick=ev=>{const b=ev.target.closest('.tb');if(b){openMatch(ms[+b.dataset.i].archiveId);}};
}
