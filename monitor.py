import requests
import feedparser
import json
import os
import re
import time
from datetime import datetime

# ==================== 🛠️ 唯一修改处 ====================
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"

# 硅基流动账户已成功充值，全面复活 DeepSeek-V3 顶级算力！
AI_API_KEY = "sk-cwrrsvquwdsiqtfjbgsgqqmdjyblnxyiunpqrpvvssgpakzx" 
AI_API_URL = "https://api.siliconflow.cn/v1/chat/completions" 
AI_MODEL = "deepseek-ai/DeepSeek-V3" 
# ========================================================

SITE_LIST = [
    # ==================== 一、央行 + 金融监管（全面放行） ====================
    {"name": "中国人民银行-公告", "url": "https://rsshub.app/sina/gov/pbc"},
    {"name": "证监会官网-动态", "url": "https://rsshub.app/sina/gov/csrc"},
    {"name": "金融监管总局", "url": "https://rsshub.app/gov/nfra/news"},
    {"name": "央行公开市场操作", "url": "https://rsshub.app/gov/pbc/goutongjiaoliu"},
    {"name": "美联储资讯(Fed)", "url": "https://www.federalreserve.gov/feeds/press_all.xml"},

    # ==================== 二、宏观财经大盘 ====================
    {"name": "华尔街见闻-实时快讯", "url": "https://feedx.net/rss/wallstreetcn.xml"},
    {"name": "财新网-金融要闻", "url": "https://feedx.net/rss/caixin.xml"},
    {"name": "第一财经-股市", "url": "https://feedx.net/rss/yicai.xml"},
    {"name": "雪球-最新热帖", "url": "https://rsshub.app/xueqiu/hots"}, 
    {"name": "国家统计局-数据", "url": "https://rsshub.app/sina/gov/stats"},
    {"name": "中证网-证券基金", "url": "https://feedx.net/rss/cs.xml"},
    {"name": "路透国际财经", "url": "https://feedx.net/rss/reuters.xml"},

    # ==================== 三、创投 + 融资 + 黑马企业 ====================
    {"name": "36氪-全量快讯", "url": "https://rsshub.app/36kr/news/latest"}, 
    {"name": "钛媒体-创投动态", "url": "https://feedx.net/rss/tmtpost.xml"},
    {"name": "猎云网创投", "url": "https://feedx.net/rss/lieyunwang.xml"},
    {"name": "创业邦-最新", "url": "https://rsshub.app/cyzone/news"},
    {"name": "投资界(清科)", "url": "https://rsshub.app/zero2ipo/news"},
    {"name": "黑马创业资讯", "url": "https://rsshub.app/heimaying/news"},

    # ==================== 四、硬科技 + 前沿新技术 ====================
    {"name": "科创板日报-快讯", "url": "https://rsshub.app/cls/kechuangban"},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml"},
    {"name": "极客公园-最新", "url": "https://rsshub.app/geekpark/news"},
    {"name": "高工机器人", "url": "https://rsshub.app/gg-robot/news"},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rsshub.app/sina/gov/cnsa"},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/"},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/"},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/"},

    # ==================== 七、全球顶级 VC 与创投风向标 ====================
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/"},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/"},

    # ==================== 八、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rsshub.app/sina/gov/miit"},
    {"name": "36氪-未来汽车日报", "url": "https://rsshub.app/36kr.info/automotive"},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml"},

    # ==================== 九、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/"},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml"},

    # ==================== 🎯 十、垂直补充：顶级早期黑马与创新科技发源地 ====================
    {"name": "TechFlow-深潮深度", "url": "https://rsshub.app/techflowpost/depth"},
    {"name": "arXiv-人工智能最新论文", "url": "https://rsshub.app/arxiv/query/search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending"},
    {"name": "GitHub-全球每日趋势榜", "url": "https://rsshub.app/github/trending/daily/any"},
    {"name": "ProductHunt-硅谷每日新品", "url": "https://rsshub.app/producthunt/today"},
    {"name": "IT桔子-一手投融资快讯", "url": "https://rsshub.app/itjuzi/merge"}
]

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('\n', ' ')
    return re.sub(r'\s+', ' ', clean_text).strip()

