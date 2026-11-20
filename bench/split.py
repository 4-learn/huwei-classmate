import json,random
random.seed(20261121)
man=json.load(open('manifest.json')); E=json.load(open('emb-img.json')); R=json.load(open('emb-oldref.json'))
man.append({'label':'_非地標','file':'lunch-ai.jpg','title':'AI 生成便當','page':'','license':'AI-generated'})
cos=lambda a,b:sum(x*y for x,y in zip(a,b))
man=[m for m in man if m['file'] in E]
# 1) 與舊版參考照片近乎重複的照片：不能當考題（會偏袒舊版）
leak=[m['file'] for m in man if any(cos(E[m['file']],r)>0.93 for r in R.values())]
print('與舊版參考照近乎重複，排除:',len(leak))
man=[m for m in man if m['file'] not in leak]
# 2) 同地標內近乎重複的照片綁成一組，整組進同一邊
split={}
for lbl in sorted(set(m['label'] for m in man)):
    fs=[m['file'] for m in man if m['label']==lbl]
    groups=[]
    for f in fs:
        for g in groups:
            if any(cos(E[f],E[x])>0.93 for x in g): g.append(f);break
        else: groups.append([f])
    random.shuffle(groups)
    if lbl=='_非地標':
        pick=[g[0] for g in groups][:40]+(['lunch-ai.jpg'] if 'lunch-ai.jpg' not in [g[0] for g in groups][:40] else [])
        for f in pick: split[f]='test'
        continue
    n=len(fs); want=max(2,round(n*0.35)); t=0
    for g in groups:
        side='test' if t<want and len(g)<=want-t+1 else 'album'
        if side=='test': t+=len(g)
        for f in g: split[f]=side
    print(f'{lbl}: {n} 張, {len(groups)} 組, 考卷 {t}, 相簿 {n-t}')
for m in man: m['split']=split.get(m['file'],'unused')
json.dump(man,open('dataset.json','w'),ensure_ascii=False,indent=1)
from collections import Counter;print(Counter(m['split'] for m in man))
