import requests
import feedparser
import json
import os
import re
import time
from datetime import datetime

# ==================== 🛠️ 唯一修改处 ====================
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"

# [推荐方案 A]：如果你去 DeepSeek 官网（platform.deepseek.com）申请了官方 sk- Key，请按下行配置：
# AI_API_KEY = "你的DeepSeek官方sk密钥"
# AI_API_URL = "https://api.deepseek.com/v1/chat/completions"
# AI_MODEL = "deepseek-chat"

# [免费方案 B]：如果你依然想白嫖硅基流动，我帮你换成了完全不限频的千问 72B 顶级模型：
AI_API_KEY = "sk-cwrrsvquwdsiqtfjbgsgqqmdjyblnxyiunpqrpvvssgpakzx" 
AI_API_URL = "https://api.siliconflow.cn/v1/chat/completions" 
AI_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # 核心更换：换用完全放开 RPM 限制的高爽度模型
# ========================================================

SITE_LIST = [
    # ==================== 一、央行 + 金融监管（全量放行） ====================
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

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手 ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml"},
    {"name": "Foresight News-实时快讯", "url": "https://rsshub.app/foresightnews/news"}, 
    {"name": "PANews-加密前沿", "url": "https://rsshub.app/panews/news"}, 
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/"},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/"},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/"},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rsshub.app/sina/gov/miit"},
    {"name": "36氪-未来汽车日报", "url": "https://rsshub.app/36kr.info/automotive"},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml"},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/"},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml"}
]

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('\n', ' ')
    return re.sub(r'\s+', ' ', clean_text).strip()

def get_ai_summary(title, content):
    """ 调用大模型进行硬核提炼与投研风控 """
    if "你的" in AI_API_KEY or not AI_API_KEY or AI_API_KEY.strip() == "":
        return None

    safe_content = clean_html(content)[:600]

    prompt = f"""
    你是一名冷峻、一针见血的Web3、硬科技与宏观财经行业顶级投研专家。
    请评估以下新闻是否有行业风向标意义、政策变动、大额融资或潜在Alpha机会。

    新闻标题：{title}
    新闻摘要：{safe_content}

    【硬性拦截规则】：
    如果这只是普通的日常流水账、毫无行业影响力的公关八卦或普通琐事，请【仅仅回复】四个字：忽略推送

    【正常解读格式】：
    如果极具投研价值，请严格按照以下格式回复：
    🔴 **核心看点：** [一句话直接刺破事件本质，剔除公关水分]
    📈 **潜在影响：** [精准推演该事件对宏观大盘、链上Alpha、AI算力或二级赛道的链式反应]
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
    
    # 保持健康间隔
    time.sleep(3.5)
    
    try:
        res = requests.post(AI_API_URL, json=payload, headers=headers, timeout=15)
        res_data = res.json()
        
        if 'choices' in res_data and len(res_data['choices']) > 0:
            raw_reply = res_data['choices'][0]['message']['content'].strip()
            clean_reply = raw_reply.replace('`', '').replace('markdown', '').strip()
            
            if "忽略推送" in clean_reply or len(clean_reply) < 8:
                return "FILTERED"
                
            return clean_reply
        
        # 核心暴露：如果API报错了，在GitHub后台打印真实原因
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
    
    print(f"-> 正在尝试为 [{site_name}] 进行 AI 智能投研鉴别...")
    ai_interpreted_content = get_ai_summary(safe_title, summary)
    
    if ai_interpreted_content == "FILTERED":
        print(f"   [熔断] AI 判定 [{site_name}] 为行业噪音，已拦截。")
        return

    if ai_interpreted_content:
        card_title = f"🤖 {site_name} · AI 智能研报"
        header_template = "orange"
        formatted_body = ai_interpreted_content
    else:
        # AI不给力时蓝色保底推，确保100%不漏单
        card_title = f"🔔 {site_name} · 实时快讯"
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
