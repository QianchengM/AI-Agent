import uvicorn
import os
from pathlib import Path # 👈 引入这个神器
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.agents.fund_manager import create_fund_manager

# 1. 初始化 FastAPI
app = FastAPI()

# 2. 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🛠️ 关键修复：锁定绝对路径 ---
# 获取 server.py 当前所在的文件夹路径 (例如 C:\Users\...\Crypto_Advisor_Core)
BASE_DIR = Path(__file__).resolve().parent

# 检查一下文件夹到底在不在 (调试用)
css_path = BASE_DIR / "css"
print(f"📂 正在寻找 CSS 路径: {css_path}")
print(f"👀 是否存在? {css_path.exists()}")

# 3. 初始化 Web3 Agent
print("🚀 正在启动 Agent，请稍候...")
# 注意：这里我们只初始化一次，避免每次请求都重新连接区块链
agent_executor = create_fund_manager()
print("✅ Agent 就绪！")

# 4. 挂载静态文件 (使用绝对路径)
# 这样不管你在哪里运行 python 命令，它都能精准找到文件
app.mount("/css", StaticFiles(directory=str(BASE_DIR / "css")), name="css")
app.mount("/img", StaticFiles(directory=str(BASE_DIR / "img")), name="img")
app.mount("/plugins", StaticFiles(directory=str(BASE_DIR / "plugins")), name="plugins")

# --- 核心接口 ---

@app.get("/")
async def read_root():
    return FileResponse(BASE_DIR / 'index.html') # 这里也加上绝对路径

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if not messages:
            return {"answer": "尴尬了，没收到消息..."}

        user_input = messages[-1]['content']
        print(f"📩 收到指令: {user_input}")

        # 调用 Agent
        result = agent_executor.invoke({"input": user_input})
        ai_response = result["output"]

        return {"answer": ai_response}

    except Exception as e:
        print(f"❌ 报错: {e}")
        return {"answer": f"Agent Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)