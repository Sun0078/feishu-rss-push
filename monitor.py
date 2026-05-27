import requests
import feedparser
import json
import os
from datetime import datetime

# ========== 唯一修改处：粘贴你的飞书机器人链接 ==========
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"
# ========================================================

   SITE_LIST = [
    # ==================== 一、央行 + 金融监管 ====================
    # 原因：官网原生RSS停用或对海外机房IP严格物理阻断。
    # 替代：改用新浪财经高频抓取的官方公告流，以及支持海外机房的 RSSHub 优质公共节点。
    {"name": "中国人民银行-公告", "url": "https://rss.feedverse.info/sina/gov/pbc", "keys": ["降息", "降准", "货币政策"]},
    {"name": "证监会官网-动态", "url": "https://rss.feedverse.info/sina/gov/csrc", "keys": ["IPO", "监管", "退市"]},
    {"name": "金融监管总局", "url": "https://rss.feedverse.info/gov/nfra/news", "keys": ["银行保险", "金融政策"]},
    {"name": "央行公开市场操作", "url": "https://rss.feedverse.info/gov/pbc/goutongjiaoliu", "keys": ["逆回购", "MLF", "公开市场"]},
    {"name": "美联储资讯(Fed)", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "keys": ["加息", "美元"]},

    # ==================== 二、宏观财经大盘 ====================
    # 原因：财新、华尔街见闻、雪球对微软Azure机房（GitHub运行环境）有极严格的Cloudflare五秒盾反爬。
    # 替代：使用 feedx 干净清洁节点或支持跨国抓取的镜像，保障内容不被403阻断。
    {"name": "华尔街见闻-实时快讯", "url": "https://feedx.net/rss/wallstreetcn.xml", "keys": ["全球行情", "盘面解读"]},
    {"name": "财新网-金融要闻", "url": "https://feedx.net/rss/caixin.xml", "keys": ["市场动态", "产业经济"]},
    {"name": "第一财经-股市", "url": "https://feedx.net/rss/yicai.xml", "keys": ["A股", "板块热点"]},
    {"name": "雪球投资热帖", "url": "https://rss.feedverse.info/xueqiu/hots", "keys": ["个股", "资金流向"]},
    {"name": "国家统计局-数据", "url": "https://rss.feedverse.info/sina/gov/stats", "keys": ["经济数据", "物价GDP"]},
    {"name": "中证网-证券基金", "url": "https://feedx.net/rss/cs.xml", "keys": ["证券", "基金"]},

    # ==================== 三、创投 + 融资 + 黑马企业 ====================
    # 原因：36氪垂直栏目RSS收窄，创业邦、投资界走公共RSSHub极易超时。
    # 替代：聚合36氪全量高频流配合关键词过滤，RSSHub节点替换为高可用海外镜像。
    {"name": "36氪-创投快讯", "url": "https://36kr.com/feed", "keys": ["融资", "并购", "创业项目"]},
    {"name": "钛媒体-创投", "url": "https://feedx.net/rss/tmtpost.xml", "keys": ["初创企业", "赛道投资"]},
    {"name": "创业邦", "url": "https://rss.feedverse.info/cyzone/news", "keys": ["黑马企业", "早期融资"]},
    {"name": "投资界(清科)", "url": "https://rss.feedverse.info/zero2ipo/news", "keys": ["VC/PE", "PreIPO"]},

    # ==================== 四、硬科技 + 前沿新技术 ====================
    # 原因：科创板日报反爬严重，量子位及极客公园原生RSS偶发性XML格式格式化错误。
    # 替代：引入财联社/科创板代理流，修复原生科技媒体的格式兼容性。
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": ["科创企业", "专精特新"]},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": ["大模型", "AI新技术"]},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品"]},

    # ==================== 五、海外顶级科技创投 ====================
    # 原因：原生源无问题，但在海外机房运行时，无需设置复杂的过滤关键词即可秒级响应。
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []}
]
def send_feishu(site_name, title, link):
    msg = {
        "msg_type": "text",
        "content": {
            "text": f"🔔【{site_name}】有新动态！\n\n📌标题：{title}\n🔗直达：{link}\n⏰时间：{datetime.now().strftime('%m-%d %H:%M')}"
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
    except Exception as e:
        print(f"飞书推送失败: {e}")

def main():
    record_file = "record.json"
    
    # 读取历史记录
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

        # 获取最新的一条文章
        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "")
        link = latest_entry.get("link", "")

        if not link:
            continue

        # 检查是否是全新文章
        if old_record.get(site_url) != link:
            # 命中关键词过滤（若命中，或关键词列表为空则放行）
            is_match = False
            if not keywords:
                is_match = True
            else:
                for kw in keywords:
                    if kw in title:
                        is_match = True
                        break
            
            if is_match:
                print(f"发现新文章并命中关键词: {title}")
                send_feishu(site_name, title, link)
            
            # 更新记录
            old_record[site_url] = link

    # 保存最新记录到本地文件
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(old_record, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
