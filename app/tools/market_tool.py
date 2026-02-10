import requests
from langchain.tools import tool

@tool
def get_token_price(symbol: str = "ethereum") -> str:
    """
    查询加密货币的实时市场价格 (美元)。
    参数 symbol 默认是 'ethereum'。也可以查 'bitcoin', 'aave' 等。
    """
    try:
        # 简单的 CoinGecko API 调用
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if symbol in data:
            price = data[symbol]['usd']
            return f"📈 {symbol} 当前价格: ${price}"
        else:
            return f"❌ 未查询到 {symbol} 的价格，请尝试使用全称 (如 ethereum 而不是 ETH)。"
            
    except Exception as e:
        return f"❌ 查价失败: 网络错误或 API 限制"