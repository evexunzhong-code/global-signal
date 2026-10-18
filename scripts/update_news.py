#!/usr/bin/env python3
"""Fetch public RSS and optionally translate/analyze using an OpenAI API key."""
import datetime as dt
import email.utils
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data/news.json"
FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("BBC Science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
]
TERMS = {
    "地缘政治": ["election", "war", "minister", "president", "government", "diplomat", "military", "sanction", "security", "conflict"],
    "经济金融": ["economy", "trade", "market", "inflation", "tariff", "bank", "interest rate", "stock", "investment", "business"],
    "科技产业": ["technology", "ai ", "artificial intelligence", "chip", "semiconductor", "software", "tech ", "cyber", "robot"],
    "能源气候": ["energy", "oil", "climate", "renewable", "gas ", "solar", "wind", "carbon", "emission"],
}
SIGNALS = {
    "地缘政治": "可能改变相关国家的政策预期和谈判空间。可持续关注官方表态和政策实施。",
    "经济金融": "可能影响市场预期、企业成本或国际资本流向。可关注后续经济数据与政策变化。",
    "科技产业": "可能影响技术竞争、产业布局及监管方向。可关注企业投资和政策落地情况。",
    "能源气候": "可能影响能源供需、成本或转型节奏。可关注价格变化和政策执行。",
}
def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", s or "")).strip()

def fetch_items(source, url):
    req = urllib.request.Request(url, headers={"User-Agent":"GlobalSignalRSSReader/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        tree = ET.fromstring(response.read(2000000))
    result = []
    for item in tree.findall(".//item"):
        title, link = clean(item.findtext("title")), (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue
        summary = clean(item.findtext("description"))
        try:
            date = email.utils.parsedate_to_datetime(item.findtext("pubDate", ""))
            if date.tzinfo is None:
                date = date.replace(tzinfo=dt.timezone.utc)
        except (TypeError, ValueError, IndexError):
            date = dt.datetime.now(dt.timezone.utc)
        age = (dt.datetime.now(dt.timezone.utc) - date).total_seconds()/3600
        if age > 96:
            continue
        haystack=(title+" "+summary).lower()
        counts={cat:sum(word in haystack for word in words) for cat,words in TERMS.items()}
        cat=max(counts,key=counts.get)
        result.append({"title":title,"summary":summary[:420],"category":cat,"source":source,
                       "published":date.isoformat(),"url":link,
                       "signal":SIGNALS[cat],"signal_type":"规则生成 · 通用观察",
                       "_score":counts[cat]*10+max(0,72-age)/12})
    return result

def ai_analysis(stories):
    key=os.environ.get("OPENAI_API_KEY","").strip()
    if not key:
        return False
    payload={"model":os.environ.get("OPENAI_MODEL","gpt-4.1-mini"),
             "response_format":{"type":"json_object"},
             "messages":[
                {"role":"system","content":"你是一位严谨的中文新闻编辑。根据输入的公开新闻标题和摘要，用中文写准确的title、summary和signal。signal解释可能的政治、经济或产业影响，明确推测性质，不编造未经提供的事实。仅输出JSON对象，格式为{\"stories\":[{\"title\":\"\",\"summary\":\"\",\"signal\":\"\"}]}，顺序及数量与输入相同。"},
                {"role":"user","content":json.dumps([{"title":s["title"],"summary":s["summary"]} for s in stories],ensure_ascii=False)}]}
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            raw=json.load(response)
        translations=json.loads(raw["choices"][0]["message"]["content"])["stories"]
        if len(translations)!=len(stories):
            raise ValueError("Returned wrong number of stories")
        if any(not all(isinstance(x.get(k),str) and x[k].strip() for k in ("title","summary","signal")) for x in translations):
            raise ValueError("Missing translated fields")
        for story,x in zip(stories,translations):
            for key in ("title","summary","signal"):
                story[key]=x[key].strip()[:700]
            story["signal_type"]="AI 辅助推断"
        return True
    except Exception as error:
        print("AI step failed, retaining RSS headlines:",str(error)[:200])
        return False

def main():
    candidates=[]
    for source,url in FEEDS:
        try:
            found=fetch_items(source,url)
            print(source, len(found))
            candidates.extend(found)
        except Exception as error:
            print("RSS unavailable:",source,str(error)[:200])
    if not candidates:
        raise RuntimeError("No live stories found; preserving previous data")
    seen=set()
    unique=[]
    for story in sorted(candidates,key=lambda x:(x["_score"],x["published"]),reverse=True):
        canonical=re.sub("[^a-z0-9]","",story["title"].lower())
        if canonical not in seen:
            seen.add(canonical)
            unique.append(story)
    selected=[]
    for cat in TERMS:
        selected.extend([s for s in unique if s["category"]==cat][:3])
    for s in unique:
        if len(selected)>=13: break
        if s not in selected: selected.append(s)
    selected=sorted(selected,key=lambda x:(x["_score"],x["published"]),reverse=True)[:13]
    ai=ai_analysis(selected)
    for story in selected:
        del story["_score"]
    data={"updated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"demo":False,
          "note":"新闻来自媒体RSS；信号为AI辅助推断，请核实原文。" if ai else "实时RSS英文新闻；信号仅为分类通用观察（尚未启用AI中文解读）。",
          "stories":selected}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Saved",len(selected),"stories; AI:",ai)
if __name__=="__main__":
    main()
