from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# 初始化免费的无头搜索引擎
search = DuckDuckGoSearchRun()

@tool
def get_crypto_news(query: str) -> str:
    """
    获取加密货币相关的最新市场行情、新闻和情绪分析。
    输入搜索关键词，返回互联网上的真实最新数据。
    """
    print(f"📰 [分析师] 正在连接互联网全网检索: '{query}' ...")
    try:
        # 为了提高搜索准确度，自动在用户关键词后加上 crypto news
        search_query = f"{query} 最新 行情 新闻"
        results = search.run(search_query)
        
        # 限制返回长度，防止把大语言模型的上下文撑爆
        if len(results) > 1500:
            results = results[:1500] + "...(截断)"
            
        return results
    except Exception as e:
        return f"互联网检索暂时失败，请重试。错误信息: {str(e)}"