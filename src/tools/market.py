"""
全球股票市场数据工具 - 使用 yfinance
"""
import yfinance as yf
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime, timedelta
import pandas as pd


def get_market_data(stock_ticker: str) -> Dict[str, Any]:
    """
    获取实时市场数据

    Args:
        stock_ticker: 股票代码

    Returns:
        市场数据字典
    """
    try:
        logger.info(f"📈 获取 {stock_ticker} 的市场数据")

        stock = yf.Ticker(stock_ticker)
        info = stock.info

        # 获取最新价格
        hist = stock.history(period="1d")

        if hist.empty:
            return {"error": "无法获取市场数据", "success": False}

        latest = hist.iloc[-1]

        result = {
            "stock_ticker": stock_ticker,
            "stock_name": info.get('longName', info.get('shortName', '')),
            "current_price": round(float(latest['Close']), 2),
            "open": round(float(latest['Open']), 2),
            "high": round(float(latest['High']), 2),
            "low": round(float(latest['Low']), 2),
            "volume": int(latest['Volume']),
            "change_amount": round(float(latest['Close'] - info.get('previousClose', latest['Close'])), 2),
            "change_percent": round(float(info.get('regularMarketChangePercent', 0)), 2),
            "previous_close": round(float(info.get('previousClose', 0)), 2),
            "market_cap": info.get('marketCap', 0),
            "52week_high": round(float(info.get('fiftyTwoWeekHigh', 0)), 2),
            "52week_low": round(float(info.get('fiftyTwoWeekLow', 0)), 2),
            "avg_volume": info.get('averageVolume', 0),
            "currency": info.get('currency', 'USD'),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

        logger.info(f"✅ 市场数据获取成功: {result['stock_name']} - {result['currency']}{result['current_price']}")
        return result

    except Exception as e:
        logger.error(f"❌ 获取市场数据失败: {e}")
        return {
            "stock_ticker": stock_ticker,
            "error": str(e),
            "success": False
        }


def get_historical_data(stock_ticker: str, period: str = "1y",
                        start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    获取历史行情数据

    Args:
        stock_ticker: 股票代码
        period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        start_date: 开始日期 (YYYY-MM-DD, 可选)
        end_date: 结束日期 (YYYY-MM-DD, 可选)

    Returns:
        历史数据字典
    """
    try:
        logger.info(f"📊 获取 {stock_ticker} 的历史数据")

        stock = yf.Ticker(stock_ticker)

        if start_date and end_date:
            hist = stock.history(start=start_date, end=end_date)
        else:
            hist = stock.history(period=period)

        if hist.empty:
            return {"error": "无历史数据", "success": False}

        # 转换为字典列表
        history = []
        for date, row in hist.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })

        result = {
            "stock_ticker": stock_ticker,
            "period": period,
            "start_date": start_date or history[0]['date'],
            "end_date": end_date or history[-1]['date'],
            "data_count": len(history),
            "history": history,
            "success": True
        }

        logger.info(f"✅ 历史数据获取成功,共 {len(history)} 条记录")
        return result

    except Exception as e:
        logger.error(f"❌ 获取历史数据失败: {e}")
        return {
            "stock_ticker": stock_ticker,
            "error": str(e),
            "success": False
        }


def get_technical_indicators(stock_ticker: str) -> Dict[str, Any]:
    """
    获取技术指标数据

    Args:
        stock_ticker: 股票代码

    Returns:
        技术指标字典
    """
    try:
        logger.info(f"📉 获取 {stock_ticker} 的技术指标")

        stock = yf.Ticker(stock_ticker)
        hist = stock.history(period="3mo")

        if hist.empty:
            return {"error": "无数据计算技术指标", "success": False}

        close_prices = hist['Close']

        # 计算移动平均线
        indicators = {}

        if len(close_prices) >= 5:
            indicators['MA5'] = round(float(close_prices.tail(5).mean()), 2)
        if len(close_prices) >= 10:
            indicators['MA10'] = round(float(close_prices.tail(10).mean()), 2)
        if len(close_prices) >= 20:
            indicators['MA20'] = round(float(close_prices.tail(20).mean()), 2)
        if len(close_prices) >= 50:
            indicators['MA50'] = round(float(close_prices.tail(50).mean()), 2)

        # 当前价格
        current_price = round(float(close_prices.iloc[-1]), 2)
        indicators['current_price'] = current_price

        # 价格趋势判断
        if 'MA5' in indicators and 'MA20' in indicators:
            if indicators['MA5'] > indicators['MA20']:
                indicators['trend'] = "上涨趋势"
                indicators['trend_en'] = "Uptrend"
            else:
                indicators['trend'] = "下跌趋势"
                indicators['trend_en'] = "Downtrend"

        result = {
            "stock_ticker": stock_ticker,
            "indicators": indicators,
            "calculation_date": datetime.now().strftime("%Y-%m-%d"),
            "success": True
        }

        logger.info(f"✅ 技术指标计算完成")
        return result

    except Exception as e:
        logger.error(f"❌ 获取技术指标失败: {e}")
        return {
            "stock_ticker": stock_ticker,
            "error": str(e),
            "success": False
        }


def get_industry_info(stock_ticker: str) -> Dict[str, Any]:
    """
    获取行业信息

    Args:
        stock_ticker: 股票代码

    Returns:
        行业信息字典
    """
    try:
        logger.info(f"🏭 获取 {stock_ticker} 的行业信息")

        stock = yf.Ticker(stock_ticker)
        info = stock.info

        result = {
            "stock_ticker": stock_ticker,
            "company_name": info.get('longName', ''),
            "industry": info.get('industry', ''),
            "sector": info.get('sector', ''),
            "country": info.get('country', ''),
            "website": info.get('website', ''),
            "exchange": info.get('exchange', ''),
            "listing_date": info.get('firstTradeDateEpochUtc', ''),
            "employees": info.get('fullTimeEmployees', 0),
            "success": True
        }

        logger.info(f"✅ 行业信息获取成功: {result['industry']}")
        return result

    except Exception as e:
        logger.error(f"❌ 获取行业信息失败: {e}")
        return {
            "stock_ticker": stock_ticker,
            "error": str(e),
            "success": False
        }