import json
import traceback
from langchain.tools import tool
from web3 import Web3
from app.utils.web3_client import Web3Client
from config import settings  # 👈 必须导入配置

@tool
def deposit_weth_to_aave(amount_str: str) -> str:
    """
    构造将 WETH 存入 Aave 的交易数据。
    """
    print(f"\n🔍 [DEBUG] 正在执行存钱工具... 金额: {amount_str}")
    
    try:
        # 1. 获取 Web3 实例
        w3 = Web3Client.get_instance()

        # 2. 清洗金额
        clean_amount = amount_str.lower().replace("weth", "").replace("eth", "").strip()
        amount_wei = w3.to_wei(clean_amount, "ether")
        print(f"✅ [DEBUG] 金额转换成功: {amount_wei} Wei")

        # 3. 获取配置中的地址 (Sepolia)
        AAVE_POOL = settings.AAVE_POOL_ADDRESS
        WETH_TOKEN = settings.WETH_ADDRESS
        USER_ADDRESS = settings.MY_ADDRESS 

        # 4. 最小化 ABI (Supply 函数)
        abi = [{
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address", "name": "onBehalfOf", "type": "address"},
                {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
            ],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]

        # 5. 构造交易数据 (兼容性修复)
        contract = w3.eth.contract(address=AAVE_POOL, abi=abi)
        
        print(f"✅ [DEBUG] 正在构建交易... 受益人: {USER_ADDRESS}")
        
        # 🛠️ 修复点：使用 build_transaction 替代 encodeABI
        # 这种方式在 web3.py 的所有版本中都可用
        # 我们填入假的 gas/nonce，因为这一步只是为了生成 'data' 字段给前端用
        tx = contract.functions.supply(
            WETH_TOKEN,       # asset
            amount_wei,       # amount
            USER_ADDRESS,     # onBehalfOf
            0                 # referralCode
        ).build_transaction({
            'from': USER_ADDRESS, 
            'gas': 500000,           # 估算值，仅仅为了通过 build 检查
            'gasPrice': w3.to_wei('1', 'gwei'), 
            'nonce': 0,              # 占位符
            'value': 0,
            'chainId': settings.SEPOLIA_CHAIN_ID
        })
        
        # 提取数据字段
        tx_data = tx['data']
        print(f"✅ [DEBUG] 交易数据生成成功! Length: {len(tx_data)}")

        # 6. 返回结果
        result = {
            "type": "transaction",
            "message": f"已准备好存入 {clean_amount} WETH 到 Aave，请在钱包确认。",
            "tx_data": {
                "to": AAVE_POOL,
                "data": tx_data,
                "value": "0x0"
            }
        }
        return json.dumps(result)

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"❌ [DEBUG] 严重错误:\n{error_msg}")
        return f"系统配置错误: {str(e)}"