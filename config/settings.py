# config/settings.py
# config/settings.py
MY_ADDRESS = "0xF467257a991351317A76ed5a115f7fAD525231f4"  

# 2. 网络配置 (Sepolia)
SEPOLIA_CHAIN_ID = 11155111

# 3. 合约地址 
WETH_ADDRESS = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"
AAVE_POOL_ADDRESS = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"

# 4. ABI 定义 
# config/settings.py (找到 WETH_ABI 并替换)

WETH_ABI = [
    # 1. 存 ETH 换 WETH
    {
        "constant": False, "inputs": [], "name": "deposit",
        "outputs": [], "payable": True, "stateMutability": "payable", "type": "function"
    },
    # 2. 新增：授权函数 (Approve)
    {
        "constant": False,
        "inputs": [
            {"name": "guy", "type": "address"},
            {"name": "wad", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

AAVE_ABI = [{
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