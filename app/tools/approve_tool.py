import json
import traceback
from langchain.tools import tool
from web3 import Web3
from app.utils.web3_client import Web3Client
from config import settings

@tool
def approve_weth_to_aave() -> str:
    """
    授权 Aave 协议使用我的 WETH。
    在执行存钱(deposit)之前，必须先执行一次这个工具。
    """
    try:
        w3 = Web3Client.get_instance()
        user_address = settings.MY_ADDRESS
        
        # WETH 合约
        weth_contract = w3.eth.contract(address=settings.WETH_ADDRESS, abi=settings.WETH_ABI)
        
        # 我们要授权给 Aave Pool，金额设大一点（无限授权），避免以后每次都要点
        # 10000 ETH 应该够用了
        max_amount = w3.to_wei(10000, 'ether')
        
        print(f"✅ [DEBUG] 正在构建授权交易...")

        # 构建 Approve 交易
        tx = weth_contract.functions.approve(
            settings.AAVE_POOL_ADDRESS,  # 授权给谁：Aave
            max_amount                   # 授权多少
        ).build_transaction({
            'from': user_address,
            'gas': 100000,
            'gasPrice': w3.to_wei('2', 'gwei'),
            'nonce': 0, 
            'value': 0,
            'chainId': settings.SEPOLIA_CHAIN_ID
        })
        
        result = {
            "type": "transaction",
            "message": "正在请求 WETH 授权 (Approve)，请在钱包确认。\n授权成功后，你才能进行存款操作。",
            "tx_data": {
                "to": settings.WETH_ADDRESS, # 注意：授权是发给 WETH 合约的
                "data": tx['data'],
                "value": "0x0"
            }
        }
        return json.dumps(result)

    except Exception as e:
        return f"授权构建失败: {str(e)}"