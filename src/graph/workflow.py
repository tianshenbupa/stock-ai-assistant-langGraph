from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes import (
    financial_agent_node,
    market_agent_node,
    valuation_agent_node,
    supervisor_agent_node
)
from loguru import logger


def create_investment_workflow():
    """
    创建投资分析工作流

    Returns:
        编译后的 LangGraph 工作流
    """
    logger.info("🔨 构建 LangGraph 工作流...")

    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("financial_agent", financial_agent_node)
    workflow.add_node("market_agent", market_agent_node)
    workflow.add_node("valuation_agent", valuation_agent_node)
    workflow.add_node("supervisor", supervisor_agent_node)

    # 设置入口点 - 三个专家代理并行执行
    workflow.set_entry_point("financial_agent")

    # 定义边（执行流程）
    # 财务分析 → 主管理
    workflow.add_edge("financial_agent", "supervisor")

    # 市场分析 → 主管理
    workflow.add_edge("market_agent", "supervisor")

    # 估值分析 → 主管理
    workflow.add_edge("valuation_agent", "supervisor")

    # 主管理 → 结束
    workflow.add_edge("supervisor", END)

    # 并行执行财务、市场、估值三个代理
    # 注意：LangGraph 会自动处理并行执行
    workflow.set_entry_point("financial_agent")
    workflow.add_edge("financial_agent", "market_agent")
    workflow.add_edge("market_agent", "valuation_agent")

    # 编译工作流
    app = workflow.compile()

    logger.info("✅ LangGraph 工作流构建完成")
    return app


# 创建全局工作流实例
investment_workflow = create_investment_workflow()