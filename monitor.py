import requests
import feedparser
import json
import os
import re
from datetime import datetime

# ==================== 🛠️ 唯一修改处 ====================
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"

# 推荐去 siliconflow.cn (硅基流动) 或 deepseek.com 注册一个免费API Key填在这里
# 如果暂时没有，可以先保持原样，代码自带了完美的零Key兼容回退机制，绝对不报错
AI_API_KEY = "sk-cwrrsvquwdsiqtfjbgsgqqmdjyblnxyiunpqrpvvssgpakzx" 
AI_API_URL = "https://api.siliconflow.cn/v1/chat/completions" # 默认硅基流动接口
AI_MODEL = "deepseek-ai/DeepSeek-V3" # 使用的高性能大模型名称
# ========================================================

SITE_LIST = [
    # ==================== 一、央行 + 金融监管（全量放行） ====================
    {"name": "中国人民银行-公告", "url": "https://rsshub.app/sina/gov/pbc", "keys": []},
    {"name": "证监会官网-动态", "url": "https://rsshub.app/sina/gov/csrc", "keys": []},
    {"name": "金融监管总局", "url": "https://rsshub.app/gov/nfra/news", "keys": []},
    {"name": "央行公开市场操作", "url": "https://rsshub.app/gov/pbc/goutongjiaoliu", "keys": []},
    {"name": "美联储资讯(Fed)", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "keys": []},

    # ==================== 二、宏观财经大盘（全量放行） ====================
    {"name": "华尔街见闻-实时快讯", "url": "https://feedx.net/rss/wallstreetcn.xml", "keys": []},
    {"name": "财新网-金融要闻", "url": "https://feedx.net/rss/caixin.xml", "keys": []},
    {"name": "第一财经-股市", "url": "https://feedx.net/rss/yicai.xml", "keys": []},
    {"name": "雪球投资热帖", "url": "https://rsshub.app/xueqiu/hots", "keys": []},
    {"name": "国家统计局-数据", "url": "https://rsshub.app/sina/gov/stats", "keys": []},
    {"name": "中证网-证券基金", "url": "https://feedx.net/rss/cs.xml", "keys": []},
    {"name": "路透国际财经", "url": "https://feedx.net/rss/reuters.xml", "keys": []},

    # ==================== 三、创投 + 融资 + 黑马企业（全量放行） ====================
    {"name": "36氪-创投快讯", "url": "https://36kr.com/feed", "keys": []},
    {"name": "钛媒体-创投", "url": "https://feedx.net/rss/tmtpost.xml", "keys": []},
    {"name": "猎云网创投", "url": "https://feedx.net/rss/lieyunwang.xml", "keys": []},
    {"name": "创业邦", "url": "https://rsshub.app/cyzone/news", "keys": []},
    {"name": "投资界(清科)", "url": "https://rsshub.app/zero2ipo/news", "keys": []},
    {"name": "黑马创业资讯", "url": "https://rsshub.app/heimaying/news", "keys": []},

    # ==================== 四、硬科技 + 前沿新技术（全量放行） ====================
    {"name": "科创板日报", "url": "https://rsshub.app/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": []},
    {"name": "极客公园", "url": "https://rsshub.app/geekpark/news", "keys": []},
    {"name": "高工机器人", "url": "https://rsshub.app/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造（全量放行） ====================
    {"name": "中国航天新闻", "url": "https://rsshub.app/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投（全量放行） ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量放行） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rsshub.app/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rsshub.app/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标（全量放行） ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": []},

    # ==================== 九、国内产业政策与硬科技风向（全量放行） ====================
    {"name": "工信部-政策发布", "url": "https://rsshub.app/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rsshub.app/36kr.info/automotive", "keys": []},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地（全量放行） ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": []}
]

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('\n', ' ')
    return re.sub(r'\s+', ' ', clean_text).strip()

def get_ai_summary(title, content):
    """ 调用大模型对文章进行深度投研解读 """
    # 🕵️‍♂️ 核心熔断检测：如果用户没配置或者保持默认Key，自动返回空，让系统优雅降级，绝不报错崩盘
    if "你的" in AI_API_KEY or not AI_API_KEY or AI_API_KEY.strip() == "":
        return None

    prompt = f"""
    你是一名顶级的Web3和宏观财经智库研究员。请对以下新闻进行冷峻、直接、直击本质的智能化解读。
    新闻标题：{title}
    新闻内容/摘要：{content}

    请严格按照以下格式简短回复（控制在150字以内，不要有多余的废话）：
    【核心看点】一句话指出这篇动态的核心本质。
    【潜在影响】指出该事件对宏观大盘、Web3行业或硬科技赛道可能带来的链式反应。
    """
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        res = requests.post(AI_API_URL, json=payload, headers=headers, timeout=15)
        ai_reply = res.json()['choices'][0]['message']['content'].strip()
        return ai_reply
    except Exception as e:
        print(f"AI读取失败，原因: {e}")
        return None

def send_feishu(site_name, title, summary, link):
    safe_title = clean_html(title)[:100]
    safe_summary = clean_html(summary)[:180]
    
    if not safe_summary:
        safe_summary = "点击下方按钮阅读原文详情。"
    else:
        safe_summary += "..."

    # 尝试请求 AI 智能摘要
    print(f"-> 正在尝试为 [{site_name}] 生成AI智能解读...")
    ai_interpreted_content = get_ai_summary(safe_title, clean_html(summary))
    
    if ai_interpreted_content:
        # AI 解读成功：使用高级橙色卡片模板
        card_title = f"🤖【{site_name}】AI 智能解读版"
        header_template = "orange"
        main_content = ai_interpreted_content
    else:
        # 未配Key或AI超时：自动丝滑回退到标准蓝色数据卡片
        card_title = f"🔔【{site_name}】新动态快讯"
        header_template = "blue"
        main_content = f"**📝 内容摘要：**\n*{safe_summary}*"

    card_msg = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "text": card_title},
                "template": header_template
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**📌 资讯标题：**\n{safe_title}"}
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": main_content}
                },
                {
                    "tag": "hr"
                },
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

        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "")
        link = latest_entry.get("link", "")
        summary = latest_entry.get("summary", latest_entry.get("description", ""))

        if not link:
            continue

        # 核心去重过滤（完全无视关键词，有更新立刻放行推送）
        if old_record.get(site_url) != link:
            send_feishu(site_name, title, summary, link)
            old_record[site_url] = link

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(old_record, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
