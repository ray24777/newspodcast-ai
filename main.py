import feedparser
from datetime import datetime, timedelta
from openai import OpenAI
import os
import requests
from dateutil import parser

# 设置OpenAI API密钥
os.environ["OPENAI_API_KEY"] = "sk-Y1W03ED34Fo7QoSp9ZRQ70kpX8DpN4yO63qOsKo3B9kubkKZ"
os.environ["OPENAI_BASE_URL"] = "https://api.feidaapi.com/v1"
client = OpenAI()


# 获取RSS数据并过滤最近24小时新闻
def get_recent_news(rss_url, proxy=None):

    now = datetime.now()
    print("当前时间：", now)
    last_24_hours = now - timedelta(hours=24)
    recent_news = []
    
    if proxy is not None:
        print(f"使用代理：{proxy}") 
        # 使用代理获取RSS数据
        proxies = {
            "http": proxy,
            "https": proxy,
        }
        response = requests.get(rss_url, proxies=proxies)
    else:
        # 直接获取RSS数据
        response = requests.get(rss_url)
    response.raise_for_status()  # 检查请求是否成功
    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        published = parser.parse(entry.published) if 'published' in entry else None
        published = published.replace(tzinfo=None)
        if published and published > last_24_hours:
            recent_news.append({
                "title": entry.title,
                "link": entry.link,
                "published": published,
                "summary": entry.summary if "summary" in entry else "",
            })
    return recent_news

# 使用GPT-3.5生成单条新闻概要
def generate_summary(news_item):
    prompt = f"以下是一条新闻：\n标题: {news_item['title']}\n内容: {news_item['summary']}\n生成一段简洁的中文概要："
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=250,
    )

    return response.choices[0].message
# 汇总所有概要为要闻
def generate_headlines_summary(summaries):
    combined_summaries = "\n".join([f"- {summary}" for summary in summaries])
    prompt = f"以下是最近24小时的新闻概要：\n{combined_summaries}\n总结当天的新闻："
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500,
    )

    return response.choices[0].message

def save_to_md_file(recent_news, summaries, headlines_summary, filename="news_summary.md"):
    """将新闻概要和要闻保存为 Markdown 文件"""
    with open(filename, "w", encoding="utf-8") as md_file:
        md_file.write("# 汇总要闻\n\n")
        # replace '\n' with true newline
        headlines_summary.content = headlines_summary.content.replace("\\n", "\n")
        md_file.write(f"{headlines_summary.content}\n\n")

        md_file.write("# 最近24小时新闻概要\n\n")
        
        for i, news in enumerate(recent_news):
            md_file.write(f"## 新闻 {i+1}\n")
            md_file.write(f"- **标题**: [{news['title']}]({news['link']})\n")
            md_file.write(f"- **发布时间**: {news['published']}\n")
            md_file.write(f"- **概要**: {summaries[i]}\n\n")
        

def rssgpt(url,output_file='news_summary.md',proxy=None):
    # 获取最近24小时的新闻
    #recent_news = get_recent_news(RSS_URL,PROXY)
    recent_news = get_recent_news(url)
    if not recent_news:
        print("最近24小时没有新闻。")
        return
    
    summaries = []
    for news in recent_news:
        print(f"正在处理新闻: {news['title']}")
        summary = generate_summary(news).content
        summaries.append(summary)
        print(f"概要: {summary}\n")
    
    # 汇总要闻
    print("生成汇总要闻...")
    headlines_summary = generate_headlines_summary(summaries)

    save_to_md_file(recent_news, summaries, headlines_summary, output_file)
    print("要闻已保存到", output_file)


if __name__ == "__main__":
    # 输入RSS链接
    zaobao_url = "https://rsshub.rssforever.com/zaobao/realtime/china"
    paper_url = "https://feedx.net/rss/thepaper.xml"
    # 设置代理
    PROXY = "http://localhost:7892"

    #rssgpt(zaobao_url,"zaobao.md",PROXY)

    rssgpt(paper_url,"paper.md")


