/* The Stage's shared navigation, mounted by every atlas with its own accessors (tools: build.py puts this file before
   each application): a season timeline under the era strip — oldest on the left, newest on the right, the current season
   lit, the lens (all seasons or one era) deciding what it spans — with previous/next stepping through seasons and through
   the atlas's unit (race, match, draw, event), wrapping into the neighbouring season; ← → on the keyboard; and the sticky
   status line as a jump back to the timeline. Lists elsewhere start at today; timelines here flow forward. */
const StageNav=(()=>{
  let C=null,mounted=false;const $=s=>document.querySelector(s);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function seasons(){try{return C.seasons()||[];}catch(e){return [];}}
  function idx(ss){return ss.findIndex(s=>s.year===C.year());}
  function unitsOf(season){try{return (C.units&&season&&C.units(season))||[];}catch(e){return [];}}
  function onUnitTab(){return !!C.unitTab&&C.tab()===C.unitTab&&!C.whole();}
  function stepSeason(d){const ss=seasons();if(!ss.length)return;let i=idx(ss);if(i<0)i=d>0?-1:ss.length;const n=Math.min(ss.length-1,Math.max(0,i+d));if(n===i)return;C.setYear(ss[n].year);}
  function stepUnit(d){const ss=seasons();const i=idx(ss);if(i<0||!C.unitTab)return stepSeason(d);const us=unitsOf(ss[i]);const k=us.findIndex(u=>String(u.key)===String(C.unit()));const n=k+d;
    if(k>=0&&n>=0&&n<us.length){C.setUnit(us[n].key);return;}
    let j=i+d;while(j>=0&&j<ss.length){const vs=unitsOf(ss[j]);if(vs.length){C.setYear(ss[j].year);C.setUnit(d>0?vs[0].key:vs[vs.length-1].key);return;}j+=d;}}
  function draw(){const host=$('#seasonNav');if(!host||!C)return;const ss=seasons();if(!ss.length){host.innerHTML='';return;}const y=C.year();const i=idx(ss);const whole=C.whole();const first=ss[0].year,last=ss[ss.length-1].year;
    const bar=ss.map((s,k)=>`<button type="button" class="sy${s.year===y&&!whole?' on':''}${s.cancelled?' off':''}" data-year="${s.year}" title="${s.year}${s.cancelled?' · cancelled':''}" aria-label="${s.year}" aria-pressed="${s.year===y&&!whole}"></button>`).join('');
    let unitRow='';
    if(onUnitTab()&&i>=0){const us=unitsOf(ss[i]);const k=us.findIndex(u=>String(u.key)===String(C.unit()));
      if(k>=0){const p=us[k-1],n=us[k+1];const pj=!p?ss.slice(0,i).reverse().find(s=>unitsOf(s).length):null,nj=!n?ss.slice(i+1).find(s=>unitsOf(s).length):null;const name=(C.unitName||'').toLowerCase();
        unitRow=`<div class="unit-nav"><button type="button" class="ubtn" data-unit-step="-1"${p||pj?'':' disabled'} title="${p?'Previous '+name:pj?'Last '+name+' of '+pj.year:'No earlier '+name}">‹ ${p?esc(p.label):pj?'…'+pj.year:'—'}</button><span class="ucur"><b>${esc(us[k].label)}</b><small>${k+1} of ${us.length} · ${y}</small></span><button type="button" class="ubtn" data-unit-step="1"${n||nj?'':' disabled'} title="${n?'Next '+name:nj?'First '+name+' of '+nj.year:'No later '+name}">${n?esc(n.label):nj?nj.year+'…':'—'} ›</button></div>`;}}
    host.innerHTML=`<div class="season-strip"><button type="button" class="sbtn" data-season-step="-1"${i<=0?' disabled':''} aria-label="Previous season" title="Previous season">‹</button><div class="sbar" role="group" aria-label="Seasons in the lens, oldest on the left"><span class="tick">${first}</span><div class="sys">${bar}</div><span class="tick">${last}</span></div><button type="button" class="sbtn" data-season-step="1"${i<0||i>=ss.length-1?' disabled':''} aria-label="Next season" title="Next season">›</button></div><div class="season-cap"><span>${whole?`<b>Whole lens</b> · ${first}–${last} · ${ss.length} seasons`:`<b>${y}</b> · ${i+1} of ${ss.length} seasons in the lens · click a season, or ‹ › to step`}</span><span class="dim">${onUnitTab()?'← → steps '+(C.unitName||'unit').toLowerCase()+'s · shift ← → steps seasons':'← → steps seasons'}</span></div>${unitRow}`;
    const on=host.querySelector('.sy.on'),sb=host.querySelector('.sys');if(on&&sb&&sb.scrollWidth>sb.clientWidth)sb.scrollLeft=on.offsetLeft-sb.clientWidth/2;}
  function mount(cfg){C=cfg;if(mounted){draw();return;}mounted=true;
    const host=$('#seasonNav');if(!host)return;
    host.addEventListener('click',e=>{const b=e.target.closest('[data-year],[data-season-step],[data-unit-step]');if(!b||b.disabled)return;if(b.dataset.year){if(+b.dataset.year!==C.year()||C.whole())C.setYear(+b.dataset.year);}else if(b.dataset.seasonStep)stepSeason(+b.dataset.seasonStep);else stepUnit(+b.dataset.unitStep);});
    document.addEventListener('keydown',e=>{if(e.defaultPrevented||e.metaKey||e.ctrlKey||e.altKey)return;const t=e.target;if(t&&(/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(t.tagName)||t.isContentEditable))return;if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;const d=e.key==='ArrowRight'?1:-1;e.preventDefault();if(e.shiftKey||!onUnitTab())stepSeason(d);else stepUnit(d);});
    const st=$('#stageStatus');if(st){st.addEventListener('click',()=>{host.scrollIntoView({behavior:'smooth',block:'center'});host.classList.remove('flash');void host.offsetWidth;host.classList.add('flash');});st.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();st.click();}});}
    draw();}
  return {mount,draw,stepSeason,stepUnit};
})();
