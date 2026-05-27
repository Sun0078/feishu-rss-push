import requests
import feedparser
import json
import os
import re
from datetime import datetime

# ========== 唯一修改处：粘贴你的飞书机器人链接 ==========
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"
# ========================================================

SITE_LIST = [
    # ==================== 一、央行 + 金融监管（全量放行，换用稳定节点） ====================
    {"name": "中国人民银行-公告", "url": "https://rsshub.app/sina/gov/pbc", "keys": []},
    {"name": "证监会官网-动态", "url": "https://rsshub.app/sina/gov/csrc", "keys": []},
    {"name": "金融监管总局", "url": "https://rsshub.app/gov/nfra/news", "keys": []},
    {"name": "央行公开市场操作", "url": "https://rsshub.app/gov/pbc/goutongjiaoliu", "keys": []},
    {"name": "美联储资讯(Fed)", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "keys": []},

    # ==================== 二、宏观财经大盘（商业源：保留关键词降噪） ====================
    {"name": "华尔街见闻-实时快讯", "url": "https://feedx.net/rss/wallstreetcn.xml", "keys": ["全球行情", "盘面解读", "突发", "重磅"]},
    {"name": "财新网-金融要闻", "url": "https://feedx.net/rss/caixin.xml", "keys": ["市场动态", "产业经济", "降息", "重磅"]},
    {"name": "第一财经-股市", "url": "https://feedx.net/rss/yicai.xml", "keys": ["A股", "板块热点", "大盘"]},
    {"name": "雪球投资热帖", "url": "https://rsshub.app/xueqiu/hots", "keys": ["个股", "资金流向", "调研"]},
    {"name": "国家统计局-数据", "url": "https://rsshub.app/sina/gov/stats", "keys": ["经济数据", "物价GDP", "CPI"]},
    {"name": "中证网-证券基金", "url": "https://feedx.net/rss/cs.xml", "keys": ["证券", "基金", "公告"]},
    {"name": "路透国际财经", "url": "https://feedx.net/rss/reuters.xml", "keys": []},

    # ==================== 三、创投 + 融资 + 黑马企业 ====================
    {"name": "36氪-创投快讯", "url": "https://36kr.com/feed", "keys": ["融资", "并购", "创业项目", "独角兽"]},
    {"name": "钛媒体-创投", "url": "https://feedx.net/rss/tmtpost.xml", "keys": ["初创企业", "赛道投资", "融资"]},
    {"name": "猎云网创投", "url": "https://feedx.net/rss/lieyunwang.xml", "keys": ["初创企业", "赛道投资", "融资"]},
    {"name": "创业邦", "url": "https://rsshub.app/cyzone/news", "keys": ["黑马企业", "早期融资", "独角兽"]},
    {"name": "投资界(清科)", "url": "https://rsshub.app/zero2ipo/news", "keys": ["VC/PE", "PreIPO", "募资"]},
    {"name": "黑马创业资讯", "url": "https://rsshub.app/heimaying/news", "keys": ["隐形黑马", "成长企业", "融资"]},

    # ==================== 四、硬科技 + 前沿新技术 ====================
    {"name": "科创板日报", "url": "https://rsshub.app/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rsshub.app/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rsshub.app/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rsshub.app/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量接收） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rsshub.app/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rsshub.app/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rsshub.app/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rsshub.app/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def clean_html(raw_html):
    if not raw_html:
        return ""
    # 去除各种HTML标签、特殊多余字符，防止飞书19002解析报错
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&mdsh;', '—').replace('&quot;', '"')
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

def send_feishu(site_name, title, summary, link):
    safe_title = clean_html(title)[:100]
    safe_summary = clean_html(summary)[:180]
    
    if not safe_summary:
        safe_summary = "点击下方按钮阅读原文详情。"
    else:
        safe_summary += "..."

    # 升级为官方标准高容错交互卡片格式，彻底告别 19002 报错
    card_msg = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "text": f"🔔【{site_name}】发现新动态！"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📌 标题：**\n{safe_title}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📝 内容摘要：**\n*{safe_summary}*"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "text": "🚀 直达原文阅读"
                            },
                            "url": link,
                            "type": "default"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        res = requests.post(FEISHU_WEBHOOK, json=card_msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_feishu("系统链路测试", f"GitHub Actions 终极高容错卡片版激活成功！", f"当前时间：{now_str}。全新卡片架构已就绪，已切换全线备用稳定节点，大水管正式蓄水...", "https://github.com")
    
    record_file = "record.json"
    
    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf-8") as f:
            try:
                old_record = json.load(f)
            except:
                old_record = {}
    else:
        old_record = {}

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for info in SITE_LIST:
        site_name = info["name"]
        site_url = info["url"]
        keywords = info.get("keys", [])

        print(f"正在扫描: {site_name}")
        try:
            res = requests.get(site_url, headers=headers, timeout=15)
            feed = feedparser.parse(res.text)
        except Exception as e:
            print(f"{site_name} 请求失败: {e}")
            continue

        if not feed.entries:
            continue

        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "")
        link = latest_entry.get("link", "")
        summary = latest_entry.get("summary", latest_entry.get("description", ""))

        if not link:
            continue

        if old_record.get(site_url) != link:
            is_match = False
            if not keywords:
                is_match = True
            else:
                for kw in keywords:
                    if kw in title or kw in summary:
                        is_match = True
                        break
            
            if is_match:
                print(f"发现新文章并命中关键词: {title}")
                send_feishu(site_name, title, summary, link)
            
            old_record[site_url] = link

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(old_record, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
