from langchain_openai import ChatOpenAI
from config.settings import settings
from loguru import logger


def get_llm(temperature: float = 0.7, model: str = None):
    """
    初始化 DeepSeek LLM

    Args:
        temperature: 生成温度 (0-1)
        model: 模型名称（默认使用配置文件）

    Returns:
        ChatOpenAI 实例
    """
    try:
        llm = ChatOpenAI(
            model=model or settings.DEEPSEEK_MODEL,
            openai_api_key=settings.DEEPSEEK_API_KEY,
            openai_api_base=settings.DEEPSEEK_API_BASE,
            temperature=temperature,
            max_tokens=4000,
            timeout=60,
            max_retries=3
        )
        logger.info(f"✅ LLM 初始化成功: {model or settings.DEEPSEEK_MODEL}")
        return llm
    except Exception as e:
        logger.error(f"❌ LLM 初始化失败: {e}")
        raise