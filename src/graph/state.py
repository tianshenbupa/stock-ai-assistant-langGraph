from typing import TypedDict, Annotated, List, Dict, Any
from operator import add
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Agent 状态定义

    使用 Annotated 来处理并行更新:
    - 普通类型: 只能被一个节点更新
    - Annotated[type, add]: 可以被多个节点累积更新
    """
    # ===== 输入参数 (不会被修改) =====
    stock_ticker: str
    query: str

    # ===== 消息历史 (累积更新) =====
    messages: Annotated[List[BaseMessage], add]

    # ===== 各代理的分析结果 (各自独立更新,不冲突) =====
    financial_analysis: str
    market_analysis: str
    valuation_analysis: str

    # ===== 上下文和数据 (各自独立) =====
    rag_context: str
    market_data: Dict[str, Any]
    valuation_data: Dict[str, Any]

    # ===== 最终结果 (只由 supervisor 更新) =====
    final_recommendation: Dict[str, Any]

    # ===== 控制流 =====
    next_agent: str
    iteration_count: int