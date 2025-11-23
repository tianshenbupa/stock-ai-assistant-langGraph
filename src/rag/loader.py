from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter  # ✅ 新的导入路径
from typing import List
from pathlib import Path
from loguru import logger
from config.settings import settings


class FinancialReportLoader:
    """财报加载器"""

    def __init__(self):
        self.pdf_directory = Path(settings.PDF_DIRECTORY)
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def load_documents(self) -> List:
        """
        加载并分割PDF文档

        Returns:
            分割后的文档列表
        """
        try:
            logger.info(f"📂 开始加载财报目录: {self.pdf_directory}")

            # 检查目录是否存在
            if not self.pdf_directory.exists():
                logger.warning(f"⚠️  目录不存在，创建: {self.pdf_directory}")
                self.pdf_directory.mkdir(parents=True, exist_ok=True)
                return []

            # 检查是否有 PDF 文件
            pdf_files = list(self.pdf_directory.glob("**/*.pdf"))
            if not pdf_files:
                logger.warning(f"⚠️  目录中没有 PDF 文件: {self.pdf_directory}")
                logger.info(f"💡 请将 PDF 文件放入: {self.pdf_directory.absolute()}")
                return []

            logger.info(f"📄 发现 {len(pdf_files)} 个 PDF 文件:")
            for pdf_file in pdf_files:
                logger.info(f"   - {pdf_file.name}")

            # 加载所有 PDF 文件
            loader = DirectoryLoader(
                str(self.pdf_directory),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True
            )

            documents = loader.load()

            if not documents:
                logger.warning("⚠️  PDF 文件加载失败或为空")
                return []

            logger.info(f"✅ 成功加载 {len(documents)} 个文档页面")

            # 分割文档
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
            )

            splits = text_splitter.split_documents(documents)
            logger.info(f"✅ 文档分割完成，共 {len(splits)} 个块")

            return splits

        except Exception as e:
            logger.error(f"❌ 文档加载失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise