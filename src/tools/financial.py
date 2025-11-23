"""
全球股票财务数据工具 - 使用 yfinance
支持美股、港股、欧股等全球市场(不包括A股直接查询)
"""
import yfinance as yf
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime
import pandas as pd


def get_financial_data(stock_ticker: str, query: str = "") -> Dict[str, Any]:
    """
    获取全球股票财务数据

    Args:
        stock_ticker: 股票代码
            - 美股: AAPL, MSFT, TSLA, GOOGL, AMZN, NVDA
            - 港股: 0700.HK (腾讯), 9988.HK (阿里巴巴), 1810.HK (小米)
            - 欧股: NESN.SW (雀巢), SAP.DE (SAP)
            - 日本ADR: TM (丰田), SONY (索尼)
        query: 查询问题(可选)

    Returns:
        财务数据字典
    """
    try:
        logger.info(f"📊 获取 {stock_ticker} 的财务数据")

        # 创建股票对象
        stock = yf.Ticker(stock_ticker)

        # 获取财务数据
        real_data = _fetch_yfinance_data(stock, stock_ticker)

        return {
            "stock_ticker": stock_ticker,
            "real_time_data": real_data,
            "data_source": "Yahoo Finance",
            "timestamp": datetime.now().isoformat(),
            "success": True if real_data and "error" not in real_data else False
        }

    except Exception as e:
        logger.error(f"❌ 获取财务数据失败: {e}")
        return {
            "stock_ticker": stock_ticker,
            "error": str(e),
            "success": False
        }


