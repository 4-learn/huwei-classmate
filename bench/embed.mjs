// 用法：node embed.mjs <imgdir> <out.json>  → {file: [512 floats]}
import { AutoProcessor, CLIPVisionModelWithProjection, RawImage } from '@huggingface/transformers';
import { readdirSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
const [dir, out] = process.argv.slice(2);
const id = 'Xenova/clip-vit-base-patch32';
const proc = await AutoProcessor.from_pretrained(id); const m = await CLIPVisionModelWithProjection.from_pretrained(id);
const E = existsSync(out) ? JSON.parse(readFileSync(out)) : {};
for (const f of readdirSync(dir).filter(f => /\.(jpe?g|png)$/i.test(f))) {
  if (E[f]) continue;
  try { const im = await RawImage.read(`${dir}/${f}`); const o = await m(await proc(im));
    const v = Array.from(o.image_embeds.data); const n = Math.hypot(...v); E[f] = v.map(x => +(x / n).toFixed(5));
  } catch (e) { console.error('fail', f, e.message); }
}
writeFileSync(out, JSON.stringify(E)); console.log('embedded', Object.keys(E).length);
