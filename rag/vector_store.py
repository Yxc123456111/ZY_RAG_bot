"""
RAG向量数据库模块
支持ChromaDB，用于存储和检索中医知识文档
"""

import os
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


@dataclass
class SearchResult:
    """搜索结果数据类"""
    content: str
    metadata: Dict
    score: float
    source: str


class TCMVectorStore:
    """
    中医知识向量数据库
    用于存储和检索：针灸、伤寒论、金匮要略、神农本草经、医案等文档
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/vector_db",
        collection_name: str = "tcm_knowledge",
        embedding_model: str = "BAAI/bge-large-zh-v1.5",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 初始化或加载向量数据库
        self.vectorstore = self._init_vectorstore()
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
            length_function=len
        )
    
    def _init_vectorstore(self) -> Chroma:
        """初始化向量数据库"""
        os.makedirs(self.persist_directory, exist_ok=True)
        
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
    
    def add_documents(
        self,
        documents: List[Document],
        source_type: str = "general"
    ) -> List[str]:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            source_type: 文档来源类型 (acupuncture/shanghan/jinkui/shennong/case)
        
        Returns:
            文档ID列表
        """
        # 分割文档
        chunks = self.text_splitter.split_documents(documents)
        
        # 添加来源类型到metadata
        for chunk in chunks:
            chunk.metadata["source_type"] = source_type
            # 生成文档唯一ID
            content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()[:12]
            chunk.metadata["doc_id"] = f"{source_type}_{content_hash}"
        
        # 添加到向量数据库
        ids = self.vectorstore.add_documents(chunks)
        
        # 持久化
        self.vectorstore.persist()
        
        return ids
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件，如 {"source_type": "acupuncture"}
            score_threshold: 相似度阈值
        
        Returns:
            搜索结果列表
        """
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        search_results = []
        for doc, score in results:
            # Chroma返回的是距离，转换为相似度分数 (1 - distance)
            similarity_score = 1 - score
            
            if similarity_score >= score_threshold:
                search_results.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=similarity_score,
                    source=doc.metadata.get("source", "unknown")
                ))
        
        # 按分数排序
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        return search_results
    
    def search_by_source_type(
        self,
        query: str,
        source_type: str,
        k: int = 5
    ) -> List[SearchResult]:
        """
        按来源类型搜索
        
        Args:
            query: 查询文本
            source_type: 来源类型 (acupuncture/shanghan/jinkui/shennong/case)
            k: 返回结果数量
        
        Returns:
            搜索结果列表
        """
        return self.similarity_search(
            query=query,
            k=k,
            filter_dict={"source_type": source_type}
        )
    
    def multi_source_search(
        self,
        query: str,
        source_types: List[str],
        k_per_source: int = 3
    ) -> Dict[str, List[SearchResult]]:
        """
        多来源搜索
        
        Args:
            query: 查询文本
            source_types: 来源类型列表
            k_per_source: 每类来源返回结果数
        
        Returns:
            按来源分类的搜索结果
        """
        results = {}
        for source_type in source_types:
            results[source_type] = self.search_by_source_type(
                query=query,
                source_type=source_type,
                k=k_per_source
            )
        return results
    
    def delete_by_source(self, source_type: str) -> None:
        """删除某类来源的所有文档"""
        self.vectorstore.delete(where={"source_type": source_type})
        self.vectorstore.persist()
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息"""
        collection = self.vectorstore._collection
        return {
            "total_documents": collection.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }
    
    def clear(self) -> None:
        """清空向量数据库"""
        self.vectorstore.delete_collection()
        self.vectorstore = self._init_vectorstore()


