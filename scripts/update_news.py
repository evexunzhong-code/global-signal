#!/usr/bin/env python3
"""Fetch public RSS and optionally translate/analyze using an OpenAI API key."""
import datetime as dt
import email.utils
import json
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
                       "signal":specific_signal(title, summary, cat),"signal_type":"免费规则分析 · 需人工核实",
                       "_score":counts[cat]*10+max(0,72-age)/12})
    return result

def specific_signal(title, summary, category):
    """Transparent rule-based observations; no paid API or claim of AI analysis."""
    text = (title + " " + summary).lower()
    rules = [
        (("tariff", "trade war", "import duty"), "贸易限制可能改变企业采购成本与供应链配置。后续关注关税生效范围、豁免情况及贸易伙伴回应。"),
        (("sanction", "sanctions"), "制裁措施的变化可能影响跨境交易与外交谈判。后续关注具体限制清单、执行日期和相关国家反应。"),
        (("election", "vote", "ballot"), "选举进展可能改变政策方向及政治联盟。后续关注正式结果、组阁安排与关键政策承诺。"),
        (("interest rate", "central bank", "inflation"), "货币政策或通胀变化可能影响融资成本与汇率预期。后续关注官方数据及央行会议。"),
        (("oil", "natural gas", "energy prices"), "能源供需变化可能影响生产成本与通胀。后续关注价格、产量和政策执行。"),
        (("ai ", "artificial intelligence", "chip", "semiconductor"), "这类进展可能改变技术竞争和相关企业的投资预期。后续关注产品落地、监管及投资决策。"),
        (("war", "military", "ceasefire"), "军事或停火进展可能影响地区安全与外交安排。后续关注各方正式声明及实际执行情况。"),
        (("climate", "emission", "deforestation"), "环境政策与实际变化可能影响减排进程和产业预期。后续关注官方统计及政策落实。"),
    ]
    for terms, observation in rules:
        if any(term in text for term in terms):
            return observation
    return SIGNALS[category]

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
    for story in selected:
        del story["_score"]
    data={"updated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"demo":False,
          "note":"永久免费模式：原文标题和摘要为英语；中文信号是关键词规则生成的观察，请核对报道原文。",
          "stories":selected}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Saved",len(selected),"stories; no paid API used")
if __name__=="__main__":
    main()
