from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys
import time
from datetime import datetime

from config.settings import settings
from src.core.models import (
    AnalysisRequest,
    AnalysisResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    HealthResponse
)
from src.rag.retriever import rag_retriever
from src.graph.workflow import investment_workflow
from src.graph.state import AgentState

# ========== 配置日志 ==========
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)



# ========== 生命周期管理 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    logger.info("=" * 50)
    logger.info("🚀 股票投资 AI 助手（LangGraph 版本）启动中...")
    logger.info("=" * 50)

    # 启动时初始化 RAG 系统
    try:
        logger.info("📚 初始化 RAG 系统...")
        rag_retriever.initialize()
        logger.info(f"✅ RAG 系统初始化完成，向量库大小: {rag_retriever.collection_size}")

        # ===== 🆕 添加文档加载逻辑 =====
        if rag_retriever.collection_size == 0:
            logger.info("📄 向量库为空，开始加载财报文档...")

            from pathlib import Path
            from src.rag.loader import FinancialReportLoader

            # 检查 PDF 目录
            pdf_dir = Path(settings.PDF_DIRECTORY)
            pdf_files = list(pdf_dir.glob("**/*.pdf"))

            if pdf_files:
                logger.info(f"📁 发现 {len(pdf_files)} 个 PDF 文件:")
                for pdf_file in pdf_files:
                    logger.info(f"   - {pdf_file.name}")

                # 加载文档
                loader = FinancialReportLoader()
                documents = loader.load_documents()

                if documents:
                    # 添加到向量库
                    logger.info(f"📥 添加 {len(documents)} 个文档块到向量库...")
                    rag_retriever.add_documents(documents)

                    logger.info(f"✅ 文档加载完成! 向量库大小: {rag_retriever.collection_size}")
                else:
                    logger.warning("⚠️  文档加载失败，向量库仍为空")
            else:
                logger.warning(f"⚠️  未找到 PDF 文件")
                logger.info(f"💡 提示: 请将财报 PDF 放入 {pdf_dir.absolute()}")
        else:
            logger.info(f"📚 向量库已包含 {rag_retriever.collection_size} 个文档块，跳过加载")
        # ===== 结束新增代码 =====

    except Exception as e:
        logger.error(f"❌ RAG 初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("✅ 应用启动完成")
    logger.info("=" * 50)

    yield

    # 关闭时的清理工作
    logger.info("👋 应用正在关闭...")

# ========== 创建 FastAPI 应用 ==========
app = FastAPI(
    title="股票投资 AI 助手",
    description="基于 LangGraph 和 DeepSeek 的多代理股票分析系统",
    version="1.0.0",
    lifespan=lifespan
)

# ========== CORS 中间件 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== API 路由 ==========

@app.get("/", tags=["Root"])
async def root():
    """根路由 - 欢迎页面"""
    return {
        "message": "🚀 欢迎使用股票投资 AI 助手",
        "version": "1.0.0",
        "framework": "LangGraph + DeepSeek",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        rag_initialized=rag_retriever.is_initialized,
        vector_store_size=rag_retriever.collection_size
    )


@app.post("/api/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_stock(request: AnalysisRequest):
    """
    完整的股票分析 - 执行所有代理

    工作流程:
    1. 财务分析代理 (并行)
    2. 市场分析代理 (并行)
    3. 估值专家代理 (并行)
    4. 主管理代理 (综合)
    """
    start_time = time.time()
    logger.info(f"📊 开始分析股票: {request.stock_ticker}")

    try:
        # 初始化状态
        initial_state: AgentState = {
            "stock_ticker": request.stock_ticker,
            "query": request.query,
            "messages": [],
            "financial_analysis": "",
            "market_analysis": "",
            "valuation_analysis": "",
            "rag_context": "",
            "market_data": {},
            "valuation_data": {},
            "final_recommendation": {},
            "next_agent": "",
            "iteration_count": 0
        }

        # 执行工作流
        logger.info("🔄 执行 LangGraph 工作流...")
        result = investment_workflow.invoke(initial_state)

        # 提取最终建议
        final_rec = result.get("final_recommendation", {})

        # 构建响应
        execution_time = time.time() - start_time
        response = AnalysisResponse(
            stock_ticker=request.stock_ticker,
            query=request.query,
            financial_analysis=result.get("financial_analysis"),
            market_analysis=result.get("market_analysis"),
            valuation_analysis=result.get("valuation_analysis"),
            recommendation=final_rec.get("recommendation"),
            score=final_rec.get("score"),
            target_price=final_rec.get("target_price"),
            stop_loss=final_rec.get("stop_loss"),
            reasoning=final_rec.get("reasoning"),
            risks=final_rec.get("risks"),
            opportunities=final_rec.get("opportunities"),
            execution_time=execution_time
        )

        logger.info(f"✅ 分析完成，耗时: {execution_time:.2f}秒")
        return response

    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/analyze/financial", tags=["Analysis"])
async def analyze_financial_only(stock_ticker: str, query: str):
    """仅执行财务分析"""
    from src.graph.nodes import financial_agent_node

    try:
        state: AgentState = {
            "stock_ticker": stock_ticker,
            "query": query,
            "messages": [],
            "financial_analysis": "",
            "market_analysis": "",
            "valuation_analysis": "",
            "rag_context": "",
            "market_data": {},
            "valuation_data": {},
            "final_recommendation": {},
            "next_agent": "",
            "iteration_count": 0
        }

        result = financial_agent_node(state)
        return {
            "stock_ticker": stock_ticker,
            "analysis": result["financial_analysis"],
            "rag_context": result.get("rag_context", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/market", tags=["Analysis"])
async def analyze_market_only(stock_ticker: str, query: str):
    """仅执行市场分析"""
    from src.graph.nodes import market_agent_node

    try:
        state: AgentState = {
            "stock_ticker": stock_ticker,
            "query": query,
            "messages": [],
            "financial_analysis": "",
            "market_analysis": "",
            "valuation_analysis": "",
            "rag_context": "",
            "market_data": {},
            "valuation_data": {},
            "final_recommendation": {},
            "next_agent": "",
            "iteration_count": 0
        }

        result = market_agent_node(state)
        return {
            "stock_ticker": stock_ticker,
            "analysis": result["market_analysis"],
            "market_data": result.get("market_data", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/valuation", tags=["Analysis"])
async def analyze_valuation_only(stock_ticker: str, query: str):
    """仅执行估值分析"""
    from src.graph.nodes import valuation_agent_node

    try:
        state: AgentState = {
            "stock_ticker": stock_ticker,
            "query": query,
            "messages": [],
            "financial_analysis": "",
            "market_analysis": "",
            "valuation_analysis": "",
            "rag_context": "",
            "market_data": {},
            "valuation_data": {},
            "final_recommendation": {},
            "next_agent": "",
            "iteration_count": 0
        }

        result = valuation_agent_node(state)
        return {
            "stock_ticker": stock_ticker,
            "analysis": result["valuation_analysis"],
            "valuation_data": result.get("valuation_data", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
async def query_rag(request: RAGQueryRequest):
    """查询 RAG 系统"""
    try:
        if not rag_retriever.is_initialized:
            raise HTTPException(status_code=503, detail="RAG 系统未初始化")

        results = rag_retriever.query(
            query=request.query,
            top_k=request.top_k,
            stock_ticker=request.stock_ticker
        )

        return RAGQueryResponse(
            query=request.query,
            documents=results,
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/initialize", tags=["RAG"])
async def initialize_rag(force_reload: bool = False):
    """初始化或重新加载 RAG 系统"""
    try:
        rag_retriever.initialize(force_reload=force_reload)
        return {
            "status": "success",
            "message": "RAG 系统初始化完成",
            "vector_store_size": rag_retriever.collection_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/info", tags=["Info"])
async def get_info():
    """获取应用信息"""
    return {
        "name": "股票投资 AI 助手",
        "version": "1.0.0",
        "framework": "LangGraph",
        "llm": "DeepSeek",
        "features": [
            "多代理协作",
            "财报 RAG 检索",
            "并行任务执行",
            "状态持久化",
            "完整的 API 文档"
        ],
        "rag_status": {
            "initialized": rag_retriever.is_initialized,
            "vector_store_size": rag_retriever.collection_size
        }
    }


# ========== 启动应用 ==========
if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 50)
    print(f"🚀 服务启动: http://localhost:{settings.PORT}")
    print(f"📚 API文档: http://localhost:{settings.PORT}/docs")
    print("=" * 50 + "\n")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )