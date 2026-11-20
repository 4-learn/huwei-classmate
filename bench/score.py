import json,statistics as st
from collections import Counter,defaultdict
D={d['file']:d for d in json.load(open('dataset.json'))}
S={}
for s in ['bare','old','new']:
    R=[json.loads(l) for l in open(f'res-{s}.jsonl')]
    errs=sum(r['reply'].startswith('ERROR') for r in R)
    g=defaultdict(list)
    for r in R: g[D[r['file']]['angle']].append(r['ok'])
    lm=g['front']+g['hard']
    # 不穩：同一張 3 次答案不一致
    by=defaultdict(set)
    for r in R: by[r['file']].add(r['pred'])
    unstable=sum(len(v)>1 for v in by.values())
    # 地標照被說成 unknown（保守） vs 認成別的地標（認錯）
    wrong=Counter()
    for r in R:
        if r['truth']!='_非地標' and not r['ok']: wrong['說不認得' if r['pred']=='_非地標' else '認成別的']+=1
        if r['truth']=='_非地標' and not r['ok']: wrong['非地標被硬認']+=1
    secs=[r['sec'] for r in R if r['sec']>0]; tok=[r['in_tok'] for r in R if r['in_tok']]
    S[s]=dict(front=sum(g['front'])/len(g['front']),hard=sum(g['hard'])/len(g['hard']),landmark=sum(lm)/len(lm),reject=sum(g['nonlandmark'])/len(g['nonlandmark']),
              n=(len(g['front'])//3,len(g['hard'])//3,len(g['nonlandmark'])//3),unstable=unstable,wrong=dict(wrong),sec=st.median(secs) if secs else 0,tok=st.median(tok) if tok else 0,errs=errs,calls=len(secs))
    print(s,json.dumps(S[s],ensure_ascii=False))
json.dump(S,open('score.json','w'),ensure_ascii=False,indent=1)
