'use strict';
/* ============================================================
   Adapter: reads the embedded archive (never modified) and
   presents it in the shape the APEX application expects.
   ============================================================ */
const ARCHIVE=window.ARCHIVE||JSON.parse(document.getElementById('archive-data').textContent);

/* ---------- schematic motorcycles for the era cards (original outlines, not specific bikes) ---------- */
function bikeSvg(o){const st='fill="none" stroke="#e8eef8" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"';const F='#172536',Fd='#0f1826';
  const wheel=(cx,cy,r,wire)=>{let s=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="#0c121c" ${st}/><circle cx="${cx}" cy="${cy}" r="${r-9}" ${st} stroke-width="1.6"/>`;if(wire){for(let i=0;i<16;i++){const a=i*Math.PI/8;s+=`<path d="M${(cx+Math.cos(a)*6).toFixed(1)} ${(cy+Math.sin(a)*6).toFixed(1)}L${(cx+Math.cos(a)*(r-10)).toFixed(1)} ${(cy+Math.sin(a)*(r-10)).toFixed(1)}" stroke="#8296ad" stroke-width="1.2"/>`;}}else{for(let i=0;i<5;i++){const a=i*Math.PI*2/5-Math.PI/2;s+=`<path d="M${cx} ${cy}L${(cx+Math.cos(a)*(r-11)).toFixed(1)} ${(cy+Math.sin(a)*(r-11)).toFixed(1)}" stroke="#8296ad" stroke-width="5"/>`;}}s+=`<circle cx="${cx}" cy="${cy}" r="6" fill="#0c121c" ${st} stroke-width="2"/>`;return s;};
  const R=[300,204],Fr=[700,204],r=58;let g='';
  g+=`<path d="M38 262H920" stroke="#304053" stroke-width="1"/>`;
  g+=wheel(R[0],R[1],r,o.wire);
  // swingarm and frame
  g+=`<path d="M300 204 L430 188" ${st} stroke-width="7"/><path d="M430 188 L470 124 L640 112" ${st} stroke-width="5"/><path d="M470 124 L455 190" ${st} stroke-width="4"/>`;
  // engine
  g+=`<path d="M440 150 L570 148 L582 214 L452 226 Z" fill="${F}" ${st}/><path d="M462 168h96M464 182h96M466 196h96" stroke="#8296ad" stroke-width="1.6"/>`;
  // exhaust
  if(o.exhaust==='twin')g+=`<path d="M460 226 Q520 250 640 238 L700 232" ${st} stroke-width="9"/><path d="M470 234 Q530 262 650 250" ${st} stroke-width="7"/>`;
  else if(o.exhaust==='under')g+=`<path d="M560 214 Q600 232 520 232 Q430 232 400 200 L372 150 L352 124" ${st} stroke-width="6"/><path d="M356 126 L326 110" ${st} stroke-width="9"/>`;
  else g+=`<path d="M570 214 Q610 236 520 238 Q430 240 400 236 L330 232" ${st} stroke-width="6"/><path d="M340 240 L262 236" ${st} stroke-width="11"/>`;
  // tank, seat, tail
  g+=`<path d="M448 122 Q462 84 540 82 Q596 84 606 106 L590 124 Z" fill="${F}" ${st}/>`;
  g+=`<path d="M448 122 L380 122 L332 120 Q312 112 322 98 L360 94 L448 100 Z" fill="${o.tail?F:Fd}" ${st}/>`;
  if(o.tail)g+=`<path d="M332 120 Q300 116 310 96 L322 98" ${st}/>`;
  // fairing
  if(o.fairing){g+=`<path d="M606 106 Q636 70 662 68 Q700 84 740 118 Q754 134 744 156 L722 190 Q702 236 620 244 L500 244 Q446 240 452 214 L450 160 L460 150 L570 148 L590 124 Z" fill="${F}" fill-opacity=".92" ${st}/>`;
    g+=`<path d="M626 92 Q652 70 664 70 L704 92" ${st} stroke-width="2" stroke="#8296ad"/>`;// screen
    if(o.headlight)g+=`<path d="M712 110 q12 8 14 22 M700 120 q10 6 12 18" stroke="#8296ad" stroke-width="2" fill="none"/>`;
    if(o.wings)g+=`<path d="M690 130 L760 124 L762 131 L692 138 Z" fill="${F}" ${st} stroke-width="2"/><path d="M700 150 L756 146 L757 152 L702 157 Z" fill="${F}" ${st} stroke-width="2"/>`;}
  else{g+=`<path d="M606 106 L640 112 L646 130 L600 132 Z" fill="${F}" ${st}/>`;}
  // fork, bars, front wheel
  g+=`<path d="M700 204 L646 96" ${st} stroke-width="6"/><path d="M712 200 L658 92" ${st} stroke-width="6"/><path d="M646 96 L616 104 M658 92 L640 84" ${st} stroke-width="4"/>`;
  g+=wheel(Fr[0],Fr[1],r,o.wire);
  // rider: helmet over the screen, back along the tank, hips over the seat, knee to the peg
  const hx=o.fairing?602:604,hy=o.fairing?64:44;
  if(o.fairing)g+=`<path d="M${hx-8} ${hy+20} Q${hx-40} ${hy+18} ${hx-90} ${hy+28} Q${hx-140} ${hy+38} ${hx-176} ${hy+56} L${hx-170} ${hy+70} Q${hx-120} ${hy+62} ${hx-60} ${hy+56} L${hx-14} ${hy+44} Z" fill="#101823" ${st}/>`;
  else g+=`<path d="M${hx-8} ${hy+18} Q${hx-50} ${hy+22} ${hx-100} ${hy+44} Q${hx-150} ${hy+64} ${hx-176} ${hy+78} L${hx-168} ${hy+90} Q${hx-120} ${hy+80} ${hx-70} ${hy+66} L${hx-12} ${hy+42} Z" fill="#101823" ${st}/>`;
  g+=`<path d="M${hx-14} ${hy+44} L${hx+12} ${hy+50} L${hx+36} ${hy+38}" ${st} stroke-width="5"/>`;
  const kf=o.fairing;g+=`<path d="M${hx-168} ${hy+(kf?66:86)} L${hx-120} ${hy+(kf?108:116)} L${hx-92} ${hy+(kf?146:150)}" ${st} stroke-width="6"/>`;
  g+=`<circle cx="${hx}" cy="${hy}" r="21" fill="#0c121c" ${st}/><path d="M${hx-4} ${hy-4} q18 -2 22 8" stroke="#8296ad" stroke-width="2.5" fill="none"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 290" role="img" aria-label="${o.label}: simplified side profile"><title>${o.label} — schematic outline</title><desc>Representative illustration, not a scale drawing or a specific motorcycle.</desc><g>${g}</g></svg>`;}

/* ---------- conversion ---------- */
function adapt(A,SP){
  const D={eras:[],circuits:{},layouts:{},cutoff:A.lastDate?new Date(A.lastDate+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}):'',seasons:[],drivers:{},teams:{}};
  D.eras=SP.eras.map(e=>{const car={label:e.bike.label,features:e.bike.features,source:e.source||'',svg:bikeSvg(e.bike)};return {id:e.id,from:e.from,to:e.to,name:e.name,short:e.short||e.name,text:e.text,car,bike:car};});
  // riders
  const codeCount={};for(const [id,r] of Object.entries(A.riders)){const parts=(r.name||'').trim().split(/\s+/);const last=parts[parts.length-1]||r.name||'';const first=parts.length>1?parts[0]:'';const clean=x=>x.normalize('NFD').replace(/[^A-Za-z]/g,'');let code=(clean(last).slice(0,3)||'???').toUpperCase();D.drivers[id]={name:r.name,short:last,code,nationality:r.country||'',dob:null,number:r.number,first};codeCount[code]=(codeCount[code]||0)+1;}
  for(const id in D.drivers){const d=D.drivers[id];if(codeCount[d.code]>1&&d.first){const alt=(d.first.normalize('NFD').replace(/[^A-Za-z]/g,'').slice(0,1)+d.short.normalize('NFD').replace(/[^A-Za-z]/g,'').slice(0,2)).toUpperCase();if(alt.length===3)d.code=alt;}}
  // makers
  const makers=new Set();for(const r of A.races)for(const x of r.results)makers.add(x.maker||'Unresolved make');for(const y in A.standings)for(const x of A.standings[y].rows)makers.add(x.maker||'Unresolved make');
  for(const m of makers)D.teams[m]={name:m,color:SP.colours[m]||'#b5a5ed'};
  // circuits + layouts
  for(const [id,c] of Object.entries(A.circuits)){const t=SP.osm&&SP.osm[id];const f1=SP.venues[id];const layouts=[];
    if(t){D.layouts[id]={id,d:t,source:'osm'};layouts.push(id);}
    if(f1){for(const l of f1.layouts){const lid='f1db:'+l.id;D.layouts[lid]={id:lid,d:l.d,from:l.from,to:l.to,source:'f1db',venue:f1.name};layouts.push(lid);}}
    D.circuits[id]={id,name:c.name,country:c.country||'',place:c.place||'',lat:c.lat||null,lon:c.lng||null,url:'',length:c.length||null,layouts,hasOwn:!!t,f1Name:f1?f1.name:null};}
  const layoutFor=(cid,year)=>{const c=D.circuits[cid];if(!c)return null;if(c.hasOwn)return cid;const f1=SP.venues[cid];if(!f1)return null;let best=null,bd=1e9;for(const l of f1.layouts){const dist=year<l.from?l.from-year:year>l.to?year-l.to:0;if(dist<bd){bd=dist;best='f1db:'+l.id;}}return best;};
  // races → seasons
  const byYear={};
  const statusOf=x=>{const s=(x.status||'').toUpperCase();if(s==='CLASSIFIED'){const lg=parseInt(x.lapGap||'0',10)||0;return lg>0?`+${lg} Lap${lg>1?'s':''}`:'Finished';}if(s==='NC'||s==='NOT CLASSIFIED')return x.pos!=null?'Finished':'Not classified';if(s==='RET'||s==='DNF'||s==='RETIRED'||s==='NOTFINISHFIRST')return 'Retired';if(s==='DNS'||s==='NOTSTARTED'||s==='NOT STARTED'||s==='NOTONRESTARTGRID')return 'Did not start';if(s==='DNQ')return 'Did not qualify';if(s==='EXCLUDED'||s==='DSQ')return 'Disqualified';if(s==='WD'||s==='DNA')return 'Did not start';if(s==='SUBJECT TO HOMOLOGATION')return 'Subject to homologation';return x.status||'—';};
  const labelOf=(x,st)=>(st==='Finished'||/^\+\d+ Lap/.test(st))&&x.pos!=null?String(x.pos):st==='Did not start'||st==='Did not qualify'?'W':st==='Disqualified'?'D':st==='Not classified'?'NC':'R';
  const sortedRaces=[...A.races].sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:(a.order||0)-(b.order||0)||(a.type==='RAC'||a.type==='R1'?-1:1));
  const groups={};// weekend key → {main:[], sprint:[]}
  for(const r of sortedRaces){const key=r.year+'|'+(r.round||r.code||r.circuit)+'|'+(r.round?'':r.date.slice(0,7));const g=groups[key]||(groups[key]={year:r.year,items:[]});g.items.push(r);}
  const seasonsMap={};
  const mkRows=(r,isSprint)=>{const fastR=r.fast?.rider;const poleR=r.pole?.rider;const rows=[...r.results].sort((a,b)=>(a.pos==null)-(b.pos==null)||(a.pos||0)-(b.pos||0));let p=0;return rows.map(x=>{p++;const st=statusOf(x);const lab=labelOf(x,st);const fin=st==='Finished'||/^\+\d+ Lap/.test(st);const t=x.maker||'Unresolved make';const win=!isSprint&&x.pos===1&&lab==='1';const pod=!isSprint&&x.pos!=null&&x.pos<=3&&/^\d+$/.test(lab);const fl=x.rider===fastR&&!isSprint?1:0;const isP=x.rider===poleR&&!isSprint?1:0;const pts=x.points!=null?x.points:0;
    return {d:x.rider,t,team:x.team||'',model:x.model||null,num:x.number!=null?String(x.number):'',p,label:lab,pts,g:isP?1:0,laps:x.laps||0,status:st,time:x.gap&&x.gap!=='0.000'&&x.pos!==1?'+'+x.gap:(x.pos===1?'':''),fl:x.bestLap||(fl?r.fast.time:''),fr:fl?1:0,de:1,dw:win?1:0,dp:pod?1:0,df:fl,dg:isP,dn:fin?0:1,ce:1,cw:win?1:0,cp:pod?1:0,cf:fl,cg:isP,cn:fin?0:1};});};
  let hasPts=false;
  for(const g of Object.values(groups)){const s=seasonsMap[g.year]||(seasonsMap[g.year]={year:g.year,races:[],drivers:[],teams:[]});
    const mains=g.items.filter(r=>SP.isMain(r.type));const sprints=g.items.filter(r=>!SP.isMain(r.type));
    const list=SP.sprintAsRace?g.items.map(r=>({r,sprint:[]})):mains.map(r=>({r,sprint:sprints}));
    if(!SP.sprintAsRace&&!mains.length&&sprints.length)list.push({r:sprints[0],sprint:[],sprintOnly:true});
    for(const {r,sprint,sprintOnly} of list){const rows=mkRows(r,!!sprintOnly);if(rows.some(x=>x.pts>0))hasPts=true;const c=D.circuits[r.circuit]||{name:'?',country:r.country,place:''};const lay=layoutFor(r.circuit,r.year);
      const nm=SP.raceName(r);let date=r.date,dateNote='';if(+r.date.slice(0,4)!==r.year){date=String(r.year)+r.date.slice(4);dateNote=`Date year corrected to the ${r.year} season; the archive records ${r.date}.`;}
      s.races.push({round:0,name:nm,date,dateNote,circuit:c.name,cid:r.circuit,lat:c.lat,lon:c.lon,circuitUrl:'',country:c.country||r.country||'',place:c.place||'',rows,sprint:sprint.map(sr=>mkRows(sr,true)).flat(),url:r.url||'',layout:lay,length:c.length?c.length/1000:null,turns:null,scheduledLaps:Math.max(0,...rows.map(x=>x.laps||0))||null,distance:null,trackType:'',direction:'',trackSource:'',lapSource:'',condition:r.condition||'',format:SP.formatLabel(r.type),sourceKind:r.sourceKind||'',supplementary:r.supplementary||null,sprintOnly:!!sprintOnly});}}
  const seasons=Object.values(seasonsMap).sort((a,b)=>a.year-b.year);
  for(const s of seasons){s.races.sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:0);s.races.forEach((r,i)=>r.round=i+1);
    const st=A.standings[String(s.year)];const wins={};for(const r of s.races)for(const x of r.rows)if(x.dw)wins[x.d]=(wins[x.d]||0)+1;
    if(st&&st.rows.length){s.drivers=[...st.rows].sort((a,b)=>a.pos-b.pos).map(x=>({id:x.rider,p:String(x.pos),pts:x.points||0,wins:wins[x.rider]||0,teams:[x.maker||'Unresolved make']}));s.standingsUrl=st.url||'';}
    const ms=A.manufacturerStandings?.[String(s.year)];const mwins={};for(const r of s.races)for(const x of r.rows)if(x.cw)mwins[x.t]=(mwins[x.t]||0)+1;
    if(ms&&ms.rows.length){s.teams=[...ms.rows].sort((a,b)=>a.pos-b.pos).map(x=>({id:x.maker,p:String(x.pos),pts:x.points||0,wins:mwins[x.maker]||0}));s.teamsBasis='published';}
    else if(s.drivers.length){const m={};for(const d of s.drivers){const t=d.teams[0];m[t]=(m[t]||0)+d.pts;}s.teams=Object.entries(m).sort((a,b)=>b[1]-a[1]).map(([id,pts],i)=>({id,p:String(i+1),pts,wins:mwins[id]||0}));s.teamsBasis='riders';}
  }
  for(const s of seasons)s.riders=s.drivers;D.seasons=seasons;D.riders=D.drivers;D.hasPts=hasPts;D.coverage=A.coverage||{};D.snapshot=A.snapshot;D.lastDate=A.lastDate;D.sourceCounts=A.sourceCounts||{};
  return D;}
const DATA=adapt(ARCHIVE,SPORT);
