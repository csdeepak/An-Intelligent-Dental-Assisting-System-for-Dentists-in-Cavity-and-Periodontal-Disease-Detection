import sys, json, urllib.request
out={}
for d in sys.argv[1:]:
    try:
        req=urllib.request.Request(f"https://api.openalex.org/works/doi:{d}",headers={"User-Agent":"rce-citation-check/0.1"})
        m=json.load(urllib.request.urlopen(req,timeout=30))
        inv=m.get("abstract_inverted_index") or {}
        pos=sorted((p,w) for w,ps in inv.items() for p in ps)
        out[d]={"title":m.get("title"),"abstract":" ".join(w for _,w in pos),"is_retracted":m.get("is_retracted")}
    except Exception as e:
        out[d]={"error":str(e)}
json.dump(out,open("new_lit_abstracts.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
for d,v in out.items(): print(d, v.get("is_retracted"), (v.get("abstract") or v.get("error",""))[:900], "\n")
