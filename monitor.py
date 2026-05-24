import requests
import hashlib
from datetime import datetime

# ========== 唯一修改处：粘贴你的飞书机器人链接 ==========
FEISHU_WEBHOOK = "你的飞书webhook链接"
# ========================================================

# 【最终定稿全部站点 无重复 全覆盖】
SITE_LIST = [
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
    {"name":"路透国际财经","url":"https://cn.reuters.com/rssFeed/CNIntlBizNews/","keys":["外贸全球经济"]},

    # 创投+融资+黑马企业
    {"name":"36氪创投","url":"https://36kr.com/feed/column/venture","keys":["融资","并购","创业项目"]},
    {"name":"猎云网创投","url":"https://www.lieyunwang.com/feed","keys":["初创企业","赛道投资"]},
    {"name":"创业邦","url":"https://rsshub.app/cyzone/news","keys":["黑马企业","早期融资"]},
    {"name":"投资界","url":"https://rsshub.app/zero2ipo/news","keys":["VC/PE","PreIPO"]},
    {"name":"黑马创业资讯","url":"https://rsshub.app/heimaying/news","keys":["隐形黑马","成长企业"]},

    # 硬科技+前沿新技术
    {"name":"科创板日报","url":"https://rsshub.app/cls/kechuangban","keys":["科创企业","专精特新"]},
    {"name":"机器之心AI","url":"https://www.jiqizhixin.com/rss","keys":["大模型","AI新技术"]},
    {"name":"量子位前沿科技","url":"https://www.qbitai.com/rss","keys":["算力","前沿突破"]},
    {"name":"极客公园","url":"https://rsshub.app/geekpark/news","keys":["技术落地","创新产品"]},
    {"name":"高工机器人","url":"https://rsshub.app/gg-robot/news","keys":["人形机器人","工业智造"]},

    # 航天+高端制造
    {"name":"中国航天新闻","url":"https://www.chinaspacenews.com.cn/rss.xml","keys":["火箭卫星空间站"]},
    {"name":"NASA航天资讯","url":"https://www.nasa.gov/rss/dyn/breaking_news.rss","keys":["太空科技深空探测"]},

    # 海外顶级科技创投
    {"name":"TechCrunch硬科技","url":"https://techcrunch.com/tag/hard-tech/feed","keys":["海外黑科技初创"]},
    {"name":"MIT科技评论","url":"https://www.technologyreview.com/feed/","keys":["未来技术趋势赛道风口"]}
]

def get_page_md5(url):
    headers = {"User-Agent":"Mozilla/5.0"}
    try:
        res = requests.get(url,headers=headers,timeout=10)
        return hashlib.md5(res.text.encode()).hexdigest(),res.text
    except:
        return None, ""

def send_feishu(name,link):
    msg = {
        "msg_type":"text",
        "content":{"text":f"🔔资讯更新\n来源：{name}\n直达：{link}\n时间：{datetime.now().strftime('%m-%d %H:%M')}"}
    }
    requests.post(FEISHU_WEBHOOK,json=msg)

def main():
    try:
        with open("record.txt","r",encoding="utf-8") as f:
            old_record = eval(f.read())
    except:
        old_record = {}

    for info in SITE_LIST:
        site_name = info["name"]
        site_url = info["url"]
        new_md5,_ = get_page_md5(site_url)
        if not new_md5:
            continue
        if site_url not in old_record:
            old_record[site_url] = new_md5
            continue
        if old_record[site_url] != new_md5:
            send_feishu(site_name,site_url)
            old_record[site_url] = new_md5

    with open("record.txt","w",encoding="utf-8") as f:
        f.write(str(old_record))

if __name__ == "__main__":
    main()