class DocumentLoader:
    """
    文档加载器
    支持多种格式的中医文档加载
    """
    
    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.md': 'markdown',
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.json': 'json'
    }
    
    @staticmethod
    def load_from_file(file_path: str, source_type: str = "general") -> List[Document]:
        """
        从文件加载文档
        
        Args:
            file_path: 文件路径
            source_type: 文档来源类型
        
        Returns:
            Document列表
        """
        import os
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt' or ext == '.md':
            return DocumentLoader._load_text(file_path, source_type)
        elif ext == '.pdf':
            return DocumentLoader._load_pdf(file_path, source_type)
        elif ext == '.docx':
            return DocumentLoader._load_docx(file_path, source_type)
        elif ext == '.json':
            return DocumentLoader._load_json(file_path, source_type)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    @staticmethod
    def _load_text(file_path: str, source_type: str) -> List[Document]:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [Document(
            page_content=content,
            metadata={
                "source": file_path,
                "source_type": source_type,
                "file_type": "text"
            }
        )]
    
    @staticmethod
    def _load_pdf(file_path: str, source_type: str) -> List[Document]:
        """加载PDF文件"""
        try:
            from langchain.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata["source_type"] = source_type
            
            return documents
        except ImportError:
            raise ImportError("请安装PyPDF2: pip install PyPDF2")
    
    @staticmethod
    def _load_docx(file_path: str, source_type: str) -> List[Document]:
        """加载Word文件"""
        try:
            from langchain.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata["source_type"] = source_type
            
            return documents
        except ImportError:
            raise ImportError("请安装python-docx: pip install python-docx")
    
    @staticmethod
    def _load_json(file_path: str, source_type: str) -> List[Document]:
        """加载JSON文件"""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        if isinstance(data, list):
            for item in data:
                content = item.get('content', '') or item.get('text', '')
                metadata = {k: v for k, v in item.items() if k not in ['content', 'text']}
                metadata['source'] = file_path
                metadata['source_type'] = source_type
                
                if content:
                    documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    @staticmethod
    def load_directory(
        directory: str,
        source_type: str = "general",
        recursive: bool = True
    ) -> List[Document]:
        """
        加载目录中的所有文档
        
        Args:
            directory: 目录路径
            source_type: 文档来源类型
            recursive: 是否递归子目录
        
        Returns:
            Document列表
        """
        import os
        
        documents = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in DocumentLoader.SUPPORTED_EXTENSIONS:
                        file_path = os.path.join(root, file)
                        try:
                            docs = DocumentLoader.load_from_file(file_path, source_type)
                            documents.extend(docs)
                        except Exception as e:
                            print(f"加载文件失败 {file_path}: {e}")
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in DocumentLoader.SUPPORTED_EXTENSIONS:
                        try:
                            docs = DocumentLoader.load_from_file(file_path, source_type)
                            documents.extend(docs)
                        except Exception as e:
                            print(f"加载文件失败 {file_path}: {e}")
        
        return documents


# 便捷函数
def create_vector_store(
    persist_dir: str = "./data/vector_db",
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
) -> TCMVectorStore:
    """创建向量数据库实例"""
    return TCMVectorStore(
        persist_directory=persist_dir,
        embedding_model=embedding_model
    )


def init_knowledge_base(
    vector_store: TCMVectorStore,
    data_dir: str = "./data/documents"
) -> None:
    """
    初始化知识库
    加载各类型文档到向量数据库
    """
    import os
    
    source_mapping = {
        "acupuncture": "针灸",
        "shanghan": "伤寒论",
        "jinkui": "金匮要略",
        "shennong": "神农本草经",
        "cases": "医案"
    }
    
    for source_type, dir_name in source_mapping.items():
        dir_path = os.path.join(data_dir, dir_name)
        
        if os.path.exists(dir_path):
            print(f"正在加载 {dir_name} 文档...")
            documents = DocumentLoader.load_directory(
                directory=dir_path,
                source_type=source_type,
                recursive=True
            )
            
            if documents:
                ids = vector_store.add_documents(documents, source_type=source_type)
                print(f"已加载 {len(documents)} 个文档，分割为 {len(ids)} 个片段")
            else:
                print(f"目录 {dir_path} 中没有找到文档")
        else:
            print(f"目录不存在: {dir_path}")
