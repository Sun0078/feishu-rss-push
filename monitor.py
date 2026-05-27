import requests
import feedparser
import json
import os
from datetime import datetime
import time  # 新增：用于重试和时间戳

# ========== 唯一修改处：粘贴你的飞书机器人链接 ==========
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"
# ========================================================

# 新增：全局配置
RETRY_TIMES = 3  # 请求失败重试次数
RETRY_DELAY = 2  # 重试间隔（秒）
SUMMARY_MAX_LENGTH = 150  # 摘要最大长度

SITE_LIST = [
    # 原配置保持不变
    {"name": "中国人民银行-公告", "url": "https://rss.feedverse.info/sina/gov/pbc", "keys": []},
    {"name": "证监会官网-动态", "url": "https://rss.feedverse.info/sina/gov/csrc", "keys": []},
    {"name": "金融监管总局", "url": "https://rss.feedverse.info/gov/nfra/news", "keys": []},
    {"name": "央行公开市场操作", "url": "https://rss.feedverse.info/gov/pbc/goutongjiaoliu", "keys": []},
    {"name": "美联储资讯(Fed)", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "keys": []},
    {"name": "华尔街见闻-实时快讯", "url": "https://feedx.net/rss/wallstreetcn.xml", "keys": ["全球行情", "盘面解读", "突发", "重磅"]},
    {"name": "财新网-金融要闻", "url": "https://feedx.net/rss/caixin.xml", "keys": ["市场动态", "产业经济", "降息", "重磅"]},
    {"name": "第一财经-股市", "url": "https://feedx.net/rss/yicai.xml", "keys": ["A股", "板块热点", "大盘"]},
    {"name": "雪球投资热帖", "url": "https://rss.feedverse.info/xueqiu/hots", "keys": ["个股", "资金流向", "调研"]},
    {"name": "国家统计局-数据", "url": "https://rss.feedverse.info/sina/gov/stats", "keys": ["经济数据", "物价GDP", "CPI"]},
    {"name": "中证网-证券基金", "url": "https://feedx.net/rss/cs.xml", "keys": ["证券", "基金", "公告"]},
    {"name": "路透国际财经", "url": "https://feedx.net/rss/reuters.xml", "keys": []},
    {"name": "36氪-创投快讯", "url": "https://36kr.com/feed", "keys": ["融资", "并购", "创业项目", "独角兽"]},
    {"name": "钛媒体-创投", "url": "https://feedx.net/rss/tmtpost.xml", "keys": ["初创企业", "赛道投资", "融资"]},
    {"name": "猎云网创投", "url": "https://feedx.net/rss/lieyunwang.xml", "keys": ["初创企业", "赛道投资", "融资"]},
    {"name": "创业邦", "url": "https://rss.feedverse.info/cyzone/news", "keys": ["黑马企业", "早期融资", "独角兽"]},
    {"name": "投资界(清科)", "url": "https://rss.feedverse.info/zero2ipo/news", "keys": ["VC/PE", "PreIPO", "募资"]},
    {"name": "黑马创业资讯", "url": "https://rss.feedverse.info/heimaying/news", "keys": ["隐形黑马", "成长企业", "融资"]},
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": []},
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def send_feishu(site_name, title, summary, link):
    """优化版飞书推送：增加异常重试和更健壮的文本处理"""
    # 更彻底的HTML标签清理
    import re
    clean_summary = re.sub(r'<[^>]+>', '', summary)  # 正则移除所有HTML标签
    clean_summary = clean_summary.replace('&nbsp;', ' ').replace('\n', ' ').strip()
    
    if len(clean_summary) > SUMMARY_MAX_LENGTH:
        clean_summary = clean_summary[:SUMMARY_MAX_LENGTH] + "..."
    elif not clean_summary:
        clean_summary = "点击下方链接直接查看原文详情。"

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [{"tag": "text", "text": "📌 标题：\n"}, {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}],
                        [{"tag": "text", "text": "📝 内容摘要：\n"}, {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}],
                        [{"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}],
                        [{"tag": "text", "text": f"\n⏰ 推送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')"}]
                    ]
                }
            }
        }
    }
    
    # 增加推送重试机制
    for attempt in range(RETRY_TIMES):
        try:
            res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
            res.raise_for_status()  # 抛出HTTP状态码异常
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{site_name}] 推送成功: {title[:30]}...")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{site_name}] 推送失败(第{attempt+1}次): {str(e)}")
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY)
    return False

