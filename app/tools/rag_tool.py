import os
from pathlib import Path
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader

# 1. 动态获取绝对路径，防止路径报错
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "chroma_db"

print("📚 [系统] 正在初始化本地 RAG 知识库...")
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

# 2. 检查是否已经存在数据库，避免每次重启重复扣费和等待
if not DB_DIR.exists():
    print(f"📖 [系统] 首次运行，正在读取 {DOCS_DIR} 下的 PDF 文件...")
    # 自动加载 docs 文件夹下的所有 PDF
    loader = PyPDFDirectoryLoader(str(DOCS_DIR))
    docs = loader.load()
    print(f"✅ [系统] 成功读取了 {len(docs)} 页 PDF，正在切分并存入数据库...")
    
    # 因为研报很长，我们把区块大小调大一点
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)
    
    # 创建并永久保存在本地
    vectorstore = Chroma.from_documents(
        documents=split_docs, 
        embedding=embeddings,
        persist_directory=str(DB_DIR)
    )
    print("✅ [系统] 向量数据库构建并保存成功！")
else:
    print("⚡ [系统] 检测到本地已有向量数据库，极速加载中...")
    vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)

# 每次检索最相关的前 3 个段落
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

@tool
def query_knowledge_base(query: str) -> str:
    """
    查询专业的加密货币研报、DeFi 白皮书（如 Uniswap）和宏观分析框架。
    当用户问到具体的协议机制（如集中流动性、无常损失）、宏观市场周期，或者需要极度专业的分析支撑时，必须调用此工具。
    """
    print(f"📖 [分析师] 正在翻阅顶级研报与白皮书检索: '{query}' ...")
    results = retriever.invoke(query)
    
    if not results:
        return "本地知识库中未找到相关专业资料。"
    
    # 拼接检索到的 PDF 内容片段
    return "\n\n".join([doc.page_content for doc in results])