def _fetch_yfinance_data(stock: yf.Ticker, ticker: str) -> Dict[str, Any]:
    """从 yfinance 获取完整财务数据"""
    try:
        financial_data = {}

        # 安全获取 info (可能超时)
        info = None
        try:
            logger.info(f"正在获取 {ticker} 的基本信息...")
            # 添加超时保护
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("获取 info 超时")

            # 设置20秒超时 (Linux/Mac)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(20)
                info = stock.info
                signal.alarm(0)  # 取消超时
            except:
                # Windows 不支持 signal.SIGALRM,直接尝试获取
                info = stock.info

        except Exception as e:
            logger.warning(f"⚠️ 无法获取 info: {e}")
            info = None

        # 1. 基本信息 (只有 info 可用时才处理)
        if info:
            try:
                financial_data['basic_info'] = {
                    '公司名称': info.get('longName', ''),
                    '行业': info.get('industry', ''),
                    '板块': info.get('sector', ''),
                    '国家': info.get('country', ''),
                    '货币': info.get('currency', 'USD'),
                    '交易所': info.get('exchange', ''),
                    '网站': info.get('website', ''),
                    '员工数': info.get('fullTimeEmployees', 0),
                    '简介': (info.get('longBusinessSummary', '')[:300] + '...') if info.get(
                        'longBusinessSummary') else '',
                }
                logger.info("✅ 基本信息获取成功")
            except Exception as e:
                logger.warning(f"⚠️ 获取基本信息失败: {e}")
        else:
            logger.info("⏭️ 跳过基本信息 (info 不可用)")

        # 2. 关键财务指标 (只有 info 可用时才处理)
        if info:
            try:
                financial_data['key_indicators'] = {
                    # 市场指标
                    '市值': info.get('marketCap', 0),
                    '流通市值': info.get('floatShares', 0) * info.get('currentPrice', 0) if info.get(
                        'floatShares') and info.get('currentPrice') else 0,

                    # 估值指标
                    '市盈率_PE': round(info.get('trailingPE', 0), 2),
                    '远期PE': round(info.get('forwardPE', 0), 2),
                    '市净率_PB': round(info.get('priceToBook', 0), 2),
                    '市销率_PS': round(info.get('priceToSalesTrailing12Months', 0), 2),
                    'PEG比率': round(info.get('pegRatio', 0), 2),

                    # 盈利能力
                    '净资产收益率_ROE': round((info.get('returnOnEquity', 0) * 100), 2) if info.get(
                        'returnOnEquity') else 0,
                    '总资产收益率_ROA': round((info.get('returnOnAssets', 0) * 100), 2) if info.get(
                        'returnOnAssets') else 0,
                    '毛利率': round((info.get('grossMargins', 0) * 100), 2) if info.get('grossMargins') else 0,
                    '营业利润率': round((info.get('operatingMargins', 0) * 100), 2) if info.get(
                        'operatingMargins') else 0,
                    '净利率': round((info.get('profitMargins', 0) * 100), 2) if info.get('profitMargins') else 0,

                    # 财务健康
                    '流动比率': round(info.get('currentRatio', 0), 2),
                    '速动比率': round(info.get('quickRatio', 0), 2),
                    '资产负债率': round(info.get('debtToEquity', 0), 2),

                    # 股息
                    '股息率': round((info.get('dividendYield', 0) * 100), 2) if info.get('dividendYield') else 0,
                    '派息比率': round((info.get('payoutRatio', 0) * 100), 2) if info.get('payoutRatio') else 0,

                    # 增长
                    '收入增长率': round((info.get('revenueGrowth', 0) * 100), 2) if info.get('revenueGrowth') else 0,
                    '盈利增长率': round((info.get('earningsGrowth', 0) * 100), 2) if info.get('earningsGrowth') else 0,

                    '报告期': 'Latest'
                }
                logger.info("✅ 关键指标获取成功")
            except Exception as e:
                logger.warning(f"⚠️ 获取关键指标失败: {e}")
        else:
            # 如果 info 不可用,从财报计算基本指标
            logger.info("⏭️ 跳过关键指标 (info 不可用),将从财报计算")

        # 3. 利润表数据
        try:
            logger.info(f"正在获取 {ticker} 的利润表...")
            income_stmt = stock.financials
            if not income_stmt.empty:
                latest = income_stmt.iloc[:, 0]  # 最新财报

                total_revenue = float(latest.get('Total Revenue', 0)) if 'Total Revenue' in latest.index else 0
                cost_of_revenue = float(latest.get('Cost Of Revenue', 0)) if 'Cost Of Revenue' in latest.index else 0
                gross_profit = float(latest.get('Gross Profit', 0)) if 'Gross Profit' in latest.index else 0
                operating_income = float(latest.get('Operating Income', 0)) if 'Operating Income' in latest.index else 0
                net_income = float(latest.get('Net Income', 0)) if 'Net Income' in latest.index else 0

                financial_data['profit_statement'] = {
                    '营业总收入': total_revenue,
                    '营业成本': cost_of_revenue,
                    '毛利润': gross_profit,
                    '营业利润': operating_income,
                    '净利润': net_income,
                    '毛利率_计算': round((gross_profit / total_revenue * 100), 2) if total_revenue > 0 else 0,
                    '营业利润率_计算': round((operating_income / total_revenue * 100), 2) if total_revenue > 0 else 0,
                    '净利率_计算': round((net_income / total_revenue * 100), 2) if total_revenue > 0 else 0,
                    '报告期': str(income_stmt.columns[0].date()) if hasattr(income_stmt.columns[0], 'date') else str(
                        income_stmt.columns[0])
                }
                logger.info("✅ 利润表数据获取成功")

                # 如果 info 不可用,从利润表补充计算指标
                if not info and 'key_indicators' not in financial_data:
                    financial_data['key_indicators'] = {
                        '净利率': round((net_income / total_revenue * 100), 2) if total_revenue > 0 else 0,
                        '毛利率': round((gross_profit / total_revenue * 100), 2) if total_revenue > 0 else 0,
                        '营业利润率': round((operating_income / total_revenue * 100), 2) if total_revenue > 0 else 0,
                        '报告期': str(income_stmt.columns[0].date()) if hasattr(income_stmt.columns[0],
                                                                                'date') else 'Latest',
                        '数据来源': '从财报计算'
                    }

        except Exception as e:
            logger.warning(f"⚠️ 获取利润表失败: {e}")

        # 4. 资产负债表
        try:
            logger.info(f"正在获取 {ticker} 的资产负债表...")
            balance = stock.balance_sheet
            if not balance.empty:
                latest = balance.iloc[:, 0]

                total_assets = float(latest.get('Total Assets', 0)) if 'Total Assets' in latest.index else 0
                current_assets = float(latest.get('Current Assets', 0)) if 'Current Assets' in latest.index else 0
                total_liabilities = float(latest.get('Total Liabilities Net Minority Interest',
                                                     0)) if 'Total Liabilities Net Minority Interest' in latest.index else 0
                current_liabilities = float(
                    latest.get('Current Liabilities', 0)) if 'Current Liabilities' in latest.index else 0
                stockholders_equity = float(
                    latest.get('Stockholders Equity', 0)) if 'Stockholders Equity' in latest.index else 0

                financial_data['balance_sheet'] = {
                    '资产总计': total_assets,
                    '流动资产合计': current_assets,
                    '非流动资产': total_assets - current_assets if total_assets > current_assets else 0,
                    '负债合计': total_liabilities,
                    '流动负债合计': current_liabilities,
                    '非流动负债': total_liabilities - current_liabilities if total_liabilities > current_liabilities else 0,
                    '所有者权益合计': stockholders_equity,
                    '资产负债率_计算': round((total_liabilities / total_assets * 100), 2) if total_assets > 0 else 0,
                    '流动比率_计算': round((current_assets / current_liabilities), 2) if current_liabilities > 0 else 0,
                    '报告期': str(balance.columns[0].date()) if hasattr(balance.columns[0], 'date') else str(
                        balance.columns[0])
                }
                logger.info("✅ 资产负债表获取成功")

                # 如果 info 不可用且有利润表,补充计算 ROE 和 ROA
                if not info and 'profit_statement' in financial_data and 'key_indicators' in financial_data:
                    net_income = financial_data['profit_statement'].get('净利润', 0)
                    if net_income and stockholders_equity and total_assets:
                        financial_data['key_indicators']['净资产收益率_ROE'] = round(
                            (net_income / stockholders_equity * 100), 2)
                        financial_data['key_indicators']['总资产收益率_ROA'] = round((net_income / total_assets * 100),
                                                                                     2)
                        financial_data['key_indicators']['资产负债率'] = round((total_liabilities / total_assets * 100),
                                                                               2)
                        financial_data['key_indicators']['流动比率'] = round((current_assets / current_liabilities),
                                                                             2) if current_liabilities > 0 else 0

        except Exception as e:
            logger.warning(f"⚠️ 获取资产负债表失败: {e}")

        # 5. 现金流量表
        try:
            logger.info(f"正在获取 {ticker} 的现金流量表...")
            cashflow = stock.cashflow
            if not cashflow.empty:
                latest = cashflow.iloc[:, 0]

                operating_cf = float(
                    latest.get('Operating Cash Flow', 0)) if 'Operating Cash Flow' in latest.index else 0
                investing_cf = float(
                    latest.get('Investing Cash Flow', 0)) if 'Investing Cash Flow' in latest.index else 0
                financing_cf = float(
                    latest.get('Financing Cash Flow', 0)) if 'Financing Cash Flow' in latest.index else 0
                free_cf = float(latest.get('Free Cash Flow', 0)) if 'Free Cash Flow' in latest.index else 0

                financial_data['cash_flow'] = {
                    '经营活动产生的现金流量净额': operating_cf,
                    '投资活动产生的现金流量净额': investing_cf,
                    '筹资活动产生的现金流量净额': financing_cf,
                    '自由现金流': free_cf,
                    '现金流净额': operating_cf + investing_cf + financing_cf,
                    '报告期': str(cashflow.columns[0].date()) if hasattr(cashflow.columns[0], 'date') else str(
                        cashflow.columns[0])
                }
                logger.info("✅ 现金流量表获取成功")
        except Exception as e:
            logger.warning(f"⚠️ 获取现金流量表失败: {e}")

        # 检查是否获取到任何数据
        if not financial_data:
            return {"error": "未能获取任何财务数据"}

        # 添加数据完整性标记
        financial_data['data_completeness'] = {
            'has_basic_info': 'basic_info' in financial_data,
            'has_key_indicators': 'key_indicators' in financial_data,
            'has_profit_statement': 'profit_statement' in financial_data,
            'has_balance_sheet': 'balance_sheet' in financial_data,
            'has_cash_flow': 'cash_flow' in financial_data,
            'info_available': info is not None
        }

        return financial_data

    except Exception as e:
        logger.error(f"❌ 获取 yfinance 数据失败: {e}")
        return {"error": str(e)}