def fetch_rss_with_retry(url, headers):
    """带重试的RSS请求函数"""
    for attempt in range(RETRY_TIMES):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            return feedparser.parse(res.text)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 请求失败(第{attempt+1}次) {url}: {str(e)}")
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY)
    return None

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 资讯监控脚本启动")
    send_feishu("系统链路测试", "GitHub Actions 终极全量卡片版上线成功！", 
               "测试摘要：大水管全量监测模式已开启。核心渠道零拦截，30分钟内自动巡查更新...", 
               "https://github.com")
    
    record_file = "record.json"
    old_record = {}
    
    # 安全加载历史记录
    if os.path.exists(record_file):
        try:
            with open(record_file, "r", encoding="utf-8") as f:
                old_record = json.load(f)
        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 历史记录文件损坏，将重新创建")
            old_record = {}
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 读取历史记录失败: {str(e)}")
            old_record = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
    }

    new_count = 0
    for info in SITE_LIST:
        site_name = info["name"]
        site_url = info["url"]
        keywords = info.get("keys", [])

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在扫描: {site_name}")
        feed = fetch_rss_with_retry(site_url, headers)
        
        if not feed or not feed.entries:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {site_name} 无新内容或请求失败")
            continue

        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "无标题").strip()
        link = latest_entry.get("link", "").strip()
        summary = latest_entry.get("summary", latest_entry.get("description", "")).strip()

        if not link:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {site_name} 文章无有效链接，跳过")
            continue

        # 检查是否为新文章
        if old_record.get(site_url) != link:
            # 关键词过滤
            is_match = False
            if not keywords:
                is_match = True
            else:
                for kw in keywords:
                    if kw.lower() in title.lower() or kw.lower() in summary.lower():
                        is_match = True
                        break
            
            if is_match:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现新文章并命中关键词: {title}")
                if send_feishu(site_name, title, summary, link):
                    new_count += 1
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 新文章未命中关键词，跳过: {title}")
            
            # 无论是否命中都更新记录，避免重复推送
            old_record[site_url] = link
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 无新文章")

    # 保存更新后的记录
    try:
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(old_record, f, ensure_ascii=False, indent=4)
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 扫描完成，本次推送 {new_count} 条新资讯")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 保存历史记录失败: {str(e)}")

