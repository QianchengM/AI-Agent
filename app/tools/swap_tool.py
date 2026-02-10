import os
from langchain.tools import tool
from app.utils.web3_client import Web3Client
from config import settings

@tool
def swap_eth_to_weth(amount_str: str) -> str:
    """
    将 ETH 兑换为 WETH (Wrap Ether)。
    Aave 协议需要 WETH 才能存款，所以如果你只有 ETH，必须先调用此工具。
    参数 amount_str 是要兑换的金额，例如 "0.001"。
    """
    try:
        w3 = Web3Client.get_instance()
        account = Web3Client.get_account()
        
        amount_wei = w3.to_wei(amount_str, "ether")
        weth_contract = w3.eth.contract(address=settings.WETH_ADDRESS, abi=settings.WETH_ABI)
        
        # WETH 的存款很简单，就是直接转 ETH 进去
        nonce = w3.eth.get_transaction_count(settings.MY_ADDRESS)
        
        # 构建交易 (调用 WETH 合约的 deposit 方法，并附带 ETH value)
        # 注意：WETH 的 deposit 函数在 ABI 里可能没写名字，它通常是一个 receive/fallback 函数，
        # 但标准的 WETH9 也有 deposit()。为了稳妥，我们直接往合约地址转账即可（WETH 合约会自动 wrap）。
        # 不过，标准的 web3py 调用习惯是调用函数。只要你的 settings.py 里 WETH ABI 是对的。
        # 如果你的 ABI 里没有 deposit，我们可以直接构造一个普通转账，但 data 必须为空。
        
        # 这里我们假设用最通用的方法：调用 deposit()
        # 如果报错，说明 settings.py 的 ABI 需要检查一下有没有 deposit
        tx = weth_contract.functions.deposit().build_transaction({
            'from': settings.MY_ADDRESS,
            'value': amount_wei, # 这里附带你要换的 ETH
            'gas': 100000,
            'gasPrice': int(w3.eth.gas_price * 1.2),
            'nonce': nonce,
            'chainId': settings.SEPOLIA_CHAIN_ID
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, os.getenv("PRIVATE_KEY"))
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # 等待回执
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"🔄 兑换成功！\n已将 {amount_str} ETH 换为 WETH。\n交易哈希: {w3.to_hex(tx_hash)}"

    except Exception as e:
        return f"❌ 兑换失败: {str(e)}"