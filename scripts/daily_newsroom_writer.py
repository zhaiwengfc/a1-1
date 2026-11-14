#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A1 低空信息站 · A1 新闻部每日专栏生成脚本
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


def try_llm_generation(top_cat: str, crawled_context: list, today_str: str):
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return None

    cat_name = CATEGORY_LABELS.get(top_cat, "政策法规")
    context_text = "\n".join([f"- [{a.get('category')}] {a.get('title')}: {a.get('summary')}" for a in crawled_context])

    prompt = f"""你是 A1 网站的官方“A1 新闻部”主笔。今天是 {today_str}。
今日重点聚焦栏目为【{cat_name}】。
今日行业背景信息如下：
{context_text}

请撰写一篇“A1 新闻部”深度专栏文章，要求：
1. 具备产业深度与独到见解，直击商业化本质与产业趋势；严禁在文章标题、署名或正文中出现“AI”、“智能体”、“07:00抓取”、“09:00撰稿”、“重要度评分”等任何后台技术词汇；
2. 同时设计一个结构化的互动专题看板组件 `creativeWidget`（包含3个可切换Tab：核心指标对比 / 行业观点探讨 / 实操步骤指南）。
3. 严格输出合法的 JSON 对象，包含字段：title, author (固定写为“A1 新闻部”), readTime, creativeFormat, summary, body (4段深度正文的字符串数组), tags (字符串数组，请勿在tags里重复包含“A1新闻部”), creativeWidget (包含 badge, title, subtitle, tabs 数组)。"""

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
    except Exception:
        pass
    return None