def get_ai_summary(title, content):
    """ 调用 DeepSeek-V3 帮你在后台疯狂洗沙，执行硬核黑马筛选 """
    if "你的" in AI_API_KEY or not AI_API_KEY or AI_API_KEY.strip() == "":
        return None

    safe_content = clean_html(content)[:600]

    # 🔥 核心大脑重构：升级为具有高度主观见解的黑马猎手提示词
    prompt = f"""
    你是一名冷峻、拥有敏锐行业洞察力的前沿硬科技产业与创投孵化顶级专家。
    请评估以下新闻，帮我筛选出具有“早期黑马潜力”或“颠覆性创新科技”的情报。

    新闻标题：{title}
    新闻摘要：{safe_content}

    【早期黑马/创新科技 识别标准】：
    1. 【早期黑马】：新成立或首次露面的团队背景、首发的新颖商业模式、Pre-A到A轮的硬科技企业获得数千万以上真金白银融资。
    2. 【创新科技】：具身智能/AI Agent/半导体芯片/商业航天/量子计算等领域的底层技术突破、重大核心论文（如arXiv/Nature子刊）、巨头前沿实验室的首发技术落地。

    【硬性拦截规则】：
    如果该新闻只是：成熟巨头/上市公司的常规财报披露、普通的产品版本迭代更新、公关软文、老总出席会议的花边八卦、或者不痛不痒的日常行业流水账，请【仅仅回复】四个字：忽略推送

    【正常解读格式】：
    如果高度符合“早期黑马”或“创新科技”标准，请直接切入本质，严格按照以下格式回复（不要说任何客套话，不要包含任何反引号）：
    🔴 **黑马核心/硬核突破：** [用最硬核简练的语言，一句话直接刺破该项目/技术的创新本质或团队背景，剔除公关水分]
    📈 **颠覆影响/Alpha推演：** [精准推演该技术或项目对产业上下游、大模型算力、或实体二级赛道的链式反应，指出谁可能被颠覆，哪里有聪明钱的肉吃]
    """
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15
    }
    
    # 工业级控频阀：每次向 AI 递折子前严格小憩 5.5 秒
    time.sleep(5.5)
    
    try:
        res = requests.post(AI_API_URL, json=payload, headers=headers, timeout=15)
        res_data = res.json()
        
        if 'choices' in res_data and len(res_data['choices']) > 0:
            raw_reply = res_data['choices'][0]['message']['content'].strip()
            clean_reply = raw_reply.replace('`', '').replace('markdown', '').strip()
            
            if "忽略推送" in clean_reply or len(clean_reply) < 8:
                return "FILTERED"
                
            return clean_reply
        
        print(f"   [API无响应细节]: {res_data}")
        return None
    except Exception as e:
        print(f"   [API通讯异常细节]: {e}")
        return None

def send_feishu(site_name, title, summary, link):
    safe_title = clean_html(title)[:100]
    safe_summary = clean_html(summary)[:180]
    if not safe_summary:
        safe_summary = "点击下方按钮阅读原文详情。"
    else:
        safe_summary += "..."
    
    print(f"-> 正在尝试为 [{site_name}] 进行黑马级别 AI 智能鉴别...")
    ai_interpreted_content = get_ai_summary(safe_title, summary)
    
    if ai_interpreted_content == "FILTERED":
        print(f"   [熔断] AI 判定 [{site_name}] 为行业常规噪音，已成功拦截。")
        return

    # 终极智能双保险：AI计算完美时吐出橙色研报卡片；API突发超时时蓝色快讯卡片无漏单强推
    if ai_interpreted_content:
        card_title = f"🚀 {site_name} · 黑马科技研报"
        header_template = "orange"
        formatted_body = ai_interpreted_content
    else:
        print(f"   [降级] AI接口超时，转为清爽蓝色普通卡片，确保绝不漏单。")
        card_title = f"🔔 {site_name} · 实时速递"
        header_template = "blue"
        formatted_body = f"📝 **内容摘要：**\n\n*{safe_summary}*"

    card_msg = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "title": {"tag": "plain_text", "text": card_title},
                "template": header_template
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"⚡️ **资讯源标题**\n**{safe_title}**"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"{formatted_body}"}},
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {"tag": "button", "text": {"tag": "plain_text", "text": "🚀 穿透阅读原文"}, "url": link, "type": "primary"}
                    ]
                }
            ]
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK, json=card_msg, timeout=10)
    except Exception as e:
        print(f"飞书推送失败: {e}")

def main():
    record_file = "record.json"
    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf-8") as f:
            try: old_record = json.load(f)
            except: old_record = {}
    else:
        old_record = {}

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for info in SITE_LIST:
        site_name = info["name"]
        site_url = info["url"]

        try:
            res = requests.get(site_url, headers=headers, timeout=15)
            feed = feedparser.parse(res.text)
        except:
            continue

        if not feed.entries:
            continue

        # 🚀 纵深25条全量扫描滑窗：哪怕 GitHub 迟到，积压的论文、新品和投融资也绝不漏单！
        entries_to_check = feed.entries[:25]
        entries_to_check.reverse()

        for entry in entries_to_check:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))

            if not link:
                continue

            cache_key = f"{site_name}_{link}"

            if old_record.get(cache_key) is None and old_record.get(site_url) != link:
                send_feishu(site_name, title, summary, link)
                old_record[cache_key] = "read"
                old_record[site_url] = link

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(old_record, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
