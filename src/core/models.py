from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    """投资建议类型"""
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    stock_ticker: str = Field(..., description="股票代码", example="AAPL")
    query: str = Field(..., description="用户问题", example="这只股票值得投资吗？")


class AnalysisResponse(BaseModel):
    """分析响应模型"""
    stock_ticker: str
    query: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # 各代理分析结果
    financial_analysis: Optional[str] = None
    market_analysis: Optional[str] = None
    valuation_analysis: Optional[str] = None

    # 最终建议
    recommendation: Optional[str] = None
    score: Optional[float] = Field(None, ge=1, le=10, description="投资评分 1-10")
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    # 详细分析
    reasoning: Optional[str] = None
    risks: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None

    # 元数据
    execution_time: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""
    query: str = Field(..., description="查询问题")
    stock_ticker: Optional[str] = Field(None, description="股票代码（可选）")
    top_k: int = Field(5, ge=1, le=20, description="返回文档数量")


class RAGQueryResponse(BaseModel):
    """RAG 查询响应"""
    query: str
    documents: List[Dict[str, Any]]
    total_results: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    rag_initialized: bool
    vector_store_size: int