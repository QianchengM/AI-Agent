import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from app.tools.aave_tool import deposit_weth_to_aave
from app.tools.balance_tool import get_balance
from app.tools.aave_tool import deposit_weth_to_aave
from app.tools.swap_tool import swap_eth_to_weth
from app.tools.market_tool import get_token_price
from app.tools.approve_tool import approve_weth_to_aave
# 加载环境变量
load_dotenv()

def create_fund_manager():
    """
    创建并初始化理财经理 Agent (使用 LangChain 新版架构)
    """
    print("⚙️  正在组装 Agent 大脑 (New Architecture)...")
    
    # 1. 定义大脑 (LLM)
    llm = ChatOpenAI(
        model="gpt-4", 
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 2. 装备工具包
    tools = [deposit_weth_to_aave]
    tools = [deposit_weth_to_aave, get_balance]
    tools = [deposit_weth_to_aave, get_balance, swap_eth_to_weth, get_token_price]
    tools = [
        deposit_weth_to_aave, 
        get_balance, 
        swap_eth_to_weth, 
        get_token_price,
        approve_weth_to_aave 
    ]
    # 3. 定义 Prompt (这是新版必须的)
    # 我们需要告诉 AI 它是谁，并预留好“记忆”和“思考”的位置
    prompt = ChatPromptTemplate.from_messages([
       ("system", "你是一个专业的 DeFi 理财顾问。如果工具返回了 JSON 格式的交易数据（包含 type: transaction），请原样输出该 JSON 字符串，不要对其进行总结或修改格式。对于普通文本，请用中文回答。"),
        MessagesPlaceholder(variable_name="chat_history"), # 这里放聊天记录
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"), # 这里放 AI 的思考过程
    ])

    # 4. 初始化记忆系统
    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )

    # 5. 组装 Agent (新方法)
    # create_tool_calling_agent 是目前最推荐的构建方式
    agent = create_tool_calling_agent(llm, tools, prompt)

    # 6. 创建执行器
    # AgentExecutor 负责运行 Agent 并管理工具调用
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # 依然开启思考过程
        memory=memory,
        handle_parsing_errors=True
    )

    return agent_executor