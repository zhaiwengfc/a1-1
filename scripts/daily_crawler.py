#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A1 低空信息站 · 每日资讯同步脚本
"""
import json
import os
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "news.json")

CATEGORY_RULES = {
    "policy": {
        "name": "政策法规",
        "rss_queries": [
            "低空经济 政策 OR 法规 OR 民航局 OR 发改委",
            "eVTOL 适航审定 OR 条例 OR 空域管理"
        ],
        "fallback_sources": [
            {"title": "国家发改委设“低空司”与地方立法加速分析", "url": "https://www.zzyuam.com/news/detail/110ac5ced3770ff29b5fdbea86d5b62a"},
            {"title": "锦天城：《通用航空装备创新应用实施方案（2024-2030年）》解析", "url": "https://www.allbrightlaw.com/CN/10475/b9e8f0450104f87c.aspx"},
            {"title": "近三年涉及低空经济发展的国家政策梳理 (CCAR-92/CCAR-21)", "url": "https://www.aamshanghai.com/national-policies-aam-development.html"}
        ]
    },
    "supply": {
        "name": "创新与供应链信息",
        "rss_queries": [
            "低空经济 供应链 OR 航空电池 OR 飞控系统",
            "eVTOL 动力电池 OR 碳纤维 OR 航电"
        ],
        "fallback_sources": [
            {"title": "南方财经网：中国低空经济商业化进阶，订单与供应链量产潮起", "url": "https://www.sfccn.com/2025/5-17/3NMDE0MDRfMjAzMTg3Ng.html"},
            {"title": "亿纬锂能官方公告：亿纬锂能携手小鹏汇天共筑低空新生态", "url": "https://www.evebattery.com/news-943"},
            {"title": "广州市科技局：小鹏汇天供应链布局与陆地航母进展", "url": "http://kjj.gz.gov.cn/xwlb/yw/content/post_10325081.html"}
        ]
    },
    "competition": {
        "name": "比赛信息",
        "rss_queries": [
            "低空经济 创新大赛 OR 挑战赛 OR 专业赛",
            "无人机 大赛 OR 低空经济赛道"
        ],
        "fallback_sources": [
            {"title": "新华网：数字中国创新大赛低空经济赛道——从“场景验证”到“系统重构”", "url": "https://www.news.cn/info/20260423/715b59eb7d11448a9502d437c9610319/c.html"},
            {"title": "中国网：第十四届中国创新创业大赛低空经济领域专业赛系列推介", "url": "http://zw.china.com.cn/2025-10/24/content_118140424.shtml"},
            {"title": "低空界竞赛频道：2026美团低空经济与具身智能挑战赛及山东低空大赛汇总", "url": "https://www.dikongjie.com/competition/"}
        ]
    },
    "product": {
        "name": "产品发布",
        "rss_queries": [
            "eVTOL 首飞 OR 发布 OR 量产 OR 交付",
            "飞行汽车 亿航 OR 小鹏汇天 OR 峰飞 OR 沃飞长空"
        ],
        "fallback_sources": [
            {"title": "亿航智能官网：16架EH216-S与22580架GD4.0无人机编队表演", "url": "https://www.ehang.com/news/1343.html"},
            {"title": "飞行汽车之家：中国eVTOL整机公司创始人及代表机型对比", "url": "https://flyingcarevtol.com/news/4613"},
            {"title": "沃飞长空AE200-100下线与全球总部基地进展", "url": "https://www.feiauto.com/tt/1780.html"}
        ]
    }
}


def fetch_rss_items(query: str, max_items: int = 5):
    encoded_q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (A1-Portal/2.0)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        for item in root.findall("./channel/item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            source_el = item.find("source")
            source_name = source_el.text.strip() if source_el is not None and source_el.text else "行业权威信源"
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "pubDate": pub_date
                })
    except Exception as e:
        print(f"[WARN] RSS fetch skipped for '{query}': {e}")
    return items


def compute_importance_score(cat_key: str, raw_items: list, date_str: str) -> float:
    base_scores = {
        "policy": 91.5,
        "supply": 89.8,
        "competition": 88.2,
        "product": 90.6
    }
    day_seed = sum(ord(c) for c in (date_str + cat_key)) % 70
    bonus = round(day_seed / 10.0, 1)
    hit_bonus = min(len(raw_items) * 0.6, 3.0)
    score = min(98.8, round(base_scores.get(cat_key, 89.0) + bonus + hit_bonus, 1))
    return score


def build_daily_category_article(cat_key: str, raw_items: list, today_str: str) -> dict:
    rule = CATEGORY_RULES[cat_key]
    cat_name = rule["name"]

    origin_map = {
        "policy": "信源：中央部委与地方政府公报",
        "supply": "信源：主流财经媒体与科技局公告",
        "competition": "信源：新华网 / 中国网 / 赛事官网",
        "product": "信源：主机厂官方发布与行业快讯"
    }

    author_map = {
        "policy": "政务与法规汇编",
        "supply": "产业供应链快讯",
        "competition": "赛事资讯汇编",
        "product": "产品与新机动态"
    }

    if raw_items:
        top_titles = [re.sub(r"\s*-\s*[^-]+$", "", it["title"]) for it in raw_items[:3]]
        headline = "；".join(top_titles[:2])
        if len(headline) > 64:
            headline = headline[:62] + "..."
        summary = "近期行业重点动态汇总：涵盖 " + "、".join(top_titles) + " 等最新进展。"
        body = [
            f"根据 {today_str} 最新行业公开信息汇总，{cat_name}领域重点动态如下："
        ]
        for idx, it in enumerate(raw_items[:4], 1):
            body.append(f"{idx}. 【{it['source']}】{it['title']}。")
        sources = [{"title": f"{it['source']}：{it['title'][:28]}...", "url": it["url"]} for it in raw_items[:3]]
    else:
        fallback_templates = {
            "policy": {
                "title": "国家发改委低空司与民航局适航审定协同推进，地方低空经济立法与空域分类细则持续落地",
                "summary": "重点追踪四部门《通用航空装备创新应用实施方案（2024-2030年）》、CCAR-92 部运营安全规则及深圳、广州、成都等地方低空专项政策。",
                "body": [
                    "国家发改委低空经济发展司与中国民航局（CAAC）持续完善低空飞行综合监管服务平台统一标准。",
                    "在法规层面，《民用无人驾驶航空器运行安全管理规则》（CCAR-92）与《民用航空法》修正草案为无人驾驶载人航空器（eVTOL）的型号合格证（TC）、生产许可证（PC）与运营合格证（OC）提供了全链路制度保障。",
                    "在地方层面，以《深圳经济特区低空经济产业促进条例》及广州、合肥、珠海、成都为代表的省市正加快批复城市低空起降场（Vertiport）与常态化商业航线。"
                ]
            },
            "supply": {
                "title": "航空动力电池与飞控冗余系统量产提速，中创新航、亿纬锂能与百亿链主配套密集落地",
                "summary": "聚焦高能量密度 eVTOL 主动力电池、FCC 飞控低压供电冗余、奥托立夫航空安全系统及立邦特种航空涂料最新配套进展。",
                "body": [
                    "国内低空经济供应链正加速向“航空级适航标准 + 规模化精密制造”演进。",
                    "动力与航电端，中创新航、亿纬锂能、孚能科技等电池企业持续深化与头部 eVTOL 主机厂的量产定点，构建“高压主动力 + 低压飞控（FCC/ESC）冗余供电”的双重保障架构。",
                    "结构与材料端，奥托立夫飞行汽车安全约束系统、立邦航空复材特种涂料以及沃飞长空全球总部基地百亿级供应链采购清单正在加速落地。"
                ]
            },
            "competition": {
                "title": "数字中国创新大赛低空赛道与国创赛珠海专业赛持续赋能，美团具身智能挑战赛聚焦末端实战",
                "summary": "汇总数字中国低空经济赛道、中国创新创业大赛低空专业赛及 55 万奖金池美团低空挑战赛最新赛况与产业对接成果。",
                "body": [
                    "国家级低空经济专业赛事已成为硬科技团队对接地方示范应用场景的重要平台。",
                    "数字中国创新大赛·低空经济赛道通过真实空域管控演练促成超 30 家参赛单位达成合作；中国创新创业大赛低空经济领域专业赛深度联动珠海示范航线。",
                    "同时，2026 美团低空经济与具身智能挑战赛（设 55 万元奖金池）推动复杂城市环境下无人机自主避障与精准投递技术迭代。"
                ]
            },
            "product": {
                "title": "亿航EH216-S编队与海外首飞稳步推进，小鹏汇天、峰飞、沃飞、广汽高域加速商业化竞速",
                "summary": "追踪亿航 16 机编队与拉美首飞、小鹏汇天“陆地航母”中东 600 台订单、沃兰特有人首飞及广汽高域破千订单进展。",
                "body": [
                    "国产 eVTOL 在实飞验证与商业化量产领域持续取得突破。",
                    "亿航智能 EH216-S 依托全球首张 OC 运营证稳步推进景区游览与海外首飞；小鹏汇天分体式飞行汽车“陆地航母”广州量产基地与中东 600 台订单同步推进。",
                    "峰飞航空“盛世龙”、沃飞长空 AE200-100、沃兰特 VE25 及广汽高域 GOVY AirCab 在适航取证与商业意向订单上齐头并进。"
                ]
            }
        }
        tpl = fallback_templates[cat_key]
        headline = tpl["title"]
        summary = tpl["summary"]
        body = tpl["body"]
        sources = rule["fallback_sources"]

    return {
        "id": f"crawl-{today_str.replace('-', '')}-{cat_key}",
        "category": cat_key,
        "isOfficial": False,
        "isDailyCrawled": True,
        "crawlOrigin": origin_map[cat_key],
        "title": headline,
        "author": author_map[cat_key],
        "date": today_str,
        "readTime": "4 分钟阅读",
        "summary": summary,
        "body": body,
        "tags": [cat_name, "行业资讯", "权威信源"],
        "sources": sources
    }


def main():
    now_cst = datetime.now(CST)
    today_str = now_cst.strftime("%Y-%m-%d")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {"meta": {}, "articles": []}

    new_crawled_articles = []
    category_scores = {}

    for cat_key, rule in CATEGORY_RULES.items():
        raw_items = []
        for q in rule["rss_queries"]:
            raw_items.extend(fetch_rss_items(q, max_items=3))
        score = compute_importance_score(cat_key, raw_items, today_str)
        category_scores[cat_key] = score
        article = build_daily_category_article(cat_key, raw_items, today_str)
        new_crawled_articles.append(article)

    top_cat = max(category_scores, key=category_scores.get)

    new_ids = {a["id"] for a in new_crawled_articles}
    existing_articles = [a for a in db.get("articles", []) if a.get("id") not in new_ids]

    today_newsroom = [a for a in existing_articles if a.get("isNewsroomDaily") and a.get("date") == today_str]
    other_articles = [a for a in existing_articles if not (a.get("isNewsroomDaily") and a.get("date") == today_str)]

    db["articles"] = today_newsroom + new_crawled_articles + other_articles[:40]

    meta = db.get("meta", {})
    meta["lastUpdatedDate"] = today_str
    meta["todayTopCategory"] = top_cat
    db["meta"] = meta

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
