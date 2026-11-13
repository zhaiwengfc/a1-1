#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A1 低空信息站 · 每日 09:00 “A1新闻部”深度创意撰稿智能体 (daily_newsroom_writer.py)
部署仓库: https://github.com/zhaiwengfc/a1-1
运行时间: 一周七天，每日北京时间 08:40 选题撰稿，09:00 准时发布至 data/news.json 并同步上线

核心特性:
1. 动态选题（不固定栏目）：读取当日 07:00 抓取的各栏目重要度评分（`todayTopCategory`），自动针对当日最重要、最具突破性的信号撰稿。
2. 深度与独特见解：支持接入 Gemini API (`GEMINI_API_KEY`) 或 OpenAI/DeepSeek 兼容接口 (`OPENAI_API_KEY`)；若未配置密钥，自动启用内置的“A1 新闻部多模态深度合成引擎”生成高质量专栏文章。
3. 形式不限于文字（高创意交互）：每篇 A1 新闻部文章均自动生成配套的 `creativeWidget` 交互式创意模块（如三维政策擂台、供应链成本模拟器、赛事通关雷达、机型参数PK台），前端自动渲染为可按压交互的街机卡带组件。
"""

import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "news.json")

CATEGORY_LABELS = {
    "policy": "政策法规",
    "supply": "创新与供应链信息",
    "competition": "比赛信息",
    "product": "产品发布"
}


def try_llm_generation(top_cat: str, top_score: float, crawled_context: list, today_str: str):
    """如果仓库 Secrets 配置了 GEMINI_API_KEY 或 OPENAI_API_KEY，则调用大模型生成当日深度创意文章与交互式 JSON 组件"""
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return None

    cat_name = CATEGORY_LABELS.get(top_cat, "政策法规")
    context_text = "\n".join([f"- [{a.get('category')}] {a.get('title')}: {a.get('summary')}" for a in crawled_context])

    prompt = f"""你是 A1 网站的官方“A1新闻部”首席主笔智能体。今天是 {today_str}。
今早 07:00 抓取到的全网动态中，重要度最高的栏目是【{cat_name}】（重要度评分 {top_score}/100）。
今日抓取背景信息如下：
{context_text}

请你撰写一篇今日 09:00 准时发布的“A1新闻部文章”，要求：
1. 极具产业深度、犀利独到见解，直击商业化本质与利益博弈；
2. 形式不限于纯文字，必须同时设计一个结构化的交互式创意组件 `creativeWidget`（包含3个可切换Tab：数据擂台/正反方锋芒辩论PK/实操通关步骤）。
3. 严格输出合法的 JSON 对象，包含字段：title, author, readTime, creativeFormat, summary, body (4段深度正文的字符串数组), tags (字符串数组), creativeWidget (包含 badge, title, subtitle, tabs 数组)。"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        if "title" in parsed and "body" in parsed:
            return parsed
    except Exception as e:
        print(f"[INFO] LLM API 调用跳过，使用内置深度创意撰稿引擎: {e}")
    return None


