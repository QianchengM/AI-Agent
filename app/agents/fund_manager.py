import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

# 导入所有工具
from app.tools.aave_tool import deposit_weth_to_aave
from app.tools.balance_tool import get_balance
from app.tools.swap_tool import swap_eth_to_weth
from app.tools.market_tool import get_token_price
from app.tools.approve_tool import approve_weth_to_aave
from app.tools.news_tool import get_crypto_news
from app.tools.rag_tool import query_knowledge_base

import warnings
# 屏蔽 Pydantic 底层无害的序列化警告，让控制台保持清爽
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# ==========================================
# 1. 定义多 Agent 共享的状态 (记忆)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# ==========================================
# 2. 初始化 LLM 与 子 Agent
# ==========================================
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))


# 👱‍♂️ 市场分析师 (查新闻 + 读研报)
analyst_tools = [get_token_price, get_crypto_news, query_knowledge_base]
analyst_agent = create_agent(
    model=llm, 
    tools=analyst_tools, 
    system_prompt="你是顶级的加密市场分析师。你可以查询实时新闻。在解答深度问题时，请务必先调用知识库 (query_knowledge_base) 检索 a16z 研报或 Uniswap 白皮书等专业资料。请用通俗易懂的语言，基于知识库的内容给出极其专业的分析。"
)
# 👷 交易执行官 (只负责干活)
executor_tools = [deposit_weth_to_aave, get_balance, swap_eth_to_weth, approve_weth_to_aave]
executor_agent = create_agent(
    model=llm, 
    tools=executor_tools, 
    system_prompt="""你是精准的交易执行官。你的唯一任务是调用工具执行区块链操作。
    【业务纪律】：在向 Aave 存款 (Deposit) 之前，必须先确认是否已经调用了授权 (Approve) 工具。
    
    ⚠️【最高指令】（生死攸关，前端系统极其脆弱）：
    1. 必须保留包装盒：工具返回的 JSON 包含了非常关键的 `{"type": "transaction", ...}` 外层结构！你必须【连同外层结构】一起完整输出！绝对禁止只提取内部的 to、data 字段！
    2. 严禁 Markdown排版：绝对禁止在 JSON 外面加 ```json 或 ``` 符号。
    3. 正确的输出格式范例：
       请先确认授权... {"type": "transaction", "tx_data": {"to": "...", "data": "...", "value": "..."}}
    4. 🛑 防冲突：一次回复只允许输出一个完整 JSON。如果需要先授权，请只输出 Approve 的 JSON，并提示用户等待上链。"""
)
# ==========================================
# 3. 定义节点逻辑 (封装子 Agent)
# ==========================================
def analyst_node(state: AgentState):
    print(" [经理路由] 任务交给了 ->  市场分析师")
    result = analyst_agent.invoke({"messages": state["messages"]})
    # 在回复前加上身份标签
    msg = AIMessage(content=f"【市场分析师】: {result['messages'][-1].content}")
    return {"messages": [msg]}

def executor_node(state: AgentState):
    print(" [经理路由] 任务交给了 ->  交易执行官")
    result = executor_agent.invoke({"messages": state["messages"]})
    msg = AIMessage(content=f"【交易执行官】: {result['messages'][-1].content}")
    return {"messages": [msg]}

# ==========================================
# 4. 定义大堂经理 (Supervisor 路由判断)
# ==========================================
class Router(BaseModel):
    next_agent: Literal["analyst", "executor", "FINISH"] = Field(
        description="决定下一个任务的角色：查行情、看新闻、查询知识库、解释DeFi专业概念请选 analyst；查余额、授权、转账请选 executor；如果是打招呼等纯日常寒暄，选 FINISH。"
    )

def supervisor_node(state: AgentState):
    print("🧠 [大堂经理] 正在思考该安排谁...")
    prompt = f"""你是一个 DeFi 系统的总管经理。负责将任务分配给【市场分析师(analyst)】或【交易执行官(executor)】，或选择结束(FINISH)。
    
    ⚠️【绝对不容违背的防死机铁律】（违反将导致服务器崩溃）：
    1. 🛑【Web3 强制中断】：只要对话的最后一条消息包含 `{{"type": "transaction"` 或 `tx_data`，代表已唤起钱包，你必须无条件立刻选择 FINISH！
    2. 🛑【禁止同部门无限返工】（防死循环核心）：如果对话的最后一条消息是【市场分析师】发出的（无论他回答得好不好），你【绝对禁止】再次将任务派发给 analyst！同理，如果最后一条是【交易执行官】发出的，绝对禁止再派给 executor！
    3. ⚖️【任务流转与结束】：
       - 如果用户只要求查信息，且 analyst 已回复，立刻选 FINISH。
       - 如果用户只要求操作链上，且 executor 已回复（如余额），立刻选 FINISH。
       - 只有当用户明确要求“先查信息，后操作钱包”时，你才可以在 analyst 回复后，将任务接力传给 executor。
    4. 🕰️【无视历史】：只针对用户的最新指令做出判断，忽略之前回合留下的 JSON 或总结。
    
    当前对话记录: {state['messages']}"""
    
    router_llm = llm.with_structured_output(Router)
    decision = router_llm.invoke(prompt)
    return {"next_agent": decision.next_agent}
# ==========================================
# 5. 构建 LangGraph 工作流
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("executor", executor_node)

workflow.add_edge(START, "supervisor")

# 经理决定流程走向
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_agent"],
    {
        "analyst": "analyst",
        "executor": "executor",
        "FINISH": END
    }
)

# 子 Agent 干完活后，必须向经理汇报
workflow.add_edge("analyst", "supervisor")
workflow.add_edge("executor", "supervisor")

# 添加记忆持久化（确保它能记住之前的对话）
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

# ==========================================
# 6. 兼容现有 server.py 的包装器 (增强版)
# ==========================================
class MultiAgentWrapper:
    def invoke(self, inputs):
        user_input = inputs["input"]
        config = {"configurable": {"thread_id": "user_1"}} # 设定用户记忆 ID
        
        # 使用 stream() 替代 invoke()，这样我们能捕获每一个子 Agent 的工作成果
        final_responses = []
        
        # 遍历整个图的执行流
        for event in app_graph.stream({"messages": [HumanMessage(content=user_input)]}, config=config):
            for node_name, node_state in event.items():
                # 只要是分析师或执行官的汇报，我们就记录下来
                if node_name in ["analyst", "executor"]:
                    latest_msg = node_state["messages"][-1].content
                    final_responses.append(latest_msg)
        
        # 把所有 Agent 的汇报用换行符拼合在一起
        if final_responses:
            combined_output = "\n\n".join(final_responses)
        else:
            # 如果没有触发任何子 Agent（直接走到了 FINISH）
            result = app_graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
            last_msg = result["messages"][-1]
            
            # 防复读机机制：如果最后一条还是用户自己的话，说明 AI 没说话
            if isinstance(last_msg, HumanMessage):
                combined_output = "【大堂经理】：您好！我是 DeFi 智能理财管家。我可以帮您解答专业知识（如Uniswap/Aave机制）、查询行情、或者执行链上交易。请问有什么可以帮您？"
            else:
                combined_output = last_msg.content
            
        return {"output": combined_output}

def create_fund_manager():
    print("🚀 正在启动多智能体系统 (Manager -> Analyst & Executor)...")
    return MultiAgentWrapper()