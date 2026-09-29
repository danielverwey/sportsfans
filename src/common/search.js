/* Find anything on the Stage (shared by every atlas, mounted with the atlas's own index): one box in the sticky bar that
   searches every name the atlas knows — people, teams, venues, seasons, the unit (races, matches, draws, events,
   podiums) — and opens the view straight away. Diacritics and case do not matter, words may come in any order, a match at
   the start of a word ranks first. ↑ ↓ move, Enter opens, Esc closes; "/" focuses the box from anywhere. */
const StageSearch=(()=>{
  let C=null,items=null,hits=[],sel=-1,box=null,pop=null,input=null,hideT=null;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fold=s=>String(s??'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[’'`]/g,'');
  function build(){items=[];for(const g of C.groups){let list=[];try{list=g.items()||[];}catch(e){console.error('search index',g.kind,e);}for(const it of list){if(!it||!it.label)continue;items.push({kind:g.kind,label:String(it.label),sub:it.sub?String(it.sub):'',open:it.open,rank:+it.rank||0,f:fold(it.label+' '+(it.sub||'')+' '+(it.keys||[]).join(' ')),fl:fold(it.label)});}}}
  function search(q){const toks=fold(q).split(/\s+/).filter(Boolean);if(!toks.length)return [];if(!items)build();const out=[];
    for(const it of items){let score=0;for(const t of toks){const i=it.f.indexOf(t);if(i<0){score=-1;break;}score+=(i===0||it.f[i-1]===' '||it.f[i-1]==='-')?3:1;}if(score<0)continue;if(it.fl.startsWith(toks[0]))score+=5;else if(it.fl.split(' ').some(w=>w.startsWith(toks[0])))score+=2;if(it.fl===toks.join(' '))score+=8;out.push([score-Math.min(2,it.label.length/40)+Math.log1p(it.rank)*0.7,it]);}   /* the better known first among equal matches */
    out.sort((a,b)=>b[0]-a[0]);const per={},res=[];const cap=C.perGroup||6;
    for(const [,it] of out){per[it.kind]=(per[it.kind]||0)+1;if(per[it.kind]<=cap)res.push(it);if(res.length>=(C.max||30))break;}
    const order=C.groups.map(g=>g.kind);return res.sort((a,b)=>order.indexOf(a.kind)-order.indexOf(b.kind));}
  function hl(s,q){const toks=fold(q).split(/\s+/).filter(Boolean);if(!toks.length)return esc(s);const f=fold(s);let marks=[];for(const t of toks){let i=f.indexOf(t);while(i>=0&&marks.length<8){marks.push([i,i+t.length]);i=f.indexOf(t,i+1);}}
    if(f.length!==s.length)return esc(s);marks.sort((a,b)=>a[0]-b[0]);let out='',p=0;for(const [a,b] of marks){if(a<p)continue;out+=esc(s.slice(p,a))+'<mark>'+esc(s.slice(a,b))+'</mark>';p=b;}return out+esc(s.slice(p));}
  function render(){const q=input.value;hits=search(q);sel=hits.length?0:-1;if(!q.trim()){pop.hidden=true;pop.innerHTML='';input.setAttribute('aria-expanded','false');return;}
    if(!hits.length){pop.innerHTML=`<div class="ss-none">Nothing called “${esc(q)}” in this atlas</div>`;pop.hidden=false;input.setAttribute('aria-expanded','true');return;}
    let last='';pop.innerHTML=hits.map((it,i)=>{const g=it.kind!==last?`<div class="ss-group">${esc(it.kind)}</div>`:'';last=it.kind;return g+`<button type="button" class="ss-item${i===sel?' on':''}" data-i="${i}" role="option" aria-selected="${i===sel}"><b>${hl(it.label,q)}</b>${it.sub?`<small>${hl(it.sub,q)}</small>`:''}</button>`;}).join('')+`<div class="ss-hint">↑ ↓ move · Enter opens · Esc closes</div>`;pop.hidden=false;input.setAttribute('aria-expanded','true');}
  function move(d){if(!hits.length)return;sel=(sel+d+hits.length)%hits.length;[...pop.querySelectorAll('.ss-item')].forEach((b,i)=>{b.classList.toggle('on',i===sel);b.setAttribute('aria-selected',i===sel);if(i===sel)b.scrollIntoView({block:'nearest'});});}
  function choose(i){const it=hits[i];if(!it)return;pop.hidden=true;input.value='';input.blur();try{it.open();}catch(e){console.error(e);}const st=document.querySelector('#stage');if(st)st.scrollIntoView({behavior:'smooth',block:'start'});}
  function mount(cfg){C=cfg;items=null;if(box)return;const bar=document.querySelector('.stagebar');if(!bar)return;
    box=document.createElement('div');box.className='ss';box.innerHTML=`<input id="stageSearch" type="search" autocomplete="off" spellcheck="false" placeholder="${esc(C.placeholder||'Find anything')}" aria-label="Find anything in this atlas" role="combobox" aria-expanded="false" aria-autocomplete="list"><kbd class="ss-key" aria-hidden="true">/</kbd><div class="ss-pop" role="listbox" hidden></div>`;
    const spacer=bar.querySelector('.spacer');bar.insertBefore(box,spacer||null);input=box.querySelector('input');pop=box.querySelector('.ss-pop');
    input.addEventListener('input',render);input.addEventListener('focus',()=>{clearTimeout(hideT);if(input.value.trim())render();});
    input.addEventListener('blur',()=>{hideT=setTimeout(()=>{pop.hidden=true;input.setAttribute('aria-expanded','false');},180);});
    input.addEventListener('keydown',e=>{if(e.key==='ArrowDown'){e.preventDefault();move(1);}else if(e.key==='ArrowUp'){e.preventDefault();move(-1);}else if(e.key==='Enter'){e.preventDefault();if(sel>=0)choose(sel);}else if(e.key==='Escape'){if(input.value){input.value='';render();}else input.blur();}});
    pop.addEventListener('mousedown',e=>e.preventDefault());pop.addEventListener('click',e=>{const b=e.target.closest('[data-i]');if(b)choose(+b.dataset.i);});
    document.addEventListener('keydown',e=>{if(e.key!=='/'||e.metaKey||e.ctrlKey||e.altKey)return;const t=e.target;if(t&&(/^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)||t.isContentEditable))return;e.preventDefault();input.focus();input.select();});}
  return {mount,invalidate(){items=null;},search};
})();
