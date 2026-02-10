import os
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# --- 路径锁定 ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# 强制加载配置
load_dotenv(dotenv_path=env_path, override=True)

class Web3Client:
    _instance = None

    @classmethod
    def get_instance(cls):
        """单例模式：确保全局只有一个 Web3 连接"""
        if cls._instance is None:
            # 👇 修改点：这里改成读取通用的 RPC_URL
            rpc_url = os.getenv("RPC_URL")
            
            if not rpc_url:
                # 如果找不到，尝试读取旧名字作为兼容（防止你忘了改 .env）
                rpc_url = os.getenv("INFURA_URL") or os.getenv("ALCHEMY_RPC_URL")
            
            if not rpc_url:
                raise ValueError(f"❌ 未找到 RPC_URL！请检查 .env 文件中是否有 RPC_URL=... 配置")
            
            cls._instance = Web3(Web3.HTTPProvider(rpc_url))
            
            # 简单测试一下连接是否成功
            if not cls._instance.is_connected():
                raise ConnectionError("❌ 无法连接到区块链网络，请检查 RPC_URL 是否有效 (可能是 Alchemy Key 过期或网络问题)")
                
        return cls._instance

    @staticmethod
    def get_account():
        w3 = Web3Client.get_instance()
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("❌ 未找到 PRIVATE_KEY，请检查 .env 文件")
        return w3.eth.account.from_key(private_key)