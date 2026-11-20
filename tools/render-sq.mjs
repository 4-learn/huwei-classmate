import { chromium } from '/home/dsh/workspace/swarm/hives/4-learn/bubble-wall/node_modules/playwright/index.mjs';
import { readdirSync } from 'node:fs'; import { resolve, basename } from 'node:path';
const root = resolve(new URL('..', import.meta.url).pathname);
const only = process.argv.slice(2);
const files = readdirSync(`${root}/assets/src`).filter(f => /^s\d.*\.html$/.test(f)).filter(f => !only.length || only.includes(basename(f,'.html')));
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1400, height: 1200 } });
for (const f of files) { await p.goto(`file://${root}/assets/src/${f}`); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(300);
  await (await p.$('#card')).screenshot({ path: `${root}/assets/slides/${basename(f,'.html')}.png` }); console.log('ok', f); }
await b.close();
