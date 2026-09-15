#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公开军理题库采集器 V1：仅采集公开页面，不绕过付费/登录/验证码。"""
import argparse,json,re,sys,time
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
PUBLIC_HOSTS={"www.shititong.cn","shititong.cn","bu.cnies.org","cnies.org"}
def allowed(url):
    p=urlparse(url); host=p.netloc.lower().split(":")[0]
    if p.scheme not in ("http","https") or host.endswith("kyexam.com"): return False
    return host in PUBLIC_HOSTS
def fetch(url):
    if not allowed(url): raise RuntimeError("仅支持公开来源；不绕过付费或登录限制。")
    r=requests.get(url,headers={"User-Agent":UA},timeout=20);r.raise_for_status();r.encoding=r.apparent_encoding or r.encoding;return r.text
def clean(s): return re.sub(r"\s+"," ",s or "").strip()
def parse_question_page(url):
    soup=BeautifulSoup(fetch(url),"html.parser");text=clean(soup.get_text(" ",strip=True))
    typ=next((x for x in ["单选题","多选题","判断题","填空题"] if x in text),"")
    m=re.search(r"(?:答案|正确答案)\s*[:：]?\s*([A-DTF]+)",text,re.I);ans=m.group(1).upper() if m else ""
    opts=[]
    for L in "ABCD":
        m=re.search(rf"(?:^|\s){L}\s*[\.、]\s*(.*?)(?=\s+[ABCD]\s*[\.、]|答案|正确答案|$)",text,re.S)
        opts.append(clean(m.group(1)) if m else "")
    q=""
    if typ:
        tail=text.split(typ,1)[-1];m=re.search(r"(?:\d+\s*[\.、]?)?\s*(.*?)(?=\s*A\s*[\.、])",tail,re.S)
        if m:q=clean(m.group(1))
    if not q:q=clean(soup.title.get_text() if soup.title else "")
    return {"id":None,"subject":"军事理论","chapter":"","type":typ,"difficulty":"","question":q,"options":opts,"answer":ans,"source":url}
def collect(index_url,limit):
    soup=BeautifulSoup(fetch(index_url),"html.parser");links=[]
    for a in soup.find_all("a",href=True):
        u=urljoin(index_url,a["href"])
        if "/cha-kan/shiti/" in u and allowed(u) and u not in links:links.append(u)
    out=[]
    for i,u in enumerate(links[:limit],1):
        try:
            q=parse_question_page(u)
            if q["question"] and (q["answer"] or q["type"]):q["id"]=i;out.append(q)
            print(f"[{i}/{min(limit,len(links))}] {q['question'][:45]}",flush=True)
        except Exception as e:print(f"[跳过] {u}: {e}",file=sys.stderr)
        time.sleep(.15)
    return out
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("url");ap.add_argument("-o","--output",default="public_questions.json");ap.add_argument("-n","--limit",type=int,default=100);a=ap.parse_args()
    qs=collect(a.url,a.limit)
    with open(a.output,"w",encoding="utf-8") as f:json.dump(qs,f,ensure_ascii=False,indent=2)
    print(f"\n完成：{len(qs)} 道题 -> {a.output}")
