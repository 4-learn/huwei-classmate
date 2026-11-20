// 把 assets/src/*.html 截成 assets/img/*.png（截 #card 元素）
// 用法：node tools/render.mjs [name ...]
import { chromium } from '/home/dsh/workspace/swarm/hives/4-learn/bubble-wall/node_modules/playwright/index.mjs';
import { readdirSync } from 'node:fs';
import { resolve, basename } from 'node:path';
const root = resolve(new URL('..', import.meta.url).pathname);
const only = process.argv.slice(2);
const files = readdirSync(`${root}/assets/src`).filter(f => f.endsWith('.html') && !f.startsWith('_'))
  .filter(f => !only.length || only.includes(basename(f, '.html')));
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
for (const f of files) {
  await p.goto(`file://${root}/assets/src/${f}`);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  const el = await p.$('#card');
  await el.screenshot({ path: `${root}/assets/img/${basename(f, '.html')}.png` });
  console.log('ok', f);
}
await b.close();
