from typing import Dict, Any
from loguru import logger
from src.tools.financial import get_financial_data
from src.tools.market import get_market_data
from src.tools.valuation import calculate_valuation
from src.core.llm import get_llm
from .state import AgentState


def financial_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    财务分析代理节点

    只返回: financial_analysis, rag_context
    """
    logger.info("🏦 执行财务分析代理...")

    stock_ticker = state["stock_ticker"]
    query = state["query"]

    try:
        # 获取财务数据和 RAG 上下文
        financial_data = get_financial_data(stock_ticker, query)

        # 调用 LLM 进行分析
        llm = get_llm()

        prompt = f"""
        你是一位资深的财务分析师。请基于以下财务数据对 {stock_ticker} 进行深入分析:

        查询: {query}

        财务数据:
        {financial_data.get('data', '未获取到数据')}

        财报上下文:
        {financial_data.get('rag_context', '未找到相关财报')}

        请从以下角度进行分析:
        1. 收入和盈利能力
        2. 财务健康状况
        3. 现金流状况
        4. 关键财务比率
        5. 同比和环比趋势

        请提供详细、专业的分析。
        """

        analysis = llm.invoke(prompt).content

        logger.info("✅ 财务分析完成")

        # ⚠️ 只返回本节点负责的字段
        return {
            "financial_analysis": analysis,
            "rag_context": financial_data.get('rag_context', '')
        }

    except Exception as e:
        logger.error(f"❌ 财务分析失败: {e}")
        return {
            "financial_analysis": f"财务分析失败: {str(e)}",
            "rag_context": ""
        }


def market_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    市场分析代理节点

    只返回: market_analysis, market_data
    """
    logger.info("📈 执行市场分析代理...")

    stock_ticker = state["stock_ticker"]
    query = state["query"]

    try:
        # 获取市场数据
        market_data = get_market_data(stock_ticker)

        # 调用 LLM 进行分析
        llm = get_llm()

        prompt = f"""
        你是一位资深的市场分析师。请基于以下市场数据对 {stock_ticker} 进行分析:

        查询: {query}

        市场数据:
        {market_data}

        请从以下角度进行分析:
        1. 股价走势和技术指标
        2. 市场情绪和投资者行为
        3. 行业趋势和竞争格局
        4. 近期新闻和事件影响

        请提供详细、专业的分析。
        """

        analysis = llm.invoke(prompt).content

        logger.info("✅ 市场分析完成")

        # ⚠️ 只返回本节点负责的字段
        return {
            "market_analysis": analysis,
            "market_data": market_data
        }

    except Exception as e:
        logger.error(f"❌ 市场分析失败: {e}")
        return {
            "market_analysis": f"市场分析失败: {str(e)}",
            "market_data": {}
        }


def valuation_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    估值专家代理节点

    只返回: valuation_analysis, valuation_data
    """
    logger.info("💎 执行估值分析代理...")

    stock_ticker = state["stock_ticker"]
    query = state["query"]

    try:
        # 计算估值
        valuation_data = calculate_valuation(stock_ticker)

        # 调用 LLM 进行分析
        llm = get_llm()

        prompt = f"""
        你是一位资深的估值专家。请基于以下估值数据对 {stock_ticker} 进行分析:

        查询: {query}

        估值数据:
        {valuation_data}

        请从以下角度进行分析:
        1. 相对估值 (P/E, P/B, P/S 等)
        2. 绝对估值 (DCF, DDM 等)
        3. 与行业平均的对比
        4. 历史估值水平对比
        5. 内在价值评估

        请提供详细、专业的分析。
        """

        analysis = llm.invoke(prompt).content

        logger.info("✅ 估值分析完成")

        # ⚠️ 只返回本节点负责的字段
        return {
            "valuation_analysis": analysis,
            "valuation_data": valuation_data
        }

    except Exception as e:
        logger.error(f"❌ 估值分析失败: {e}")
        return {
            "valuation_analysis": f"估值分析失败: {str(e)}",
            "valuation_data": {}
        }


def supervisor_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    主管理代理节点 - 综合所有分析结果

    只返回: final_recommendation
    """
    logger.info("👔 执行主管理代理...")

    stock_ticker = state["stock_ticker"]
    query = state["query"]
    financial_analysis = state.get("financial_analysis", "")
    market_analysis = state.get("market_analysis", "")
    valuation_analysis = state.get("valuation_analysis", "")

    try:
        # 调用 LLM 综合分析
        llm = get_llm()

        prompt = f"""
        你是一位资深的投资顾问。请综合以下三位专家的分析,为 {stock_ticker} 提供最终投资建议:

        用户问题: {query}

        【财务分析师的观点】
        {financial_analysis}

        【市场分析师的观点】
        {market_analysis}

        【估值专家的观点】
        {valuation_analysis}

        请提供一个结构化的投资建议,包括:
        1. 综合评分 (1-10分,10分最高)
        2. 投资建议 (强烈买入/买入/持有/卖出/强烈卖出)
        3. 目标价格区间
        4. 止损价格
        5. 详细推理过程
        6. 主要风险因素 (3-5个)
        7. 主要投资机会 (3-5个)

        请以 JSON 格式返回,格式如下:
        {{
            "score": 8,
            "recommendation": "买入",
            "target_price": 180.5,
            "stop_loss": 150.0,
            "reasoning": "详细推理...",
            "risks": ["风险1", "风险2", "风险3"],
            "opportunities": ["机会1", "机会2", "机会3"]
        }}
        """

        response = llm.invoke(prompt).content

        # 尝试解析 JSON
        import json
        import re

        # 提取 JSON 部分
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            recommendation = json.loads(json_match.group())
        else:
            # 如果无法解析,返回默认结构
            recommendation = {
                "score": 5,
                "recommendation": "持有",
                "target_price": None,
                "stop_loss": None,
                "reasoning": response,
                "risks": ["数据解析失败"],
                "opportunities": []
            }

        logger.info("✅ 主管理代理分析完成")

        # ⚠️ 只返回本节点负责的字段
        return {
            "final_recommendation": recommendation
        }

    except Exception as e:
        logger.error(f"❌ 主管理代理分析失败: {e}")
        return {
            "final_recommendation": {
                "score": 5,
                "recommendation": "持有",
                "reasoning": f"分析失败: {str(e)}",
                "risks": ["分析失败"],
                "opportunities": []
            }
        }