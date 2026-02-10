from langchain.tools import tool
from app.utils.web3_client import Web3Client
from config import settings

@tool
def get_balance() -> str:
    """
    查询当前连接钱包的 ETH 余额。
    不需要任何参数。
    """
    try:
        # 1. 获取连接
        w3 = Web3Client.get_instance()
        my_address = settings.MY_ADDRESS
        
        # 2. 查询链上余额
        # 'latest' 表示查询最新区块的状态
        balance_wei = w3.eth.get_balance(my_address, 'latest')
        
        # 3. 转换单位 (Wei -> ETH)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        # 4. 格式化输出 (保留 5 位小数)
        return f"💰 当前余额: {balance_eth:.5f} ETH (地址: {my_address})"

    except Exception as e:
        return f"❌ 查询余额失败: {str(e)}"