"""舊版 vs 新版 預演比賽。同一模型 gpt-5.6-luna、同一份考卷、每張 3 次。
用法：python3 bench.py <system> [trials]   system = old | new | bare
"""
import json,sys,base64,csv,re,time,urllib.request,concurrent.futures as cf,os,threading
SYS=sys.argv[1]; TRIALS=int(sys.argv[2]) if len(sys.argv)>2 else 3
KEY=open('/home/dsh/workspace/swarm/.swarm/keys/shared/openai-xiaozhen.token').read().strip()
MODEL='gpt-5.6-luna'
D=json.load(open('dataset.json')); E=json.load(open('emb-img.json'))
TEST=[d for d in D if d['split']=='test']; ALBUM=[d for d in D if d['split']=='album']
LABELS=sorted({d['label'] for d in D if d['label']!='_非地標'})
b64=lambda p:base64.b64encode(open(p,'rb').read()).decode()
img=lambda p:{'type':'input_image','image_url':'data:image/jpeg;base64,'+b64(p)}
cos=lambda a,b:sum(x*y for x,y in zip(a,b))

def ask(content):
    body={'model':MODEL,'input':[{'role':'user','content':content}]}
    for a in range(4):
        try:
            r=urllib.request.Request('https://api.openai.com/v1/responses',json.dumps(body).encode(),{'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
            t=time.time(); d=json.load(urllib.request.urlopen(r,timeout=180)); dt=time.time()-t
            txt=' '.join(c['text'] for o in d['output'] if o['type']=='message' for c in o['content'] if c['type']=='output_text')
            return txt,dt,d.get('usage',{})
        except Exception as e:
            err=e; time.sleep(3*(a+1))
    return 'ERROR '+str(err),0,{}

def parse(txt):
    m=re.search(r'\{.*\}',txt,re.S)
    try: return json.loads(m.group(0)).get('name','').strip()
    except Exception: return txt.strip()[:40]

# ---------- 舊版：Sheet 文字特徵全塞 prompt + Sheet 上的參考照片（照 rag-kit 原樣） ----------
OLD_ROWS=[r for r in csv.DictReader(open('old-sheet.csv')) if (r.get('地點名稱 (name)') or '').strip()]
FEAT=[('分類','分類'),('建築風格 (style)','風格'),('建築結構 (struct)','結構'),('材質 (material)','材質'),('開口形式','開口形式'),('功能用途 (function)','用途'),('簡介 (summary)','簡介')]
def old_context():
    s=f"虎尾地標資料庫（共 {len(OLD_ROWS)} 個地點）：\n\n"
    for i,r in enumerate(OLD_ROWS,1):
        s+=f"{i}. {r['地點名稱 (name)'].strip()}\n"
        for col,lab in FEAT:
            v=(r.get(col) or '').strip()
            if not v: continue
            if col=='簡介 (summary)': v=v[:120]
            s+=f"   {lab}：{v}\n"
        s+='\n'
    return s
OLD_PROMPT=old_context()+"""
請根據照片的視覺特徵（建築風格、材質、文字、雕塑、場景），從上面的地點清單中選出最匹配的一個。

規則：
- 如果照片明顯不是 18 個地標中任何一個（例：動物、自拍、植物、非建築物、外地照片），回答 name 為 'unknown'，confidence 為 'low'。寧可說『不確定』也不要瞎掰。
- 如果照片上有文字（碑文、門牌、布條），優先用文字判斷
- 如果沒有文字，用建築風格、材質、結構來比對

請用以下 JSON 格式回答：
{"name": "地點名稱", "reason": "判斷依據", "confidence": "high/medium/low"}

只輸出 JSON。"""
OLD_REFS=[('虎尾驛','oldref/虎尾驛-1-wiki.jpg'),('虎尾郡守官邸（雲林故事館）','oldref/雲林故事館-1-commons.jpg'),('合同廳舍','oldref/合同廳舍-2-commons.jpg')]
OLD_REF_PARTS=[]
for n,p in OLD_REFS: OLD_REF_PARTS+=[{'type':'input_text','text':f'\n[reference photo of 「{n}」]'},img(p)]
OLD_MAP=[('布袋戲館','雲林布袋戲館'),('郡役所','雲林布袋戲館'),('故事館','雲林故事館'),('郡守官邸','雲林故事館'),('虎尾驛','虎尾驛'),('鐵橋','虎尾鐵橋'),('合同廳舍','合同廳舍'),('酒精槽','糖廠酒精槽'),('宿舍','糖廠宿舍'),('第一工場','虎尾糖廠')]
def old_label(name):
    for k,v in OLD_MAP:
        if k in name: return v
    return '_非地標' if name.lower() in ('unknown','') else 'OTHER:'+name
def run_old(t):
    txt,dt,u=ask([{'type':'input_text','text':OLD_PROMPT}]+OLD_REF_PARTS+[{'type':'input_text','text':'\n[使用者照片]'},img('img/'+t['file'])])
    n=parse(txt); return old_label(n),n,txt,dt,u

# ---------- 新版：以圖搜圖找前 3 名 → Luna 看參考照片確認 ----------
T_LOW=0.72   # 用校準組（不在考卷內）決定：低於此分數直接「不認得」
def retrieve(f):
    best={}
    for a in ALBUM:
        s=cos(E[f],E[a['file']])
        if s>best.get(a['label'],(0,None))[0]: best[a['label']]=(s,a['file'])
    rank=sorted(best.items(),key=lambda x:-x[1][0])
    return rank
def run_new(t):
    rank=retrieve(t['file'])
    if rank[0][1][0]<T_LOW: return '_非地標','(相似度太低)','top1=%.3f'%rank[0][1][0],0,{}
    cands=rank[:3]; parts=[{'type':'input_text','text':'下面是 3 個候選地標，每個附上相簿裡最像的照片；最後一張是遊客拍的照片。\n判斷遊客照片是哪一個候選地標。如果都不是（例如只是附近的其他建築、食物、人像），name 回答 unknown。\n只輸出 JSON：{"name":"候選名稱或 unknown","reason":"一句話"}'}]
    for lbl,(s,_) in cands:
        sims=sorted([(cos(E[t['file']],E[a['file']]),a['file']) for a in ALBUM if a['label']==lbl],reverse=True)[:2]
        parts.append({'type':'input_text','text':f'\n候選：{lbl}'})
        for _,f in sims: parts.append(img('img/'+f))
    parts+=[{'type':'input_text','text':'\n遊客照片：'},img('img/'+t['file'])]
    txt,dt,u=ask(parts); n=parse(txt)
    lab=n if n in LABELS else ('_非地標' if n.lower() in ('unknown','') else 'OTHER:'+n)
    return lab,n,txt,dt,u

# ---------- 裸考：不給任何資料 ----------
def run_bare(t):
    txt,dt,u=ask([{'type':'input_text','text':'這是台灣雲林虎尾的哪個地標？不確定就回答 unknown。只輸出 JSON：{"name":"地標名稱或 unknown","reason":"一句話"}'},img('img/'+t['file'])])
    n=parse(txt); return old_label(n),n,txt,dt,u

RUN={'old':run_old,'new':run_new,'bare':run_bare}[SYS]
out=f'res-{SYS}.jsonl'; done=set()
if os.path.exists(out):
    for l in open(out): r=json.loads(l); done.add((r['file'],r['trial']))
jobs=[(t,k) for t in TEST for k in range(TRIALS) if (t['file'],k) not in done]
lock=threading.Lock(); print(SYS,'jobs',len(jobs),flush=True)
def work(j):
    t,k=j; lab,n,txt,dt,u=RUN(t)
    rec={'file':t['file'],'trial':k,'truth':t['label'],'pred':lab,'raw_name':n,'ok':lab==t['label'],'sec':round(dt,2),'in_tok':u.get('input_tokens'),'out_tok':u.get('output_tokens'),'reply':txt[:300]}
    with lock: open(out,'a').write(json.dumps(rec,ensure_ascii=False)+'\n')
    return rec
with cf.ThreadPoolExecutor(6) as ex:
    for i,r in enumerate(ex.map(work,jobs)):
        if i%30==0: print(i,r['truth'],'→',r['pred'],flush=True)
print('done',SYS)
