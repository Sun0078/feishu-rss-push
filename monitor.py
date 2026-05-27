import requests
import feedparser
import json
import os
from datetime import datetime

# ========== 唯一修改处：粘贴你的飞书机器人链接 ==========
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/834cd07d-3e9f-4ee3-8a7b-49a49ee7bd31"
# ========================================================

SITE_LIST = [
    {"name": "测试高频源", "url": "https://wallstreetcn.com/rss/", "keys": []},
    # 央行+金融监管
    {"name":"中国人民银行","url":"https://www.pbc.gov.cn/rss/rss.xml","keys":["降息","降准","货币政策"]},
    {"name":"证监会官网","url":"https://www.csrc.gov.cn/csrc/c100028/c100029/rss.xml","keys":["IPO","监管","退市"]},
    {"name":"金融监管总局","url":"https://rsshub.app/gov/nfra/news","keys":["银行保险","金融政策"]},
    {"name":"央行公开市场","url":"https://rsshub.app/gov/pbc/goutongjiaoliu","keys":["逆回购","MLF"]},
    {"name":"美联储资讯","url":"https://www.federalreserve.gov/feeds/press_all.xml","keys":["加息","美元"]},
    # 宏观财经大盘
    {"name":"财新金融","url":"https://www.caixin.com/rss/finance.xml","keys":["市场动态","产业经济"]},
    {"name":"华尔街见闻","url":"https://wallstreetcn.com/rss/","keys":["全球行情","盘面解读"]},
    {"name":"第一财经股市","url":"https://www.yicai.com/rss/stock.xml","keys":["A股","板块热点"]},
    {"name":"雪球投资热帖","url":"https://xueqiu.com/hots/topic/rss","keys":["个股","资金流向"]},
    {"name":"国家统计局","url":"https://www.stats.gov.cn/rss/tjsj.xml","keys":["经济数据","物价GDP"]},
    {"name":"中证网财经","url":"https://www.cs.com.cn/rss/","keys":["证券基金"]},
    # 创投+融资+黑马企业
    {"name":"36氪创投","url":"https://36kr.com/feed/column/venture","keys":["融资","并购","创业项目"]},
    {"name":"猎云网创投","url":"https://www.lieyunwang.com/feed","keys":["初创企业","赛道投资"]},
    {"name":"创业邦","url":"https://rsshub.app/cyzone/news","keys":["黑马企业","早期融资"]},
    {"name":"投资界","url":"https://rsshub.app/zero2ipo/news","keys":["VC/PE","PreIPO"]},
    # 硬科技+前沿新技术
    {"name":"科创板日报","url":"https://rsshub.app/cls/kechuangban","keys":["科创企业","专精特新"]},
    {"name":"机器之心AI","url":"https://www.jiqizhixin.com/rss","keys":["大模型","AI新技术"]},
    {"name":"量子位前沿科技","url":"https://www.qbitai.com/rss","keys":["算力","前沿突破"]},
    {"name":"极客公园","url":"https://rsshub.app/geekpark/news","keys":["技术落地","创新产品"]},
    # 海外顶级科技创投
    {"name":"TechCrunch硬科技","url":"https://techcrunch.com/tag/hard-tech/feed","keys":["海外黑科技初创"]},
    {"name":"MIT科技评论","url":"https://www.technologyreview.com/feed/","keys":["未来技术趋势赛道风口"]}
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
