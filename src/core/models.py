from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


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
    target_price: Optional[Union[float, str]] = None  # 修改: 允许字符串
    stop_loss: Optional[Union[float, str]] = None  # 修改: 允许字符串

    # 详细分析
    reasoning: Optional[str] = None
    risks: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None

    # 元数据
    execution_time: Optional[float] = None

    # 添加价格解析验证器
    @field_validator('target_price', 'stop_loss', mode='before')
    @classmethod
    def parse_price(cls, v):
        """
        智能解析价格字符串

        支持的格式:
        - 纯数字: 280.5 -> 280.5
        - 带货币符号: $280 -> 280.0
        - 中文格式: 255美元 -> 255.0
        - 价格区间: 270-285美元 -> 277.5 (取平均值)
        - 无法解析: "无法确定" -> "无法确定"

        Args:
            v: 输入的价格值

        Returns:
            float 或 str: 解析后的数字,或原字符串
        """
        if v is None:
            return None

        # 如果已经是数字,直接返回
        if isinstance(v, (int, float)):
            return float(v)

        # 如果是字符串,尝试解析
        if isinstance(v, str):
            try:
                # 移除常见的货币符号、单位和空格
                cleaned = re.sub(
                    r'[美元$¥€£元人民币港币日元韩元USD HKD CNY JPY KRW\s]',
                    '',
                    v
                )

                # 查找所有数字(包括小数)
                numbers = re.findall(r'\d+\.?\d*', cleaned)

                if numbers:
                    # 如果有多个数字(如价格区间"270-285"),取平均值
                    nums = [float(n) for n in numbers]
                    result = sum(nums) / len(nums)
                    return round(result, 2)

                # 如果找不到任何数字,返回原字符串
                # 这样可以保留类似"无法确定"、"暂无目标价"等描述性文本
                return v

            except Exception as e:
                # 解析出错,返回原字符串
                return v

        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # 允许额外字段,提高兼容性
        extra = "allow"


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