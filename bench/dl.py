import json,urllib.request,urllib.parse,os,re,time,hashlib
UA={'User-Agent':'4-learn-course-bench/0.1 (yillkid@gmail.com)'}
def api(**p):
    p.update(format='json');u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA)))
def files(c): return [x['title'] for x in api(action='query',list='categorymembers',cmtitle=c,cmtype='file',cmlimit=100)['query']['categorymembers']]
L={}  # label -> list of titles
def add(lbl,cats,excl=(),only=None):
    for c in cats:
        for t in files(c):
            if any(e in t for e in excl): continue
            if only and not re.search(only,t): continue
            L.setdefault(lbl,[]).append(t)
add('虎尾驛',['Category:Huwei Station'],excl=['蒸汽火車頭'])
add('雲林布袋戲館',['Category:Yunlin Hand Puppet Museum','Category:Interior of the Yunlin Hand Puppet Museum','Category:Yunlin Hand Puppet Museum at night'],excl=['Whac-A-Mole','Night around','Statue of Huang'])
add('雲林故事館',['Category:Yunlin Story House'])
add('虎尾鐵橋',['Category:Huwei Sugar Factory Iron Bridge','Category:Huwei Sugar Factory Iron Bridge at night'])
add('合同廳舍',['Category:Huwei Joint Government Office Building'],excl=['Night around','Starbucks'])
add('虎尾糖廠',['Category:Huwei Sugar Factory'],only=r'Refinery Plant|Remote view|Scene in|虎尾糖廠0|Kobi factory')
add('糖廠酒精槽',['Category:Huwei Sugar Factory'],only=r'alcohol plant|Alcohol plant')
add('糖廠宿舍',['Category:Huwei Sugar Factory Dorms'])
for c in ['Category:Huwei Dexing Temple','Category:Huwei Water Tower',"Category:Taiwan Provincial Huwei Girls' High School",'Category:THSR Yunlin Station','Category:National Formosa University']:
    L.setdefault('_非地標',[]).extend(files(c))
os.makedirs('img',exist_ok=True); man=[]
for lbl,ts in L.items():
    for i in range(0,len(ts),40):
        r=api(action='query',titles='|'.join(ts[i:i+40]),prop='imageinfo',iiprop='url|extmetadata|mime',iiurlwidth=800)
        for pg in r['query']['pages'].values():
            ii=(pg.get('imageinfo') or [{}])[0]
            if not ii.get('thumburl') or 'image/' not in ii.get('mime',''): continue
            if ii['mime'] in ('image/tiff','image/svg+xml'): pass
            fn=hashlib.md5(pg['title'].encode()).hexdigest()[:10]+'.jpg'
            if not os.path.exists('img/'+fn):
                try:
                    data=urllib.request.urlopen(urllib.request.Request(ii['thumburl'],headers=UA),timeout=60).read()
                    open('img/'+fn,'wb').write(data); time.sleep(0.2)
                except Exception as e: print('fail',pg['title'],e); continue
            md=ii.get('extmetadata',{})
            man.append({'label':lbl,'file':fn,'title':pg['title'],'page':ii.get('descriptionurl'),'license':md.get('LicenseShortName',{}).get('value'),'artist':re.sub('<[^>]+>','',md.get('Artist',{}).get('value',''))[:80]})
json.dump(man,open('manifest.json','w'),ensure_ascii=False,indent=1)
from collections import Counter; print(Counter(m['label'] for m in man))
