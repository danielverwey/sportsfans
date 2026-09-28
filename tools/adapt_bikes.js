// Runs the bikes adapter outside the browser so the reading edition can be generated from the same shape the atlas uses.
// Usage: node tools/adapt_bikes.js motogp|sbk  →  the adapted archive as JSON on stdout
const fs = require('fs'), path = require('path'), vm = require('vm');
const tag = process.argv[2]; const root = path.resolve(__dirname, '..'); const d = path.join(root, 'src', 'bikes');
const A = JSON.parse(fs.readFileSync(path.join(root, 'data', tag + '.json'), 'utf8')); const assets = JSON.parse(fs.readFileSync(path.join(d, `assets_${tag}.json`), 'utf8'));
const src = [fs.readFileSync(path.join(d, `config_${tag}.js`), 'utf8'), 'SPORT.osm=' + JSON.stringify(assets.osm || {}) + ';SPORT.venues=' + JSON.stringify(assets.venues) + ';', fs.readFileSync(path.join(d, 'adapter.js'), 'utf8'), 'JSON.stringify(DATA)'].join('\n');
const ctx = { window: { ARCHIVE: A }, document: { getElementById: () => null } }; vm.createContext(ctx);
process.stdout.write(vm.runInContext(src, ctx));
