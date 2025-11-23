from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from typing import List, Optional
from loguru import logger
from pathlib import Path
from config.settings import settings
from src.rag.loader import FinancialReportLoader


class RAGRetriever:
    """RAG 检索器"""

    def __init__(self):
        self.vector_store_path = settings.VECTOR_STORE_PATH
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embeddings = None
        self.vector_store = None
        self._initialized = False

    def initialize(self, force_reload: bool = False):
        """
        初始化 RAG 系统

        Args:
            force_reload: 是否强制重新加载文档
        """
        try:
            logger.info("🚀 初始化 RAG 系统...")

            # 初始化嵌入模型
            logger.info(f"📥 加载嵌入模型: {self.embedding_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            # 检查向量库是否存在
            import os
            vector_store_exists = os.path.exists(self.vector_store_path)

            # ===== 🔧 修改这部分逻辑 =====
            if vector_store_exists and not force_reload:
                logger.info("📚 加载已存在的向量数据库...")
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )

                # ✅ 检查向量库是否为空
                collection_count = self.vector_store._collection.count()

                if collection_count == 0:
                    logger.warning("⚠️  向量库为空，尝试加载文档...")
                    self._load_and_add_documents()
                else:
                    logger.info(f"📚 向量库已包含 {collection_count} 个文档块")
            else:
                logger.info("📄 创建新的向量数据库并加载文档...")
                self._load_and_add_documents()
            # ===== 结束修改 =====

            self._initialized = True
            collection_count = self.vector_store._collection.count()
            logger.info(f"✅ RAG 系统初始化完成，向量库包含 {collection_count} 个文档块")

        except Exception as e:
            logger.error(f"❌ RAG 初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _load_and_add_documents(self):
        """
        加载并添加文档到向量库（内部方法）
        """
        try:
            loader = FinancialReportLoader()
            documents = loader.load_documents()

            if not documents:
                logger.warning("⚠️  没有可用的文档")
                pdf_dir = Path(settings.PDF_DIRECTORY)
                logger.info(f"💡 提示: 请将 PDF 财报放入 {pdf_dir.absolute()}")

                # 创建空向量库
                if self.vector_store is None:
                    self.vector_store = Chroma(
                        persist_directory=self.vector_store_path,
                        embedding_function=self.embeddings
                    )
            else:
                logger.info(f"📥 添加 {len(documents)} 个文档块到向量库...")

                if self.vector_store is None:
                    # 第一次创建
                    self.vector_store = Chroma.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        persist_directory=self.vector_store_path
                    )
                else:
                    # 添加到现有向量库
                    self.vector_store.add_documents(documents)

                # ❌ 移除这行
                # self.vector_store.persist()

                # ✅ 新版本的 Chroma 会自动持久化,不需要手动调用
                logger.info(f"✅ 文档加载完成")

        except Exception as e:
            logger.error(f"❌ 文档加载失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

            # 确保至少创建空向量库
            if self.vector_store is None:
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )

    def query(self, query: str, top_k: int = 5, stock_ticker: Optional[str] = None) -> List[dict]:
        """
        检索相关文档

        Args:
            query: 查询问题
            top_k: 返回结果数量
            stock_ticker: 股票代码过滤（可选）

        Returns:
            相关文档列表
        """
        if not self._initialized:
            raise RuntimeError("RAG 系统未初始化，请先调用 initialize()")

        try:
            # 构建过滤条件
            filter_dict = None
            if stock_ticker:
                logger.info(f"🔍 检索股票 {stock_ticker} 相关文档")

            # 执行相似度搜索
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter_dict
            )

            # 格式化结果
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })

            logger.info(f"✅ 检索到 {len(formatted_results)} 个相关文档")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            return []

    def get_context_for_agent(self, query: str, stock_ticker: str, top_k: int = 3) -> str:
        """
        为代理获取上下文字符串

        Args:
            query: 查询问题
            stock_ticker: 股票代码
            top_k: 返回结果数量

        Returns:
            格式化的上下文字符串
        """
        results = self.query(query, top_k, stock_ticker)

        if not results:
            return "未找到相关财报信息。"

        context_parts = ["以下是从财报中检索到的相关信息：\n"]
        for i, result in enumerate(results, 1):
            context_parts.append(f"\n【文档 {i}】")
            context_parts.append(f"内容：{result['content'][:500]}...")  # 限制长度
            context_parts.append(f"相似度：{result['similarity_score']:.4f}\n")

        return "\n".join(context_parts)

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def collection_size(self) -> int:
        if not self._initialized or not self.vector_store:
            return 0
        try:
            return self.vector_store._collection.count()
        except:
            return 0


# 全局 RAG 实例
rag_retriever = RAGRetriever()