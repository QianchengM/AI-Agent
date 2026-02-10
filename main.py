import sys
from colorama import init, Fore, Style
from dotenv import load_dotenv
from app.agents.fund_manager import create_fund_manager

# 1. 初始化颜色库
init(autoreset=True)
# 2. 加载环境变量 (.env)
load_dotenv()

def main():
    print(Fore.CYAN + "\n==========================================")
    print(Fore.CYAN + "🤖 DeFi 智能理财顾问 (LangChain v1.0)")
    print(Fore.CYAN + "==========================================")
    
    try:
        # 3. 初始化 Agent
        print(Fore.YELLOW + "⏳ 连接区块链...")
        agent = create_fund_manager()
        
        print(Fore.GREEN + "\n✅ 系统就绪！")
        print(Fore.WHITE + "你可以对我说：'把 0.0001 WETH 存入 Aave' 或 '帮我理财'")
        print(Style.DIM + "--------------------------------------------------")

        # 4. 进入对话循环
        while True:
            # 获取用户输入
            user_input = input(Fore.YELLOW + "\n👤 你: ")
            
            # 处理退出指令
            if user_input.lower() in ['q', 'exit', 'quit', '退出']:
                print(Fore.CYAN + "再见！停止运行。")
                break

            # 防止空输入
            if not user_input.strip():
                continue

            print(Fore.MAGENTA + "🤖 Agent 正在思考...", end="\r")
            
            # ---  LangChain 接管 ---
            # run() 方法自动分析决定是用工具还是只聊天
            try:
                result = agent.invoke({"input": user_input})
                response = result["output"]
                print(Fore.CYAN + f"🤖 Agent: {response}")
            except Exception as e:
                print(Fore.RED + f"❌ 执行过程中出错: {e}")

    except Exception as e:
        print(Fore.RED + f"❌ 系统启动失败: {e}")
        print(Fore.RED + "提示：请检查 .env 文件配置或网络连接。")

if __name__ == "__main__":
    main()