def build_builtin_creative_article(top_cat: str, crawled_context: list, today_str: str) -> dict:
    cat_name = CATEGORY_LABELS.get(top_cat, "政策法规")

    matched_sources = []
    for item in crawled_context:
        if item.get("category") == top_cat and item.get("sources"):
            matched_sources = item["sources"]
            break

    templates = {
        "policy": {
            "creativeFormat": "空域改革三维对比 + 观点交锋 + 适航路线图",
            "title": "当城市开始竞逐“天空立交桥”：从中央低空司到地方特区立法的三场深水区博弈",
            "author": "A1 新闻部",
            "readTime": "9 分钟深度阅读",
            "summary": "随着国家发改委低空经济发展司统筹推进、中国民航局 CCAR-92 部落地以及深圳、广州、合肥、成都等地方专项政策进入全面实施期，低空经济正从顶层规划加速迈向空域协同管理与商业订单转化的关键阶段。",
            "body": [
                "如果说 2024 年是低空经济写入政府工作报告的“概念元年”，那么当下从中央部委到地方政府密集出台的实施细则，正在把这场产业竞赛推向真金白银的“空域运营权与链主生态建设”。当前决定一家 eVTOL 或工业无人机企业商业化成败的核心，已不仅是纸面航程参数，而是能否打通“军地民空域协同监管接口”与“地方示范航线商业闭环”。",
                "一、从“发改委设司”到“民航局立规”，数字化监管底座加速成型：国家发改委设立“低空经济发展司”统筹跨部门基建投资与产业规划，而中国民航局（CAAC）通过《民用无人驾驶航空器运行安全管理规则》（CCAR-92）及《低空飞行综合监管服务平台规范》，将适航取证（TC/PC/AC）与运营合格证（OC）全面纳入数字化监管体系。",
                "二、地方产业政策的进阶考卷——从“给补贴”走向“给空域、给场景”：从《深圳经济特区低空经济产业促进条例》及 20 条扶持措施，到广州开发区护航小鹏汇天“陆地航母”量产基地建设，再到成都沃飞长空全球总部基地与珠海“天空之城”示范航线联动，各大先锋城市的发力重心已转向开放跨区真实商业航线与起降基础设施配套。",
                "三、公众安全信任度推动标准升级：围绕城市复杂空域下的飞行安全、起降场噪音控制、第三者责任保险以及高可靠低压飞控供电冗余，行业技术标准与城市低空管理规范正迎来快速完善期。"
            ],
            "creativeWidget": {
                "type": "policy_arena_simulator",
                "badge": "A1 深度专题互动看板",
                "title": "2026-2030 低空经济政策落地与适航路径全景透视",
                "subtitle": "切换下方标签，对比先锋城市政策布局、行业核心观点交锋与企业四证合规节点",
                "tabs": [
                    {
                        "id": "city_rank",
                        "label": "🏙️ 先锋城市政策布局",
                        "items": [
                            {"name": "深圳 · 特区立法领跑型", "score": 96, "tag": "全国首部特区低空条例 + 20条专项扶持措施", "detail": "对取得 CAAC 型号合格证(TC)与生产许可证(PC)的载人 eVTOL 企业给予产业化激励，开放高密度城市末端物流与跨海示范航线。"},
                            {"name": "广州 · 智造链主集群型", "score": 94, "tag": "亿航四证闭环 + 小鹏汇天量产工厂 + 广汽高域", "detail": "集聚全球首张 OC 证企业亿航智能与小鹏汇天广州智造基地，依托成熟汽车产业链打通“研发—总装—出海”全链条。"},
                            {"name": "成都/珠海 · 航展与研发双驱型", "score": 91, "tag": "沃飞长空全球总部 + 国创赛珠海专业赛", "detail": "成都以沃飞 AE200 链主基地带动百亿航空配套，珠海依托中国航展与创新创业大赛构建湾区跨海物流网络。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ 商业化路径探讨",
                        "proTitle": "路径一：优先发力支线物流与郊区特定场景，稳步推进城市载人",
                        "proDesc": "以峰飞 V2000CG 与美团无人机末端配送为代表，货运场景容错率更高、适航取证周期更可控，能先在海岛物流、医疗急救中跑通正向现金流。",
                        "conTitle": "路径二：载人 eVTOL 景区游览与城际接驳具备更高单机产值",
                        "conDesc": "以亿航 EH216-S 四证齐全与小鹏汇天中东 600 台订单为代表，高附加值文旅观光与个人飞行器能够更快分摊早期航空级电池与飞控研发投入。",
                        "a1Verdict": "★ A1 新闻部观察：2026-2027 年最具可行性的商业模式是“以高频低空物流和5A景区观光提升起降场利用率，以倾转旋翼和复合翼机型打开远期城际客运空间”。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🛡️ 企业适航四证指南",
                        "steps": [
                            {"code": "第一阶段 · TC 型号合格证", "status": "设计批准", "tip": "核心重点：专用条件审定、FCC飞控多余度容错与动力电池热失控防护验证（CCAR-21）。"},
                            {"code": "第二阶段 · PC 生产许可证", "status": "量产准入", "tip": "核心重点：供应链质量追溯体系（如中创新航/亿纬锂能电芯批次一致性与复合材料无损检测）。"},
                            {"code": "第三阶段 · AC 单机适航证", "status": "交付通行", "tip": "核心重点：每架下线航空器出厂试飞与标准构型一致性核查。"},
                            {"code": "第四阶段 · OC 运营合格证", "status": "商业运营", "tip": "核心重点：接入民航局低空飞行综合监管服务平台，建立完善空地协同运行手册（CCAR-92）。"}
                        ]
                    }
                ]
            }
        },
        "supply": {
            "creativeFormat": "核心子系统价值占比 + 适航供应链路径",
            "title": "拆解一架百万级飞行汽车：为什么动力电池与飞控系统决定了商业化上限？",
            "author": "A1 新闻部",
            "readTime": "8 分钟深度阅读",
            "summary": "随着中创新航、亿纬锂能、奥托立夫与立邦密集切入低空赛道，eVTOL 核心供应链正从样品试制走向规模化定点。本文为您解析车规级制造与航空级适航标准的融合路径。",
            "body": [
                "当市场目光聚焦于整机首飞时，低空经济真正的产业壁垒正在电芯实验室与多余度飞控代码里加速构建。",
                "一、“高能量密度主电池 + 独立低压飞控电池”成为主流架构：小鹏汇天“陆地航母”选择中创新航提供高压主动力、亿纬锂能提供低压锂电池护航 FCC 飞控与 ESC 电调，通过双轨物理隔离有效防范单点供电失效风险。",
                "二、汽车供应链龙头加速跨界赋能：奥托立夫的轻量化航空安全气囊与立邦的复合材料特种航空涂料入局，推动国产 eVTOL 充分吸收成熟新能源汽车产业链的精密制造优势。",
                "三、随着沃飞长空等链主基地释放百亿级采购需求，具备 DO-178C/DO-254 航空软硬件适航认证能力的本土核心供应商将迎来广阔市场空间。"
            ],
            "creativeWidget": {
                "type": "supply_bom_simulator",
                "badge": "A1 深度专题互动看板",
                "title": "eVTOL 整机核心供应链价值占比与技术壁垒解析",
                "subtitle": "切换下方标签，查看核心子系统价值权重、车规与航空标准对比及供应商准入流程",
                "tabs": [
                    {
                        "id": "bom_rank",
                        "label": "🔋 核心子系统价值权重",
                        "items": [
                            {"name": "推进与高密航空电池系统", "score": 95, "tag": "占整机价值约 35%-40% · 中创新航/亿纬锂能/孚能", "detail": "决定垂直起降瞬时放电倍率与有效航程，需同时满足高比能与零热失控蔓延要求。"},
                            {"name": "航电与多余度飞控系统 (FCC)", "score": 93, "tag": "占整机价值约 25%-30% · 适航取证关键系统", "detail": "三余度/四余度容错飞控架构，配合独立低压锂电供电，确保极端故障下安全迫降。"},
                            {"name": "碳纤维复材机体与被动安全", "score": 88, "tag": "占整机价值约 20%-25% · 奥托立夫/立邦航空涂层", "detail": "全机身碳纤维减重与航空特种减阻耐候涂装，结合定制轻量化安全气囊系统。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ 车规与航空规融合探讨",
                        "proTitle": "优势面：成熟新能源汽车供应链大幅降低 eVTOL 制造成本",
                        "proDesc": "依托珠三角与长三角成熟的动力电池、电机电控与智能座舱产线，国产主机厂能够有效控制整机 BOM 成本。",
                        "conTitle": "挑战面：航空级高可靠与适航追溯标准远高于地面车辆",
                        "conDesc": "高空低温、强电磁干扰与结构疲劳寿命要求严苛，上游供应商必须建立符合航空 DO-254/DO-178C 的正向开发体系。",
                        "a1Verdict": "★ A1 新闻部观察：“车规级规模制造工艺 + 航空级冗余适航标准”的融合型供应商，将成为未来五年低空供应链的核心赢家。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🛠️ 供应商配套四步路径",
                        "steps": [
                            {"code": "第一阶段 · 原理样机联合预研", "status": "技术定点", "tip": "针对主机厂专用条件需求，定制减重与高倍率样品（如亿纬锂能低压锂电合作模式）。"},
                            {"code": "第二阶段 · 适航符合性试验", "status": "地面台架", "tip": "配合主机厂完成环境、电磁兼容（EMC）、振动与极限热失控地面试验。"},
                            {"code": "第三阶段 · 批量定点与PC体系", "status": "产线审核", "tip": "建立全生命周期批次可追溯产线，支撑主机厂获取生产许可证（PC）。"},
                            {"code": "第四阶段 · 售后航材与维保池", "status": "长期服务", "tip": "随着机队投入商业运营，电池包更换与航材维保将形成持续服务市场。"}
                        ]
                    }
                ]
            }
        },
        "competition": {
            "creativeFormat": "赛事特色对比 + 参赛备赛要点",
            "title": "从技术路演到场景签约：国家级低空经济大赛如何成为产业落地的“直通车”？",
            "author": "A1 新闻部",
            "readTime": "8 分钟深度阅读",
            "summary": "数字中国低空经济赛道促成 30+ 单位签约、国创赛珠海专业赛与美团 55 万具身智能赛同台竞技，专业赛事正成为连接创新团队、地方示范航线与产业基金的关键纽带。",
            "body": [
                "当前的低空经济专业赛事已不再停留于概念展示，而是全面转向“真机实飞 + 监管平台联调”的实战检验。",
                "一、从“场景验证”到“系统重构”：以数字中国创新大赛·低空经济赛道为例，单届促成 30 余家单位达成合作的核心原因，在于赛事直接在真实空域检验无人机与 eVTOL 的数字化协同管控能力。",
                "二、龙头命题赛直指末端工程痛点：美团 55 万元低空经济与具身智能挑战赛聚焦复杂城市环境下的视觉避障与自主配送，为高校实验室与算法团队提供了贴近真实商业场景的竞技舞台。"
            ],
            "creativeWidget": {
                "type": "competition_radar_simulator",
                "badge": "A1 深度专题互动看板",
                "title": "国内三大标杆低空赛事定位与备赛指南",
                "subtitle": "切换下方标签，对比三大重点赛事特色、参赛方向选择与项目落地流程",
                "tabs": [
                    {
                        "id": "comp_rank",
                        "label": "🏆 三大重点赛事对比",
                        "items": [
                            {"name": "数字中国创新大赛 · 低空经济赛道", "score": 96, "tag": "政企合作转化率高 · 单届30+单位签约", "detail": "适合具备完整空地协同管控软件、应急救援或支线物流实飞能力的成长期企业。"},
                            {"name": "中国创新创业大赛 · 珠海低空专业赛", "score": 94, "tag": "国家级双创平台 · 联动湾区示范航线", "detail": "联动中国航展与珠海“天空之城”航线，适合整机、新材料与核心零部件硬科技团队。"},
                            {"name": "美团低空经济与具身智能挑战赛", "score": 92, "tag": "55万元奖金池 · 聚焦复杂城市视觉导航", "detail": "聚焦末端无人机自主视觉导航与具身操作，适合高校实验室与飞控视觉算法团队。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ 参赛赛道选择建议",
                        "proTitle": "方向一：整机与空管平台团队优先参加政企综合赛事",
                        "proDesc": "低空经济高度依赖空域协同与起降基建，通过国创赛与数字中国大赛可直接对接地方专班与示范园区。",
                        "conTitle": "方向二：机载感知与算法团队优先角逐产业龙头命题赛",
                        "conDesc": "企业命题赛直接对应真实的末端配送与视觉避障工程痛点，优秀算法团队更容易获得商业技术合作机会。",
                        "a1Verdict": "★ A1 新闻部观察：整机与空管系统企业建议主攻“数字中国/国创赛”对接示范航线，机载视觉与飞控算法团队建议主攻“美团挑战赛”验证工程鲁棒性。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "🎯 备赛与转化四步法",
                        "steps": [
                            {"code": "第一步 · 完善核心自主知识产权", "status": "资格审查", "tip": "确保核心飞控代码、气动构型或航电硬件具备清晰自主知识产权（各大国创赛硬性要求）。"},
                            {"code": "第二步 · 对齐地方监管平台接口", "status": "技术加分", "tip": "在方案中展示与《低空飞行综合监管服务平台规范》兼容的数据上报能力。"},
                            {"code": "第三步 · 准备真实环境实飞数据", "status": "路演核心", "tip": "提供抗风切变、动态障碍物避障与应急迫降的真实飞行测试记录。"},
                            {"code": "第四步 · 对接地方首购首用场景", "status": "产业落地", "tip": "赛后积极对接主办地低空产业专班，推动获奖方案纳入地方海岛物流、巡检或文旅示范项目。"}
                        ]
                    }
                ]
            }
        },
        "product": {
            "creativeFormat": "四大构型对比看板 + 商业运营模式分析",
            "title": "128万的“陆地航母”与239万的亿航EH216-S：四大技术构型如何算清商业化运营账？",
            "author": "A1 新闻部",
            "readTime": "9 分钟深度阅读",
            "summary": "随着亿航 EH216-S 集齐四证、小鹏汇天“陆地航母”斩获中东 600 台大单、峰飞与沃飞加速适航取证，国产 eVTOL 的核心议题已从技术验证转向商业场景闭环。",
            "body": [
                "随着国产主流 eVTOL 机型相继迈入适航取证后期与批量交付阶段，不同气动构型在商业应用场景上的分工日益清晰。",
                "一、多旋翼构型（如亿航 EH216-S、广汽高域 AirCab）凭结构简洁率先商业化卡位：在 5A 级景区低空游览与城市地标观光场景中，具备高频起降与标准化无人驾驶运营优势。",
                "二、分体式飞行汽车（小鹏汇天“陆地航母”）拓展个人与特种应用：通过六轮陆行母舰实现移动补能与仓储运输，切入户外探索与应急救援市场。",
                "三、复合翼（峰飞盛世龙/沃兰特 VE25）与倾转旋翼（沃飞 AE200-100）瞄准城际干线：兼具垂直起降与固定翼高速巡航能力，致力于重构都市圈城际空中出行网络。"
            ],
            "creativeWidget": {
                "type": "product_roi_simulator",
                "badge": "A1 深度专题互动看板",
                "title": "中国四大主流 eVTOL 技术流派与商业化场景对比",
                "subtitle": "切换下方标签，查看核心机型综合指标、B端与C端路线对比及典型运营场景",
                "tabs": [
                    {
                        "id": "prod_rank",
                        "label": "✈️ 四大机型核心指标",
                        "items": [
                            {"name": "亿航 EH216-S · 多旋翼无人载人", "score": 96, "tag": "指导价 239 万元 · 全球首家四证齐全 (TC/PC/AC/OC)", "detail": "无需人类飞行员，已实现 216 架年交付盈利与拉美首飞，景区观光与短途接驳可快速投入运营。"},
                            {"name": "小鹏汇天“陆地航母” · 分体式飞行汽车", "score": 95, "tag": "预估约 128 万元起 · 中东斩获 600 台海外订单", "detail": "陆行体可为飞行体移动补能，适配个人越野探索与野外应急搜救场景。"},
                            {"name": "峰飞盛世龙 / 沃飞 AE200 · 城际干线级", "score": 93, "tag": "复合翼与倾转旋翼代表 · 面向城际百公里航线", "detail": "兼具垂直起降与固定翼高速巡航优势，瞄准大湾区、长三角跨城商务出行。"}
                        ]
                    },
                    {
                        "id": "debate_pk",
                        "label": "⚡ B端与C端市场探讨",
                        "proTitle": "观点一：ToB/ToG 景区观光与城际航线是规模化运营主力",
                        "proDesc": "空域管理与维护保养要求较高，集中化机队运营（如亿航、峰飞、广汽高域模式）更容易建立标准化安全管理体系。",
                        "conTitle": "观点二：ToC 高端个人飞行汽车（如陆地航母）商业变现更快",
                        "conDesc": "中东 600 台订单与国内预订数据表明，面向飞行营地与户外玩家的个人飞行汽车能够快速形成销售规模。",
                        "a1Verdict": "★ A1 新闻部观察：中国主机厂正在形成“B端无人驾驶空中巴士（亿航/峰飞/沃飞）+ C端分体式越野飞行车（小鹏汇天）”的双轨并行格局。"
                    },
                    {
                        "id": "compliance_calc",
                        "label": "💰 四大商业应用场景",
                        "steps": [
                            {"code": "场景 01 · 5A景区低空游览", "status": "已商业化", "tip": "采用已获 OC 证机型（如 EH216-S），配合标准化起降场实现高频观光飞行。"},
                            {"code": "场景 02 · 跨海与海岛高值物流", "status": "高频刚需", "tip": "采用吨级货运 eVTOL（如峰飞 V2000CG），运输生鲜、医疗物资与高价值精密件。"},
                            {"code": "场景 03 · 飞行营地驻场体验", "status": "C端+B端联动", "tip": "依托分体式飞行汽车在航空营地提供飞行体验与培训服务。"},
                            {"code": "场景 04 · 枢纽机场-CBD空中快线", "status": "远期主力", "tip": "复合翼与倾转旋翼取证后，将地面拥堵车程大幅缩短为跨城空中直达。"}
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
        "publishSlot": "A1新闻部",
        "creativeFormat": tpl["creativeFormat"],
        "title": tpl["title"],
        "author": tpl["author"],
        "date": today_str,
        "readTime": tpl["readTime"],
        "summary": tpl["summary"],
        "body": tpl["body"],
        "creativeWidget": tpl["creativeWidget"],
        "tags": ["A1新闻部", cat_name, "深度专栏"],
        "sources": matched_sources if matched_sources else [
            {"title": "国家发改委设“低空司”与地方立法加速分析", "url": "https://www.zzyuam.com/news/detail/110ac5ced3770ff29b5fdbea86d5b62a"},
            {"title": "飞行汽车之家：中国eVTOL整机公司创始人及代表机型对比", "url": "https://flyingcarevtol.com/news/4613"}
        ]
    }


def main():
    now_cst = datetime.now(CST)
    today_str = now_cst.strftime("%Y-%m-%d")

    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    meta = db.get("meta", {})
    top_cat = meta.get("todayTopCategory", "policy")
    crawled_today = [a for a in db.get("articles", []) if a.get("isDailyCrawled") and a.get("date") == today_str]

    llm_article = try_llm_generation(top_cat, crawled_today, today_str)
    if llm_article:
        article = {
            "id": f"a1-newsroom-{today_str.replace('-', '')}-0900",
            "category": top_cat,
            "isOfficial": True,
            "isNewsroomDaily": True,
            "publishSlot": "A1新闻部",
            "creativeFormat": llm_article.get("creativeFormat", "深度专题互动看板"),
            "title": llm_article["title"],
            "author": "A1 新闻部",
            "date": today_str,
            "readTime": llm_article.get("readTime", "9 分钟深度阅读"),
            "summary": llm_article["summary"],
            "body": llm_article["body"],
            "creativeWidget": llm_article.get("creativeWidget"),
            "tags": llm_article.get("tags", ["A1新闻部", "深度专栏"]),
            "sources": crawled_today[0].get("sources", []) if crawled_today else []
        }
    else:
        article = build_builtin_creative_article(top_cat, crawled_today, today_str)

    existing = [a for a in db.get("articles", []) if a.get("id") != article["id"]]
    db["articles"] = [article] + existing
    meta["lastUpdatedDate"] = today_str
    db["meta"] = meta

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
