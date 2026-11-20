// 用 chromium canvas 把照片縮到寬 1000、存 jpg
import { chromium } from '/home/dsh/workspace/swarm/hives/4-learn/bubble-wall/node_modules/playwright/index.mjs';
import { readdirSync, writeFileSync, readFileSync } from 'node:fs';
const [src, dst] = process.argv.slice(2);
const b = await chromium.launch(); const p = await b.newPage();
for (const f of readdirSync(src).filter(f => /\.(jpe?g|png)$/i.test(f))) {
  const mime = f.endsWith('png') ? 'image/png' : 'image/jpeg';
  const data = `data:${mime};base64,` + readFileSync(`${src}/${f}`).toString('base64');
  const out = await p.evaluate(async (data) => {
    const img = new Image(); img.src = data; await img.decode();
    const w = Math.min(1000, img.naturalWidth), h = Math.round(img.naturalHeight * w / img.naturalWidth);
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    c.getContext('2d').drawImage(img, 0, 0, w, h);
    return c.toDataURL('image/jpeg', 0.82).split(',')[1];
  }, data);
  writeFileSync(`${dst}/${f.replace(/\.(png|jpe?g)$/i, '.jpg')}`, Buffer.from(out, 'base64'));
  console.log(f);
}
await b.close();