if __name__ == "__main__":
    main()
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量接收） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def send_feishu(site_name, title, summary, link):
    clean_summary = summary.replace('<', '').replace('>', '').replace('&nbsp;', ' ').replace('\n', '').strip()[:150]
    if not clean_summary:
        clean_summary = "点击下方链接直接查看原文详情。"
    else:
        clean_summary += "..."

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [
                            {"tag": "text", "text": "📌 标题：\n"},
                            {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}
                        ],
                        [
                            {"tag": "text", "text": "📝 内容摘要：\n"},
                            {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}
                        ],
                        [
                            {"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}
                        ]
                    ]
                }
            }
        }
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    send_feishu("系统链路测试", "GitHub Actions 终极全量卡片版上线成功！", "测试摘要：大水管全量监测模式已开启。核心渠道零拦截，30分钟内自动巡查更新...", "https://github.com")
    
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
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量接收） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def send_feishu(site_name, title, summary, link):
    clean_summary = summary.replace('<', '').replace('>', '').replace('&nbsp;', ' ').replace('\n', '').strip()[:150]
    if not clean_summary:
        clean_summary = "点击下方链接直接查看原文详情。"
    else:
        clean_summary += "..."

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [
                            {"tag": "text", "text": "📌 标题：\n"},
                            {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}
                        ],
                        [
                            {"tag": "text", "text": "📝 内容摘要：\n"},
                            {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}
                        ],
                        [
                            {"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}
                        ]
                    ]
                }
            }
        }
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    send_feishu("系统链路测试", "GitHub Actions 终极全量卡片版上线成功！", "测试摘要：大水管全量监测模式已开启。核心渠道零拦截，30分钟内自动巡查更新...", "https://github.com")
    
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
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量接收） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def send_feishu(site_name, title, summary, link):
    clean_summary = summary.replace('<', '').replace('>', '').replace('&nbsp;', ' ').replace('\n', '').strip()[:150]
    if not clean_summary:
        clean_summary = "点击下方链接直接查看原文详情。"
    else:
        clean_summary += "..."

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [
                            {"tag": "text", "text": "📌 标题：\n"},
                            {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}
                        ],
                        [
                            {"tag": "text", "text": "📝 内容摘要：\n"},
                            {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}
                        ],
                        [
                            {"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}
                        ]
                    ]
                }
            }
        }
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    send_feishu("系统链路测试", "GitHub Actions 终极全量卡片版上线成功！", "测试摘要：大水管全量监测模式已开启。核心渠道零拦截，30分钟内自动巡查更新...", "https://github.com")
    
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
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": []},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": []},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破", "大模型", "芯片"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品", "AI"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": []},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": []},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": []},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": []},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": []},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手（全量接收不漏单） ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": []},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": []},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": []},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": []},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding", "investment"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": []},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "芯片", "出海"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": []},

    # ==================== 十、大厂与前沿实验室技术落地（核心源全量放行） ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": []}
]

def send_feishu(site_name, title, summary, link):
    # 清洗并美化 HTML，截取前 150 字摘要
    clean_summary = summary.replace('<', '').replace('>', '').replace('&nbsp;', ' ').replace('\n', '').strip()[:150]
    if not clean_summary:
        clean_summary = "点击下方链接直接查看原文详情。"
    else:
        clean_summary += "..."

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [
                            {"tag": "text", "text": "📌 标题：\n"},
                            {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}
                        ],
                        [
                            {"tag": "text", "text": "📝 内容摘要：\n"},
                            {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}
                        ],
                        [
                            {"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}
                        ]
                    ]
                }
            }
        }
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    # 链路激活广播
    send_feishu("系统链路测试", "GitHub Actions 终极全量卡片版上线成功！", "测试摘要：大水管全量监测模式已开启。核心渠道零拦截，30分钟内自动巡查更新...", "https://github.com")
    
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
    {"name": "科创板日报", "url": "https://rss.feedverse.info/cls/kechuangban", "keys": ["科创企业", "专精特新"]},
    {"name": "机器之心AI", "url": "https://www.jiqizhixin.com/rss", "keys": ["大模型", "AI新技术"]},
    {"name": "量子位-前沿科技", "url": "https://feedx.net/rss/qbitai.xml", "keys": ["算力", "前沿突破"]},
    {"name": "极客公园", "url": "https://rss.feedverse.info/geekpark/news", "keys": ["技术落地", "创新产品"]},
    {"name": "高工机器人", "url": "https://rss.feedverse.info/gg-robot/news", "keys": ["人形机器人", "工业智造"]},

    # ==================== 五、航天 + 高端制造 ====================
    {"name": "中国航天新闻", "url": "https://rss.feedverse.info/sina/gov/cnsa", "keys": ["火箭", "卫星", "空间站"]},
    {"name": "NASA航天资讯", "url": "https://www.nasa.gov/news-release/feed/", "keys": ["太空科技", "深空探测"]},

    # ==================== 六、海外顶级科技创投 ====================
    {"name": "TechCrunch HardTech", "url": "https://techcrunch.com/tag/hard-tech/feed/", "keys": ["海外黑科技", "初创"]},
    {"name": "MIT科技评论", "url": "https://www.technologyreview.com/feed/", "keys": ["未来技术趋势", "赛道风口"]},

    # ==================== 七、Web3 智库 + 链上 Alpha 猎手 ====================
    {"name": "ChainCatcher-链捕手", "url": "https://feedx.net/rss/chaincatcher.xml", "keys": ["融资", "空投", "核心协议", "Alpha"]},
    {"name": "Foresight News-实时快讯", "url": "https://rss.feedverse.info/foresightnews/news", "keys": []},
    {"name": "PANews-加密前沿", "url": "https://rss.feedverse.info/panews/news", "keys": ["融资", "监管", "以太坊", "Meme"]},
    {"name": "CoinDesk-Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "keys": ["Bitcoin", "ETF", "SEC", "Fed"]},

    # ==================== 八、全球顶级 VC 与创投风向标 ====================
    {"name": "a16z Crypto-加密创投", "url": "https://a16zcrypto.com/feed/", "keys": []},
    {"name": "Crunchbase News-全球融资", "url": "https://news.crunchbase.com/feed/", "keys": ["Funding", "Acquisition", "AI", "Unicorn"]},
    {"name": "VentureBeat-新兴科技", "url": "https://venturebeat.com/feed/", "keys": ["AI", "generative AI", "funding"]},

    # ==================== 九、国内产业政策与硬科技风向 ====================
    {"name": "工信部-政策发布", "url": "https://rss.feedverse.info/sina/gov/miit", "keys": ["半导体", "人工智能", "低空经济", "专精特新"]},
    {"name": "36氪-未来汽车日报", "url": "https://rss.feedverse.info/36kr.info/automotive", "keys": ["智驾", "固态电池", "小米汽车", "特斯拉"]},
    {"name": "集微网-半导体风向", "url": "https://feedx.net/rss/jiwei.xml", "keys": ["芯片", "光刻机", "美光", "台积电"]},

    # ==================== 十、大厂与前沿实验室技术落地 ====================
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "keys": []},
    {"name": "Google Research Blog", "url": "https://blog.google/technology/research/rss/", "keys": []},
    {"name": "NVIDIA Newsroom", "url": "https://nvidianews.nvidia.com/releases.xml", "keys": ["GPU", "Blackwell", "AI", "B200"]}
]