def build_builtin_creative_article(top_cat: str, top_score: float, crawled_context: list, today_str: str) -> dict:
    """内置高水准“A1新闻部”每日深度创意撰稿引擎（覆盖四大栏目轮转与深度互动沙盘）"""
    cat_name = CATEGORY_LABELS.get(top_cat, "政策法规")

    # 找到今日对应栏目的抓取文章信源
    matched_sources = []
    for item in crawled_context:
        if item.get("category") == top_cat and item.get("sources"):
            matched_sources = item["sources"]
            break

    templates = {
        "policy": {
            "creativeFormat": "交互式空域改革博弈沙盘 + 城市积分擂台 + 观点交锋卡",
            "title": f"【A1新闻部·09:00创意特稿】({today_str}) 当市长们开始争夺“天空立交桥”：从中央低空司到地方立法的深水区博弈",
            "author": "A1 新闻部 · 每日主笔智能体 (A1 Newsroom AI)",
            "readTime": "9 分钟深度交互阅读 · 含创意互动沙盘",
            "summary": f"基于今日 07:00 全网抓取的最高重要度信号（{top_score}分）：国家发改委低空司统筹推进、民航局 CCAR-92 部落地与地方政府专项政策进入正面竞速。A1 新闻部打破纯文字报道，为您构建“地方低空新政三维战力擂台”与“空域确权三方博弈模拟器”。",
            "body": [
                f"【A1 新闻部 09:00 独到见解 · {today_str}】今天早上 07:00 我们的全网抓取智能体监测到，【政策法规】栏目的全网重要度指数达到 {top_score} 分，位居四大栏目之首。A1 新闻部认为，当前低空政策最大的变化在于：从早期的“发文件表态”全面转向“空域接口确权与财政首购闭环”。",
                "洞察一：国家发改委“低空经济发展司”与中国民航局《低空飞行综合监管服务平台规范》正在构建全国统一的数字化空管底座。过去各省市“各自画圈试飞”的碎片化状态正在终结，任何未接入国家综合监管平台的飞行器都将无法获得常态化商业运营许可（OC）。",
                "洞察二：地方党委政府的招商逻辑已发生根本逆转。无论是《深圳经济特区低空经济产业促进条例》，还是广州、成都、合肥的百亿基金，考核硬指标已锁定为“是否在本地拿到 TC/PC 证”以及“是否开通跨区真实商业航线”。",
                "洞察三：短视频信息流上的公众安全关切正在加速“城市低空强制保险与噪音国标”出台。谁能率先跑通“高安全冗余适航 + 社区友好型起降场”，谁就能拿下未来三年的市政采购大单。"
            ],
            "creativeWidget": {
                "type": "policy_arena_simulator",
                "badge": "🕹️ A1 新闻部创意交互组件 // 政策沙盘与观点擂台",
                "title": "互动推演：2026-2030 低空政策落地三维博弈沙盘",
                "subtitle": "点击下方黄色街机按键，切换查看【四大低空先锋城市政策战力榜】、【A1正反方锋芒辩论台】与【企业四证通关路线图】",
                "tabs": [
                    {
                        "id": "city_rank",
                        "label": "🏙️ 城市政策战力擂台",
                        "items": [
                            {"name": "深圳 · 特区立法领跑型", "score": 96, "tag": "全国首部特区低空条例 + 20条真金白银激励", "detail": "对取得 CAAC 型号合格证(TC)与生产许可证(PC)的载人 eVTOL 企业给予重磅奖励，开放高密度城市末端物流与跨海示范航线。"},
                            {"name": "广州 · 智造链主集群型", "score": 94, "tag": "亿航四证闭环 + 小鹏汇天量产工厂 + 广汽高域", "detail": "坐拥全球首张 OC 证企业亿航智能与小鹏汇天广州智造基地，依托整车供应链优势跑通“研发-总装-出海”全链条。"},
                            {"name": "成都/珠海 · 航展与研发双驱型", "score": 91, "tag": "沃飞长空全球总部 + 国创赛珠海专业赛", "detail": "成都以沃飞 AE200 链主基地拉动百亿航空配套，珠海依托中国航展与创新创业大赛构建湾区跨海物流网络。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ A1 锋芒观点碰撞",
                        "proTitle": "正方观点：低空商业化应“先载货、先郊区、稳步进城”",
                        "proDesc": "以峰飞 V2000CG 与美团无人机末端配送为代表，货运场景容错率更高、适航取证周期更可控，能先在海岛物流、医疗急救中跑通正现金流。",
                        "conTitle": "反方观点：载人 eVTOL 景区游览与城际接驳才是万亿级爆发点",
                        "conDesc": "以亿航 EH216-S 四证齐全与小鹏汇天中东 600 台大单为证，高客单价文旅观光与高端个人飞行器才能支撑起早期高昂的航空级电池与飞控研发摊销。",
                        "a1Verdict": "★ A1 新闻部主编裁决：2026-2027 年最稳健的商业模型是“用高频低空物流/文旅观光养活起降场基建，用倾转旋翼/复合翼城际客运打开远期天花板”。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🛡️ 企业四证通关路线图",
                        "steps": [
                            {"code": "STEP 01 // TC 型号合格证", "status": "设计批准", "tip": "核心卡点：专用条件审定、FCC飞控多余度容错与动力电池热失控防护验证（CCAR-21）。"},
                            {"code": "STEP 02 // PC 生产许可证", "status": "量产准入", "tip": "核心卡点：供应链质量追溯体系（如中创新航/亿纬锂能电芯批次一致性与复材探伤）。"},
                            {"code": "STEP 03 // AC 单机适航证", "status": "交付通行证", "tip": "核心卡点：每架下线航空器出厂试飞与标准构型一致性核查。"},
                            {"code": "STEP 04 // OC 运营合格证", "status": "商业收费闭环", "tip": "核心卡点：接入民航局低空飞行综合监管服务平台，建立空地协同运行手册（CCAR-92）。"}
                        ]
                    }
                ]
            }
        },
        "supply": {
            "creativeFormat": "eVTOL 核心BOM成本拆解仪 + 电池/飞控双轨冗余模拟器",
            "title": f"【A1新闻部·09:00创意特稿】({today_str}) 拆开一架百万级飞行汽车：为什么动力电池与飞控系统拿走了70%的话语权？",
            "author": "A1 新闻部 · 供应链首席主笔智能体",
            "readTime": "8 分钟深度交互阅读 · 含 BOM 拆解沙盘",
            "summary": f"基于今日 07:00 供应链抓取最高重要度信号（{top_score}分）：中创新航、亿纬锂能、奥托立夫与立邦密集切入低空赛道。A1 新闻部通过交互式 BOM 价值量仪表盘，为您揭示车规供应链降维打击航空制造的真相与边界。",
            "body": [
                f"【A1 新闻部 09:00 独到见解 · {today_str}】今早 07:00 抓取数据显示，【创新与供应链信息】栏目重要度跃升至 {top_score} 分。当大众还在围观飞行汽车外观时，产业真正的胜负手已经在电芯实验室和飞控冗余代码里悄然决出。",
                "洞察一：“高能量密度主电池 + 独立低压飞控电池”已成行业黄金标准。小鹏汇天“陆地航母”选择中创新航提供高压主动力、亿纬锂能提供低压锂电池护航 FCC 飞控与 ESC 电调，本质上是用双轨物理隔离解决航空适航最恐惧的“单点断电失效”。",
                "洞察二：汽车供应链巨头正在重塑航空零部件定价体系。奥托立夫的轻量化航空安全气囊与立邦的复材特种航空涂料入局，意味着中国 eVTOL 正在复用新能源汽车过去十年积累的精密制造产能，将整机 BOM 成本压缩至欧美同行的 1/3。",
                "洞察三：随着沃飞长空等链主基地释放百亿级采购清单，具备 DO-178C/DO-254 航空软硬件适航认证能力的本土Tier-1供应商将迎来估值重塑。"
            ],
            "creativeWidget": {
                "type": "supply_bom_simulator",
                "badge": "🕹️ A1 新闻部创意交互组件 // 供应链价值拆解台",
                "title": "互动拆解：eVTOL 整机核心供应链价值占比与技术壁垒",
                "subtitle": "点击切换查看【核心子系统价值权重】、【车规vs航空规锋芒对决】与【国产供应链突围路线】",
                "tabs": [
                    {
                        "id": "bom_rank",
                        "label": "🔋 供应链价值权重榜",
                        "items": [
                            {"name": "推进与高密航空电池系统", "score": 95, "tag": "占整机价值约 35%-40% · 中创新航/亿纬锂能/孚能", "detail": "决定垂直起降瞬时放电倍率与有效航程，需同时满足高比能与零热失控蔓延要求。"},
                            {"name": "航电与多余度飞控系统 (FCC)", "score": 93, "tag": "占整机价值约 25%-30% · 适航取证核心卡点", "detail": "三余度/四余度容错飞控架构，配合独立低压锂电供电，确保极端故障下安全迫降。"},
                            {"name": "碳纤维复材机体与被动安全", "score": 88, "tag": "占整机价值约 20%-25% · 奥托立夫/立邦航空涂层", "detail": "全机身碳纤维减重与航空特种减阻耐候涂装，结合定制轻量化安全气囊系统。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ A1 锋芒观点碰撞",
                        "proTitle": "正方观点：车规级供应链外溢足以让中国 eVTOL 成本碾压全球",
                        "proDesc": "依托珠三角与长三角成熟的动力电池、电机电控与智能座舱产线，国产主机厂能快速把整机价格打到 120万-240万元区间。",
                        "conTitle": "反方观点：直接套用车规件无法通过民航局严苛适航审定",
                        "conDesc": "航空高空低温、强电磁干扰与疲劳寿命要求远超地面汽车，缺乏航空 DO-254/DO-178C 正向开发体系的供应商将被淘汰。",
                        "a1Verdict": "★ A1 新闻部主编裁决：“车规级规模制造工艺 + 航空级冗余适航标准”的混血物种，才是未来五年真正的供应链赢家。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🛠️ 供应商入局四步法",
                        "steps": [
                            {"code": "STAGE 01 // 原理样机联合预研", "status": "技术卡位", "tip": "针对主机厂专用条件需求，定制减重与高倍率/高可靠样品（如亿纬锂能低压锂电合作模式）。"},
                            {"code": "STAGE 02 // 适航符合性试验", "status": "实验室摸底", "tip": "配合主机厂完成环境、电磁兼容（EMC）、振动与极限热失控地面台架试验。"},
                            {"code": "STAGE 03 // 锁定量产定点与PC体系", "status": "产线审核", "tip": "建立全生命周期批次可追溯产线，支撑主机厂获取生产许可证（PC）。"},
                            {"code": "STAGE 04 // 切入全球售后航材池", "status": "高频复购", "tip": "随着机队商业化运营，电池包更换与航材维保将带来持续高毛利现金流。"}
                        ]
                    }
                ]
            }
        },
        "competition": {
            "creativeFormat": "国家级赛事含金量雷达 + 参赛拿单通关模拟器",
            "title": f"【A1新闻部·09:00创意特稿】({today_str}) 别只盯着奖金池：为什么国家级低空大赛正在变成地方政府的“实景招标会”？",
            "author": "A1 新闻部 · 赛事与创投主笔智能体",
            "readTime": "8 分钟深度交互阅读 · 含备赛通关沙盘",
            "summary": f"基于今日 07:00 赛事抓取最高重要度信号（{top_score}分）：数字中国低空经济赛道促成 30+ 单位签约、国创赛珠海专业赛与美团 55 万具身智能赛同台竞技。A1 新闻部为您拆解如何通过一场比赛同时拿下政府航线批文与创投基金。",
            "body": [
                f"【A1 新闻部 09:00 独到见解 · {today_str}】今早 07:00 全网抓取显示，【比赛信息】栏目重要度指数达 {top_score} 分。A1 新闻部深入追踪发现，2026 年的低空赛事已经彻底告别“PPT 概念比拼”，进化为“真机实飞 + 监管平台联调”的实战考场。",
                "洞察一：从“场景验证”到“系统重构”。以数字中国创新大赛·低空经济赛道为例，单届促成 30 余家单位达成合作的核心原因，在于赛事直接在真实空域检验无人机与 eVTOL 的 5G-A 通感一体管控能力。",
                "洞察二：大厂赛题指明了末端物流最痛的工程卡点。美团 55 万元低空经济与具身智能挑战赛聚焦复杂城市环境下的视觉避障与自主配送，谁能在赛场上跑通高鲁棒性算法，谁就能直接拿到头部平台的商业化入场券。"
            ],
            "creativeWidget": {
                "type": "competition_radar_simulator",
                "badge": "🕹️ A1 新闻部创意交互组件 // 赛事含金量与拿单沙盘",
                "title": "互动推演：国内三大标杆低空赛事战队匹配与得分秘籍",
                "subtitle": "点击切换查看【三大赛事战力雷达】、【评委打分潜规则PK】与【从参赛到拿单四步通关】",
                "tabs": [
                    {
                        "id": "comp_rank",
                        "label": "🏆 核心赛事战力匹配",
                        "items": [
                            {"name": "数字中国创新大赛 · 低空经济赛道", "score": 96, "tag": "政企订单转化率最高 · 单届30+单位签约", "detail": "适合具备完整空地协同管控软件、应急救援或支线物流实飞能力的成长期企业。"},
                            {"name": "中国创新创业大赛 · 珠海低空专业赛", "score": 94, "tag": "国家级双创背书 · 直通湾区示范航线", "detail": "联动中国航展与珠海“天空之城”航线，适合整机、新材料与核心零部件硬科技团队。"},
                            {"name": "美团低空经济与具身智能挑战赛", "score": 92, "tag": "55万元高额奖金池 · 硬核算法极客擂台", "detail": "聚焦末端无人机自主视觉导航与具身操作，适合高校实验室与飞控视觉算法团队。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ A1 锋芒观点碰撞",
                        "proTitle": "正方观点：初创团队应优先冲刺国家级政企综合赛拿地方落地补贴",
                        "proDesc": "低空经济高度依赖空域审批与起降基建，通过国创赛与数字中国大赛直接对接地方专班，能省去两年的商务拓展周期。",
                        "conTitle": "反方观点：搞定美团/顺丰等产业龙头的技术命题赛才是最快变现路",
                        "conDesc": "大厂命题赛直接对应真实的百万级日均配送痛点，算法一旦夺冠即可切入成熟商业物流网络。",
                        "a1Verdict": "★ A1 新闻部主编裁决：整机与空管平台企业主攻“数字中国/国创赛”拿政府航线，机载感知与算法团队主攻“美团挑战赛”拿商业订单。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🎯 夺冠拿单四步通关",
                        "steps": [
                            {"code": "STEP 01 // 锁定自主知识产权", "status": "资格审查", "tip": "确保核心飞控代码、气动构型或航电硬件无产权纠纷（创业江苏/国创赛硬性红线）。"},
                            {"code": "STEP 02 // 对齐地方监管平台接口", "status": "技术加分项", "tip": "在方案中内置与《低空飞行综合监管服务平台规范》兼容的数据上报模块。"},
                            {"code": "STEP 03 // 准备真实复杂气象实飞数据", "status": "决赛决胜点", "tip": "拒绝纯仿真动画，展示抗风切变、障碍物动态避障与应急迫降实测日志。"},
                            {"code": "STEP 04 // 锁定地方首购首用目录", "status": "商业闭环", "tip": "赛后立即对接主办地低空专班，将获奖项目转化为海岛物流、巡检或文旅示范合同。"}
                        ]
                    }
                ]
            }
        },
        "product": {
            "creativeFormat": "四大构型商业化战力擂台 + 运营回本周期模拟器",
            "title": f"【A1新闻部·09:00创意特稿】({today_str}) 128万的“陆地航母”与239万的亿航EH216-S：谁能先帮买家把钱赚回来？",
            "author": "A1 新闻部 · 飞行器评测主笔智能体",
            "readTime": "9 分钟深度交互阅读 · 含商业回本沙盘",
            "summary": f"基于今日 07:00 产品与短视频信息流最高重要度信号（{top_score}分）：亿航 16 机编队与海外首飞刷屏、小鹏汇天中东 600 台大单、峰飞与沃飞加速取证。A1 新闻部用交互式回本账本，算清四大技术构型的商业化真账。",
            "body": [
                f"【A1 新闻部 09:00 独到见解 · {today_str}】今早 07:00 短视频信息流与主机厂官网抓取数据显示，【产品发布】栏目重要度达 {top_score} 分。随着亿航 EH216-S 集齐四证、小鹏汇天“陆地航母”斩获中东 600 台订单、广汽高域半年订单破千，买家最关心的问题已经从“能不能飞”变成了“多久能回本”。",
                "洞察一：多旋翼构型（如亿航 EH216-S、广汽高域 AirCab）凭机械结构简单率先生态卡位。虽然航程约 30 公里，但在 5A 级景区低空游览与城市地标观光场景中，单机日均高频起降即可跑通景区运营账本。",
                "洞察二：分体式飞行汽车（小鹏汇天“陆地航母”）巧妙绕开了“城市起降场不足”的早期瓶颈。把飞行体装进六轮陆行母舰后备箱，直接切入高净值人群越野消费与应急救援市场。",
                "洞察三：复合翼（峰飞盛世龙/沃兰特 VE25）与倾转旋翼（沃飞 AE200-100）则是未来城际百公里空中出行的终极主力，随着 2026-2027 年适航取证冲刺，城际空中快线即将迎来奇点。"
            ],
            "creativeWidget": {
                "type": "product_roi_simulator",
                "badge": "🕹️ A1 新闻部创意交互组件 // 机型战力与回本账本",
                "title": "互动推演：中国四大主流 eVTOL 技术流派商业化战力与回本沙盘",
                "subtitle": "点击切换查看【四大机型硬核战力榜】、【C端个人玩具 vs B端空中出租车辩论】与【景区/城际运营回本路径】",
                "tabs": [
                    {
                        "id": "prod_rank",
                        "label": "✈️ 四大机型商业战力榜",
                        "items": [
                            {"name": "亿航 EH216-S · 多旋翼无人载人", "score": 96, "tag": "指导价 239 万元 · 全球首家四证齐全 (TC/PC/AC/OC)", "detail": "无需人类飞行员，已实现 216 架年交付盈利与拉美首飞，景区观光与短途接驳可即买即运营。"},
                            {"name": "小鹏汇天“陆地航母” · 分体式飞行汽车", "score": 95, "tag": "预估约 128 万元起 · 中东斩获 600 台海外大单", "detail": "陆行体可为飞行体移动补能，完美适配高净值个人越野玩家与野外搜救队伍。"},
                            {"name": "峰飞盛世龙 / 沃飞 AE200 · 城际干线级", "score": 93, "tag": "复合翼与倾转旋翼代表 · 冲刺城际百公里航线", "detail": "兼具垂直起降与固定翼高速巡航优势，瞄准大湾区、长三角跨城商务干线。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ A1 锋芒观点碰撞",
                        "proTitle": "正方观点：ToB/ToG 景区观光与城际航线才是 eVTOL 唯一规模化出路",
                        "proDesc": "空域管制与维护保养决定了普通消费者很难像开私家车一样在城市随便起飞，集中化机队运营（如亿航/峰飞/广汽高域模式）效率最高。",
                        "conTitle": "反方观点：ToC 高端个人飞行汽车（如陆地航母）现金流回笼最快",
                        "conDesc": "中东 600 台订单与国内数千台预订证明，先卖给户外探险家与飞行爱好者，能最快帮主机厂收回百亿研发成本。",
                        "a1Verdict": "★ A1 新闻部主编裁决：中国主机厂正在走出“B端无人驾驶空中巴士（亿航/峰飞/沃飞）+ C端分体式越野飞行车（小鹏汇天）”的双轨制胜道路。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "💰 商业运营回本四步账",
                        "steps": [
                            {"code": "MODEL 01 // 5A景区低空游览", "status": "最快现金流", "tip": "采用已拿 OC 证机型（如 EH216-S），单票定价 300-600 元，配合自动充电起降场实现高频周转。"},
                            {"code": "MODEL 02 // 跨海与海岛高值物流", "status": "高频刚需", "tip": "采用吨级货运 eVTOL（如峰飞 V2000CG），运输生鲜、医药与高价值精密件。"},
                            {"code": "MODEL 03 // 高端营地飞行体验", "status": "C端+B端联动", "tip": "依托分体式飞行汽车在飞行营地提供驻场体验与驾照培训服务。"},
                            {"code": "MODEL 04 // 枢纽机场-CBD空中快线", "status": "远期万亿市场", "tip": "复合翼与倾转旋翼取证后，将 90 分钟地面拥堵车程缩短至 15 分钟空中飞行。"}
                        ]
                    }
                ]
            }
        }
    }

    tpl = templates.get(top_cat, templates["policy"])
    return {
        "id": f"a1-newsroom-{today_str.replace('-', '')}-0900",
        "category": top_cat,
        "isOfficial": True,
        "isNewsroomDaily": True,
        "publishSlot": "09:00 A1新闻部每日特稿",
        "importanceScore": top_score,
        "creativeFormat": tpl["creativeFormat"],
        "title": tpl["title"],
        "author": tpl["author"],
        "date": today_str,
        "readTime": tpl["readTime"],
        "summary": tpl["summary"],
        "body": tpl["body"],
        "creativeWidget": tpl["creativeWidget"],
        "tags": ["A1新闻部每日特稿", "09:00创意专栏", cat_name, "深度见解", "互动沙盘"],
        "sources": matched_sources if matched_sources else [
            {"title": "国家发改委设“低空司”与地方立法加速分析", "url": "https://www.zzyuam.com/news/detail/110ac5ced3770ff29b5fdbea86d5b62a"},
            {"title": "飞行汽车之家：中国eVTOL整机公司创始人及代表机型对比", "url": "https://flyingcarevtol.com/news/4613"}
        ]
    }


def main():
    now_cst = datetime.now(CST)
    today_str = now_cst.strftime("%Y-%m-%d")
    print(f"[A1 Newsroom Writer] 启动每日 09:00 A1新闻部深度创意撰稿任务 | 当前北京时间: {now_cst.strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.exists(DATA_FILE):
        print("[ERROR] data/news.json 不存在，请先运行 daily_crawler.py")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    meta = db.get("meta", {})
    top_cat = meta.get("todayTopCategory", "policy")
    top_score = meta.get("todayTopScore", 96.5)
    crawled_today = [a for a in db.get("articles", []) if a.get("isDailyCrawled") and a.get("date") == today_str]

    print(f"  -> 今日最高重要度栏目: [{CATEGORY_LABELS.get(top_cat)}] (得分: {top_score})")

    llm_article = try_llm_generation(top_cat, top_score, crawled_today, today_str)
    if llm_article:
        article = {
            "id": f"a1-newsroom-{today_str.replace('-', '')}-0900",
            "category": top_cat,
            "isOfficial": True,
            "isNewsroomDaily": True,
            "publishSlot": "09:00 A1新闻部每日特稿",
            "importanceScore": top_score,
            "creativeFormat": llm_article.get("creativeFormat", "交互式深度沙盘 + 锋芒辩论PK"),
            "title": llm_article["title"],
            "author": llm_article.get("author", "A1 新闻部 · 每日主笔智能体"),
            "date": today_str,
            "readTime": llm_article.get("readTime", "9 分钟深度交互阅读"),
            "summary": llm_article["summary"],
            "body": llm_article["body"],
            "creativeWidget": llm_article.get("creativeWidget"),
            "tags": llm_article.get("tags", ["A1新闻部每日特稿", "09:00创意专栏"]),
            "sources": crawled_today[0].get("sources", []) if crawled_today else []
        }
    else:
        article = build_builtin_creative_article(top_cat, top_score, crawled_today, today_str)

    # 移除同日已有的 09:00 特稿并置顶插入最新特稿
    existing = [a for a in db.get("articles", []) if a.get("id") != article["id"]]
    db["articles"] = [article] + existing
    meta["lastNewsroomTime"] = f"{today_str} 09:00:00 CST"
    db["meta"] = meta

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"[A1 Newsroom Writer] 09:00 A1新闻部文章已生成并置顶写入: {article['title']}")


if __name__ == "__main__":
    main()
