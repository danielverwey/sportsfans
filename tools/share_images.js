// Share images: one 1200×630 card per atlas and one for the landing page, drawn from the built hub's river miniatures.
//   python build.py && node tools/share_images.js        → src/hub/share/<key>.png (+ apex.png); build.py copies them to docs/share/
// Run this only when a river changes materially (a new sport, a rebuilt archive); the PNGs are committed so the deploy needs no browser.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.join(__dirname, '..'); const DOCS = path.join(ROOT, 'docs'); const OUT = path.join(ROOT, 'src', 'hub', 'share');
const hub = fs.readFileSync(path.join(DOCS, 'index.html'), 'utf8');
const cards = [...hub.matchAll(/class="sport" href="([a-z0-9]+)\/" style="--sc:(#[0-9a-fA-F]{6})"[^>]*><span class="tag">([^<]*)<\/span><p class="eyebrow">([^<]*)<\/p><h2>(.*?)<\/h2><div class="prev">(<svg.*?<\/svg>)<\/div>/gs)]
  .map(m => ({ key: m[1], colour: m[2], span: m[3], eyebrow: m[4], name: m[5].replace(/<[^>]+>/g, ''), svg: m[6] }));
if (!cards.length) { console.error('no cards found in docs/index.html — run python build.py first'); process.exit(1); }
const FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@1,800;1,900&family=Barlow:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap">';
const CSS = `*{box-sizing:border-box}html,body{margin:0;width:1200px;height:630px;overflow:hidden}
body{background:#07080a;color:#f4f4f2;font-family:Barlow,"Helvetica Neue",Arial,sans-serif;position:relative;
  background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.012) 0 2px,transparent 2px 6px),repeating-linear-gradient(-45deg,rgba(255,255,255,.012) 0 2px,transparent 2px 6px)}
.brand{position:absolute;left:64px;top:52px;font:900 44px/1 "Barlow Condensed","Arial Narrow",sans-serif;font-style:italic;letter-spacing:-.02em;text-transform:uppercase}
.brand i{color:var(--sc);font-style:italic}
.strap{position:absolute;left:64px;top:104px;font:600 15px "JetBrains Mono",monospace;letter-spacing:.3em;text-transform:uppercase;color:#8b9099}
.eyebrow{position:absolute;left:64px;top:170px;font:700 16px "JetBrains Mono",monospace;letter-spacing:.24em;text-transform:uppercase;color:var(--sc)}
h1{position:absolute;left:60px;top:196px;margin:0;font:900 120px/.9 "Barlow Condensed","Arial Narrow",sans-serif;font-style:italic;letter-spacing:-.03em;text-transform:uppercase;max-width:1080px}
.tag{position:absolute;right:64px;top:60px;font:700 16px "JetBrains Mono",monospace;letter-spacing:.2em;color:var(--sc);border:2px solid var(--sc);border-radius:8px;padding:8px 14px}
.river{position:absolute;left:0;right:0;bottom:0;height:250px}
.river svg{width:100%;height:100%;display:block;opacity:.95}
.site{position:absolute;right:64px;bottom:262px;font:600 15px "JetBrains Mono",monospace;letter-spacing:.3em;text-transform:uppercase;color:#8b9099}
.hubgrid{position:absolute;left:0;right:0;bottom:0;height:230px;display:grid;grid-template-columns:repeat(3,1fr);gap:0}
.hubgrid svg{width:100%;height:100%;display:block;opacity:.9}
.hubgrid > div{position:relative;overflow:hidden;height:115px}`;
const cardHtml = c => `<!doctype html><html><head><meta charset="utf-8">${FONTS}<style>${CSS}</style></head><body style="--sc:${c.colour}">
<div class="brand">APEX <i>/</i></div><div class="strap">sportsfans.co.za · sports atlases from open data</div><div class="tag">${c.span}</div>
<div class="eyebrow">${c.eyebrow}</div><h1${c.name.length > 14 ? ' style="font-size:100px"' : ''}>${c.name}</h1><div class="site">The whole record, drawn to be explored</div>
<div class="river">${c.svg}</div></body></html>`;
const hubHtml = () => `<!doctype html><html><head><meta charset="utf-8">${FONTS}<style>${CSS}</style></head><body style="--sc:#FF8000">
<div class="brand">APEX <i>/</i> Sportsfans</div><div class="strap">sportsfans.co.za · sports atlases drawn from open data</div>
<div class="eyebrow">${cards.length} atlases · River · Stage · every venue</div><h1 style="font-size:78px;top:200px">The whole record,<br>drawn to be explored</h1>
<div class="hubgrid">${cards.slice(0, 6).map(c => `<div>${c.svg}</div>`).join('')}</div></body></html>`;
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const c of cards) {
    await p.setContent(cardHtml(c), { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(200);
    await p.screenshot({ path: path.join(OUT, `${c.key}.png`), type: 'png' }); console.log('share image', c.key);
  }
  await p.setContent(hubHtml(), { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(200);
  await p.screenshot({ path: path.join(OUT, 'apex.png'), type: 'png' }); console.log('share image apex');
  await b.close();
})();