def send_feishu(site_name, title, summary, link):
    # 清洗HTML标签，截取前150字摘要，保证卡片整洁
    clean_summary = summary.replace('<', '').replace('>', '').replace('&nbsp;', ' ')[:150]
    if not clean_summary.strip():
        clean_summary = "点击下方链接查看原文详情。"
    else:
        clean_summary += "..."

    msg = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"🔔【{site_name}】发现新动态！",
                    "content": [
                        [
                            {"tag": "text", "text": "📌 标题：\n"},
                            {"tag": "text", "text": f"{title}\n\n", "style": ["bold"]}
                        ],
                        [
                            {"tag": "text", "text": "📝 内容摘要：\n"},
                            {"tag": "text", "text": f"{clean_summary}\n\n", "style": ["italic"]}
                        ],
                        [
                            {"tag": "a", "text": "🚀 点击这里 ➡️ 直达原文阅读", "href": link}
                        ]
                    ]
                }
            }
        }
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        print(f"[{site_name}] 推送响应: {res.json()}")
    except Exception as e:
        print(f"[{site_name}] 飞书推送失败: {e}")

def main():
    # 链路激活广播
    send_feishu("系统链路测试", "GitHub Actions 终极富文本卡片版上线成功！", "测试摘要：系统正在使用全新架构全网扫描中，30分钟内自动巡查...", "https://github.com")
    
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

        # 提取最新一篇文章的核心要素
        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "")
        link = latest_entry.get("link", "")
        summary = latest_entry.get("summary", latest_entry.get("description", ""))

        if not link:
            continue

        # 比对去重
        if old_record.get(site_url) != link:
            is_match = False
            if not keywords:
                is_match = True
            else:
                # 标题或摘要中包含任意关键词即放行
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