def calculate_financial_ratios(stock_ticker: str) -> Dict[str, float]:
    """
    计算财务比率(基于真实数据)

    Args:
        stock_ticker: 股票代码

    Returns:
        财务比率字典
    """
    try:
        logger.info(f"🧮 计算 {stock_ticker} 的财务比率")

        stock = yf.Ticker(stock_ticker)
        info = stock.info

        ratios = {
            # 盈利能力
            'ROE': round((info.get('returnOnEquity', 0) * 100), 2) if info.get('returnOnEquity') else 0,
            'ROA': round((info.get('returnOnAssets', 0) * 100), 2) if info.get('returnOnAssets') else 0,
            'gross_margin': round((info.get('grossMargins', 0) * 100), 2) if info.get('grossMargins') else 0,
            'operating_margin': round((info.get('operatingMargins', 0) * 100), 2) if info.get(
                'operatingMargins') else 0,
            'net_margin': round((info.get('profitMargins', 0) * 100), 2) if info.get('profitMargins') else 0,

            # 估值
            'PE_ratio': round(info.get('trailingPE', 0), 2),
            'forward_PE': round(info.get('forwardPE', 0), 2),
            'PB_ratio': round(info.get('priceToBook', 0), 2),
            'PS_ratio': round(info.get('priceToSalesTrailing12Months', 0), 2),
            'PEG_ratio': round(info.get('pegRatio', 0), 2),

            # 财务健康
            'debt_to_equity': round(info.get('debtToEquity', 0), 2),
            'current_ratio': round(info.get('currentRatio', 0), 2),
            'quick_ratio': round(info.get('quickRatio', 0), 2),

            # 股息
            'dividend_yield': round((info.get('dividendYield', 0) * 100), 2) if info.get('dividendYield') else 0,
            'payout_ratio': round((info.get('payoutRatio', 0) * 100), 2) if info.get('payoutRatio') else 0,
        }

        logger.info(f"✅ 财务比率计算完成: {ratios}")
        return ratios

    except Exception as e:
        logger.error(f"❌ 计算财务比率失败: {e}")
        return {
            "ROE": 0.0,
            "ROA": 0.0,
            "gross_margin": 0.0,
            "net_margin": 0.0,
            "PE_ratio": 0.0,
            "error": str(e)
        }


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试全球股票财务数据获取")
    print("=" * 60)

    # 测试美股
    print("\n1. 测试美股 - Apple (AAPL)")
    print("-" * 60)
    result = get_financial_data("AAPL")
    if result.get("success"):
        print("✅ 数据获取成功")
        if "basic_info" in result["real_time_data"]:
            print(f"公司: {result['real_time_data']['basic_info']['公司名称']}")
        if "key_indicators" in result["real_time_data"]:
            print(f"ROE: {result['real_time_data']['key_indicators']['净资产收益率_ROE']}%")

    ratios = calculate_financial_ratios("AAPL")
    print(f"财务比率: ROE={ratios.get('ROE')}%, PE={ratios.get('PE_ratio')}")

    # 测试港股
    print("\n2. 测试港股 - 腾讯 (0700.HK)")
    print("-" * 60)
    result = get_financial_data("0700.HK")
    print(f"结果: {result.get('success')}")