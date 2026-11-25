// Prints the site's catalogue data (brands, series, article tables) as JSON.
// Usage: node tools/dump_catalog.js [path/to/index.html]
const fs = require('fs');
const path = process.argv[2] || 'dist/index.html';
const html = fs.readFileSync(path, 'utf8');
const m = html.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/);
if (!m) { console.error('component script not found'); process.exit(1); }
const src = 'class DCLogic { constructor(p) { this.props = p; } }\n' + m[1] + '\nreturn Component;';
const Component = new Function(src)();
const c = new Component({});
process.stdout.write(JSON.stringify({ catalog: c.rawCatalog(), articles: c.rawArticles(), stockAsOf: c.STOCK_AS_OF }));
