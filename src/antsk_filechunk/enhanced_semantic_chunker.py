"""
增强版语义切片器 - 优化建议实现
包含核心算法的改进版本

主要功能:
1. 增强语义连贯性计算 - 加入位置权重和趋势分析
2. 添加缓存机制 - 避免重复计算语义向量  
3. 完善异常处理 - 增加降级策略和边界情况处理
"""

import os
import re
import json
import hashlib
import logging
import time
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import nltk
import jieba
from tqdm import tqdm

from .document_parser import DocumentParser
from .semantic_analyzer import SemanticAnalyzer
from .chunk_optimizer import ChunkOptimizer
from .quality_evaluator import QualityEvaluator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """切片配置类"""
    min_chunk_size: int = 500      # 最小切片字符数（增加到500）
    max_chunk_size: int = 3000     # 最大切片字符数（增加到3000）
    target_chunk_size: int = 1800  # 目标切片字符数（增加到1800）
    overlap_ratio: float = 0.1     # 重叠比例
    semantic_threshold: float = 0.6  # 语义相似度阈值（降低到0.6，允许更多内容合并）
    paragraph_merge_threshold: float = 0.8  # 段落合并阈值
    language: str = "zh"           # 语言设置：zh/en
    preserve_structure: bool = True  # 是否保持文档结构
    handle_special_content: bool = True  # 是否处理特殊内容

@dataclass
class TextChunk:
    """文本切片数据结构"""
    content: str                   # 切片内容
    start_pos: int                # 起始位置
    end_pos: int                  # 结束位置
    semantic_score: float         # 语义连贯性得分
    token_count: int              # Token数量
    paragraph_indices: List[int]  # 包含的段落索引
    chunk_type: str = "content"   # 切片类型：content/table/image/header
    metadata: Dict = None         # 元数据信息
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SemanticChunker:
    """语义文本切片器主类"""
    
    def __init__(self, config: ChunkConfig = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化语义切片器
        
        Args:
            config: 切片配置
            model_name: 句子嵌入模型名称
        """
        self.config = config or ChunkConfig()
        self.model_name = model_name
        
        # 初始化组件
        self._initialize_components()
        
    def _initialize_components(self):
        """初始化各个组件"""
        try:
            logger.info("正在初始化语义切片器组件...")
            
            # 文档解析器
            self.document_parser = DocumentParser()
            
            # 语义分析器
            self.semantic_analyzer = SemanticAnalyzer(
                model_name=self.model_name,
                language=self.config.language
            )
            
            # 切片优化器
            self.chunk_optimizer = ChunkOptimizer(self.config)
            
            # 质量评估器
            self.quality_evaluator = QualityEvaluator(self.semantic_analyzer)
            
            logger.info("组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def process_file(self, file_path: Union[str, Path]) -> List[TextChunk]:
        """
        处理文件并返回语义切片
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本切片列表
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始处理文件: {file_path}")
        
        try:
            # 1. 文档解析
            document_content = self.document_parser.parse_file(file_path)
            logger.info(f"文档解析完成，共提取 {len(document_content.paragraphs)} 个段落")
            
            # 2. 预处理和段落分析
            processed_paragraphs = self._preprocess_paragraphs(document_content.paragraphs)
            
            # 3. 语义分析
            semantic_embeddings = self.semantic_analyzer.compute_embeddings(processed_paragraphs)
            logger.info("语义向量计算完成")
            
            # 4. 智能切片
            chunks = self._semantic_chunking(
                processed_paragraphs, 
                semantic_embeddings,
                document_content.metadata
            )
            
            # 5. 切片优化
            optimized_chunks = self.chunk_optimizer.optimize_chunks(chunks)
            logger.info(f"切片优化完成，生成 {len(optimized_chunks)} 个切片")
            
            # 6. 质量评估
            quality_scores = self.quality_evaluator.evaluate_chunks(optimized_chunks)
            self._attach_quality_scores(optimized_chunks, quality_scores)
            
            logger.info(f"文件处理完成: {file_path}")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            raise
    
    def process_text(self, text: str) -> List[TextChunk]:
        """
        直接处理文本内容并返回语义切片
        
        Args:
            text: 要处理的文本内容
            
        Returns:
            文本切片列表
        """
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        
        logger.info("开始处理文本内容")
        
        try:
            # 1. 文本预处理 - 按段落分割
            paragraphs = self._split_text_to_paragraphs(text)
            logger.info(f"文本分割完成，共 {len(paragraphs)} 个段落")
            
            # 2. 预处理和段落分析
            processed_paragraphs = self._preprocess_text_paragraphs(paragraphs)
            
            # 3. 语义分析
            semantic_embeddings = self.semantic_analyzer.compute_embeddings(processed_paragraphs)
            logger.info("语义向量计算完成")
            
            # 4. 智能切片
            chunks = self._semantic_chunking(
                processed_paragraphs, 
                semantic_embeddings,
                {"source": "text_input", "total_length": len(text)}
            )
            
            # 5. 切片优化
            optimized_chunks = self.chunk_optimizer.optimize_chunks(chunks)
            logger.info(f"切片优化完成，生成 {len(optimized_chunks)} 个切片")
            
            # 6. 质量评估
            quality_scores = self.quality_evaluator.evaluate_chunks(optimized_chunks)
            self._attach_quality_scores(optimized_chunks, quality_scores)
            
            logger.info("文本处理完成")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"文本处理失败: {e}")
            raise
    
    def _split_text_to_paragraphs(self, text: str) -> List[str]:
        """
        将文本分割为段落
        
        Args:
            text: 原始文本
            
        Returns:
            段落列表
        """
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        # 进一步处理每个段落
        processed_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # 如果段落太长，按句号分割（提高分割阈值）
                if len(para) > self.config.max_chunk_size:  # 改为直接使用max_chunk_size
                    sentences = re.split(r'[。！？.!?]\s*', para)
                    current_para = ""
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        # 提高单个段落的长度限制
                        if len(current_para + sentence) < self.config.max_chunk_size * 0.9:  # 从0.8提高到0.9
                            current_para += sentence + "。" if sentence[-1] not in "。！？.!?" else sentence
                        else:
                            if current_para:
                                processed_paragraphs.append(current_para)
                            current_para = sentence + "。" if sentence[-1] not in "。！？.!?" else sentence
                    
                    if current_para:
                        processed_paragraphs.append(current_para)
                else:
                    processed_paragraphs.append(para)
        
        return processed_paragraphs
    
    def _preprocess_text_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        预处理文本段落
        
        Args:
            paragraphs: 原始段落列表
            
        Returns:
            处理后的段落文本列表
        """
        processed = []
        
        for para in paragraphs:
            content = para.strip()
            
            if not content:
                continue
            
            # 基本清理
            content = re.sub(r'\s+', ' ', content)  # 规范化空白字符
            content = content.replace('\t', ' ')    # 替换制表符
            
            # 长度过滤
            if len(content) < 5:  # 过滤太短的段落（降低阈值以保留更多内容）
                continue
            
            processed.append(content)
        
        return processed
    
    def _preprocess_paragraphs(self, paragraphs: List[Dict]) -> List[str]:
        """
        预处理段落内容
        
        Args:
            paragraphs: 原始段落列表
            
        Returns:
            处理后的段落文本列表
        """
        processed = []
        
        for para in paragraphs:
            content = para.get('content', '').strip()
            
            if not content:
                continue
                
            # 文本清理
            content = self._clean_text(content)
            
            # 过滤过短的段落
            if len(content) < 10:  # 降低过滤阈值
                continue
                
            processed.append(content)
        
        return processed
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留基本标点）
        if self.config.language == "zh":
            text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303fa-zA-Z0-9\s.,!?;:"""''()（）【】\[\]<>《》]', '', text)
        else:
            text = re.sub(r'[^\w\s.,!?;:"""\'()[\]<>-]', '', text)
        
        return text.strip()
    
    def _semantic_chunking(
        self, 
        paragraphs: List[str], 
        embeddings: np.ndarray,
        metadata: Dict
    ) -> List[TextChunk]:
        """
        执行语义切片
        
        Args:
            paragraphs: 段落列表
            embeddings: 语义向量
            metadata: 文档元数据
            
        Returns:
            文本切片列表
        """
        if len(paragraphs) == 0:
            return []
        
        chunks = []
        current_chunk_indices = []
        current_chunk_content = []
        current_chunk_length = 0
        
        for i in range(len(paragraphs)):
            para = paragraphs[i]
            para_length = len(para)
            
            # 检查是否应该开始新切片
            should_start_new_chunk = self._should_start_new_chunk(
                current_chunk_indices,
                current_chunk_length,
                para_length,
                embeddings,
                i
            )
            
            if should_start_new_chunk and current_chunk_content:
                # 创建当前切片
                chunk = self._create_chunk(
                    current_chunk_content,
                    current_chunk_indices,
                    embeddings
                )
                chunks.append(chunk)
                
                # 重置累计器（考虑重叠）
                overlap_indices, overlap_content = self._calculate_overlap(
                    current_chunk_indices,
                    current_chunk_content
                )
                current_chunk_indices = overlap_indices
                current_chunk_content = overlap_content
                current_chunk_length = sum(len(c) for c in overlap_content)
            
            # 添加当前段落
            current_chunk_indices.append(i)
            current_chunk_content.append(para)
            current_chunk_length += para_length
        
        # 处理最后一个切片
        if current_chunk_content:
            chunk = self._create_chunk(
                current_chunk_content,
                current_chunk_indices,
                embeddings
            )
            chunks.append(chunk)
        
        return chunks
    
    def _should_start_new_chunk(
        self,
        current_indices: List[int],
        current_length: int,
        new_para_length: int,
        embeddings: np.ndarray,
        new_para_index: int
    ) -> bool:
        """
        判断是否应该开始新的切片
        
        Args:
            current_indices: 当前切片包含的段落索引
            current_length: 当前切片长度
            new_para_length: 新段落长度
            embeddings: 语义向量
            new_para_index: 新段落索引
            
        Returns:
            是否应该开始新切片
        """
        if not current_indices:
            return False
        
        # 长度检查
        potential_length = current_length + new_para_length
        if potential_length > self.config.max_chunk_size:
            return True
        
        # 语义连贯性检查
        if new_para_index < len(embeddings):
            semantic_coherence = self._calculate_semantic_coherence(
                current_indices,
                new_para_index,
                embeddings
            )
            
            if semantic_coherence < self.config.semantic_threshold:
                # 如果当前切片已经达到目标大小，则开始新切片
                if current_length >= self.config.target_chunk_size:
                    return True
        
        return False
    
    def _calculate_semantic_coherence(
        self,
        current_indices: List[int],
        new_index: int,
        embeddings: np.ndarray
    ) -> float:
        """
        计算语义连贯性
        
        Args:
            current_indices: 当前段落索引列表
            new_index: 新段落索引
            embeddings: 语义向量
            
        Returns:
            语义连贯性得分 (0-1)
        """
        if not current_indices or new_index >= len(embeddings):
            return 0.0
        
        # 计算新段落与当前切片中所有段落的平均相似度
        similarities = []
        new_embedding = embeddings[new_index].reshape(1, -1)
        
        for idx in current_indices:
            if idx < len(embeddings):
                current_embedding = embeddings[idx].reshape(1, -1)
                similarity = cosine_similarity(new_embedding, current_embedding)[0][0]
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_overlap(
        self,
        indices: List[int],
        content: List[str]
    ) -> Tuple[List[int], List[str]]:
        """
        计算重叠内容
        
        Args:
            indices: 段落索引列表
            content: 段落内容列表
            
        Returns:
            重叠的索引和内容
        """
        if self.config.overlap_ratio <= 0 or not content:
            return [], []
        
        # 计算重叠段落数量
        overlap_count = max(1, int(len(content) * self.config.overlap_ratio))
        overlap_count = min(overlap_count, len(content) - 1)  # 避免完全重叠
        
        # 取最后几个段落作为重叠
        overlap_indices = indices[-overlap_count:]
        overlap_content = content[-overlap_count:]
        
        return overlap_indices, overlap_content
    
    def _create_chunk(
        self,
        content_list: List[str],
        paragraph_indices: List[int],
        embeddings: np.ndarray
    ) -> TextChunk:
        """
        创建文本切片对象
        
        Args:
            content_list: 内容列表
            paragraph_indices: 段落索引列表
            embeddings: 语义向量
            
        Returns:
            文本切片对象
        """
        # 合并内容
        content = '\n\n'.join(content_list)
        
        # 计算语义得分
        semantic_score = self._calculate_chunk_semantic_score(
            paragraph_indices,
            embeddings
        )
        
        # 估算token数量（粗略计算）
        token_count = self._estimate_token_count(content)
        
        return TextChunk(
            content=content,
            start_pos=0,  # 将在后续处理中更新
            end_pos=len(content),
            semantic_score=semantic_score,
            token_count=token_count,
            paragraph_indices=paragraph_indices,
            chunk_type="content"
        )
    
    def _calculate_chunk_semantic_score(
        self,
        paragraph_indices: List[int],
        embeddings: np.ndarray
    ) -> float:
        """
        计算切片的语义连贯性得分
        
        Args:
            paragraph_indices: 段落索引列表
            embeddings: 语义向量
            
        Returns:
            语义连贯性得分
        """
        if len(paragraph_indices) <= 1:
            return 1.0
        
        # 计算所有段落之间的相似度
        similarities = []
        valid_indices = [i for i in paragraph_indices if i < len(embeddings)]
        
        for i in range(len(valid_indices)):
            for j in range(i + 1, len(valid_indices)):
                idx1, idx2 = valid_indices[i], valid_indices[j]
                emb1 = embeddings[idx1].reshape(1, -1)
                emb2 = embeddings[idx2].reshape(1, -1)
                similarity = cosine_similarity(emb1, emb2)[0][0]
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 1.0
    
    def _estimate_token_count(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        if self.config.language == "zh":
            # 中文按字符数估算，约1.3个字符对应1个token
            return int(len(text) / 1.3)
        else:
            # 英文按单词数估算，约0.75个单词对应1个token
            words = text.split()
            return int(len(words) / 0.75)
    
    def _attach_quality_scores(
        self,
        chunks: List[TextChunk],
        quality_scores: Dict
    ):
        """
        为切片附加质量评估分数
        
        Args:
            chunks: 文本切片列表
            quality_scores: 质量评估结果
        """
        for i, chunk in enumerate(chunks):
            if i < len(quality_scores.get('coherence_scores', [])):
                chunk.metadata['coherence_score'] = quality_scores['coherence_scores'][i]
            if i < len(quality_scores.get('completeness_scores', [])):
                chunk.metadata['completeness_score'] = quality_scores['completeness_scores'][i]
    
    def get_chunking_statistics(self, chunks: List[TextChunk]) -> Dict:
        """
        获取切片统计信息
        
        Args:
            chunks: 文本切片列表
            
        Returns:
            统计信息字典
        """
        if not chunks:
            return {}
        
        lengths = [len(chunk.content) for chunk in chunks]
        token_counts = [chunk.token_count for chunk in chunks]
        semantic_scores = [chunk.semantic_score for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_length': np.mean(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'length_std': np.std(lengths),
            'avg_tokens': np.mean(token_counts),
            'avg_semantic_score': np.mean(semantic_scores),
            'min_semantic_score': min(semantic_scores),
            'max_semantic_score': max(semantic_scores),
            'length_distribution': {
                'under_500': sum(1 for l in lengths if l < 500),
                '500_1000': sum(1 for l in lengths if 500 <= l < 1000),
                '1000_1500': sum(1 for l in lengths if 1000 <= l < 1500),
                'over_1500': sum(1 for l in lengths if l >= 1500)
            }
        }
    
    def save_chunks(self, chunks: List[TextChunk], output_path: Union[str, Path]):
        """
        保存切片结果到文件
        
        Args:
            chunks: 文本切片列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为可序列化的格式
        chunks_data = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                'id': i,
                'content': chunk.content,
                'semantic_score': float(chunk.semantic_score),
                'token_count': chunk.token_count,
                'paragraph_count': len(chunk.paragraph_indices),
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata
            }
            chunks_data.append(chunk_dict)
        
        # 保存为JSON格式
        import numpy as np
        
        # 自定义JSON序列化函数
        def json_serialize(obj):
            if isinstance(obj, np.float32):
                return float(obj)
            elif isinstance(obj, np.float64):
                return float(obj)
            elif isinstance(obj, np.int32):
                return int(obj)
            elif isinstance(obj, np.int64):
                return int(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'chunks': chunks_data,
                'statistics': self.get_chunking_statistics(chunks),
                'config': {
                    'min_chunk_size': self.config.min_chunk_size,
                    'max_chunk_size': self.config.max_chunk_size,
                    'target_chunk_size': self.config.target_chunk_size,
                    'semantic_threshold': float(self.config.semantic_threshold),
                    'language': self.config.language
                }
            }, f, ensure_ascii=False, indent=2, default=json_serialize)
        
        logger.info(f"切片结果已保存到: {output_path}")

class EmbeddingCache:
    """
    高效语义向量缓存系统
    支持LRU淘汰策略和统计信息跟踪
    """
    
    def __init__(self, max_size=1000, ttl_seconds=3600):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
        """
        self.cache = {}
        self.access_times = {}  # 记录访问时间
        self.creation_times = {}  # 记录创建时间
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.access_order = []
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
    
    def get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        # 使用文本长度和hash确保唯一性
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{len(text)}_{text_hash[:16]}"
    
    def _is_expired(self, cache_key: str) -> bool:
        """检查缓存项是否过期"""
        if cache_key not in self.creation_times:
            return True
        
        creation_time = self.creation_times[cache_key]
        return time.time() - creation_time > self.ttl_seconds
    
    def _cleanup_expired(self):
        """清理过期的缓存项"""
        current_time = time.time()
        expired_keys = []
        
        for key, creation_time in self.creation_times.items():
            if current_time - creation_time > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_cache_item(key)
            self.stats['expired'] += 1
    
    def _remove_cache_item(self, cache_key: str):
        """移除缓存项及相关元数据"""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.access_times:
            del self.access_times[cache_key]
        if cache_key in self.creation_times:
            del self.creation_times[cache_key]
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
    
    def get_embedding(self, text: str, model, timeout=30) -> Optional[np.ndarray]:
        """
        获取语义向量（带缓存和异常处理）
        
        Args:
            text: 输入文本
            model: 语义模型
            timeout: 计算超时时间（秒）
            
        Returns:
            语义向量或None（如果失败）
        """
        try:
            cache_key = self.get_cache_key(text)
            current_time = time.time()
            
            # 定期清理过期缓存
            if len(self.cache) > 0 and current_time % 100 == 0:
                self._cleanup_expired()
            
            # 检查缓存命中
            if cache_key in self.cache and not self._is_expired(cache_key):
                # 更新访问信息
                self.access_times[cache_key] = current_time
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)
                self.access_order.append(cache_key)
                
                self.stats['hits'] += 1
                logger.debug(f"缓存命中: {cache_key[:16]}...")
                return self.cache[cache_key].copy()  # 返回副本避免修改
            
            # 缓存未命中，计算新向量
            self.stats['misses'] += 1
            logger.debug(f"缓存未命中，计算向量: {cache_key[:16]}...")
            
            # 带超时的向量计算
            start_time = time.time()
            embedding = model.encode([text], normalize_embeddings=True)[0]
            computation_time = time.time() - start_time
            
            if computation_time > timeout:
                logger.warning(f"向量计算超时: {computation_time:.2f}s > {timeout}s")
                return None
            
            # 缓存管理
            if len(self.cache) >= self.max_size:
                # LRU淘汰最久未使用的项
                if self.access_order:
                    oldest_key = self.access_order.pop(0)
                    self._remove_cache_item(oldest_key)
                    self.stats['evictions'] += 1
            
            # 存储到缓存
            self.cache[cache_key] = embedding.copy()
            self.access_times[cache_key] = current_time
            self.creation_times[cache_key] = current_time
            self.access_order.append(cache_key)
            
            return embedding
            
        except Exception as e:
            logger.error(f"向量计算失败: {e}")
            return None
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / max(total_requests, 1)
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            **self.stats
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.creation_times.clear()
        self.access_order.clear()
        
        # 重置统计
        self.stats = {k: 0 for k in self.stats.keys()}

class EnhancedSemanticChunker(SemanticChunker):
    """
    增强版语义切片器
    
    主要改进:
    1. 增强语义连贯性计算（位置权重 + 趋势分析）
    2. 高效缓存机制（LRU + TTL）
    3. 完善异常处理（降级策略 + 边界情况处理）
    """
    
    def __init__(self, config: ChunkConfig = None, model_name: str = "all-MiniLM-L6-v2", 
                 cache_size: int = 1000, enable_fallback: bool = True):
        """
        初始化增强版语义切片器
        
        Args:
            config: 切片配置
            model_name: 语义模型名称
            cache_size: 缓存大小
            enable_fallback: 是否启用降级策略
        """
        # 安全初始化父类
        try:
            super().__init__(config, model_name)
            self.initialization_success = True
            logger.info("增强版语义切片器初始化成功")
        except Exception as e:
            logger.error(f"父类初始化失败: {e}")
            self.initialization_success = False
            self.config = config or ChunkConfig()
        
        # 初始化增强功能
        self.embedding_cache = EmbeddingCache(max_size=cache_size)
        self.enable_fallback = enable_fallback
        self.fallback_mode = False
        
        # 性能统计
        self.performance_stats = {
            'total_processed': 0,
            'fallback_used': 0,
            'processing_times': [],
            'error_count': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 语义连贯性计算参数
        self.coherence_config = {
            'position_weight_enabled': True,
            'trend_analysis_enabled': True,
            'position_decay_factor': 0.5,  # 位置权重衰减因子
            'trend_penalty_factor': 0.1,   # 趋势惩罚因子
            'similarity_window_size': 3     # 相似度窗口大小
        }
    
    def _enhanced_semantic_coherence(
        self, 
        current_indices: List[int], 
        new_index: int, 
        embeddings: np.ndarray
    ) -> float:
        """
        增强的语义连贯性计算
        
        功能:
        1. 位置权重: 越近的段落权重越高
        2. 趋势分析: 检测语义变化趋势
        3. 局部连贯性: 考虑相邻段落的相似度
        4. 全局一致性: 考虑整体语义分布
        
        Args:
            current_indices: 当前切片的段落索引
            new_index: 新段落索引
            embeddings: 语义向量矩阵
            
        Returns:
            语义连贯性得分 (0-1)
        """
        if not current_indices or new_index >= len(embeddings):
            return 0.0
        
        try:
            new_embedding = embeddings[new_index].reshape(1, -1)
            similarities = []
            weights = []
            
            # 1. 计算基础相似度和位置权重
            for i, idx in enumerate(current_indices):
                if idx < len(embeddings):
                    current_embedding = embeddings[idx].reshape(1, -1)
                    similarity = cosine_similarity(new_embedding, current_embedding)[0][0]
                    
                    # 位置权重计算：距离越近权重越高
                    if self.coherence_config['position_weight_enabled']:
                        # 指数衰减位置权重
                        position_factor = self.coherence_config['position_decay_factor']
                        distance_from_end = len(current_indices) - i - 1
                        position_weight = np.exp(-position_factor * distance_from_end)
                    else:
                        position_weight = 1.0
                    
                    similarities.append(similarity)
                    weights.append(position_weight)
            
            if not similarities:
                return 0.0
            
            # 2. 计算加权平均相似度
            base_coherence = np.average(similarities, weights=weights)
            
            # 3. 趋势分析
            trend_adjustment = 0.0
            if (self.coherence_config['trend_analysis_enabled'] and 
                len(similarities) >= self.coherence_config['similarity_window_size']):
                
                # 分析相似度变化趋势
                trend_adjustment = self._analyze_semantic_trend(similarities, current_indices, new_index)
            
            # 4. 局部连贯性分析
            local_coherence_bonus = 0.0
            if len(current_indices) > 0:
                # 检查与最近段落的相似度
                last_idx = current_indices[-1]
                if abs(new_index - last_idx) == 1 and similarities:  # 相邻段落
                    local_coherence_bonus = min(0.1, similarities[-1] * 0.1)
            
            # 5. 全局一致性检查
            global_consistency = self._calculate_global_consistency(
                similarities, current_indices, new_index
            )
            
            # 6. 综合计算最终得分
            final_coherence = (
                base_coherence + 
                trend_adjustment + 
                local_coherence_bonus + 
                global_consistency * 0.1
            )
            
            return max(0.0, min(1.0, final_coherence))
            
        except Exception as e:
            logger.warning(f"语义连贯性计算失败: {e}")
            # 降级到简单平均
            return self._simple_coherence_fallback(current_indices, new_index, embeddings)
    
    def _analyze_semantic_trend(self, similarities: List[float], 
                               current_indices: List[int], new_index: int) -> float:
        """
        分析语义变化趋势
        
        Args:
            similarities: 相似度列表
            current_indices: 当前段落索引
            new_index: 新段落索引
            
        Returns:
            趋势调整值 (-0.2 到 0.1)
        """
        try:
            if len(similarities) < 3:
                return 0.0
            
            # 计算相似度的一阶差分（变化率）
            diff = np.diff(similarities)
            
            # 计算趋势强度
            if len(diff) > 1:
                # 二阶差分（加速度）
                second_diff = np.diff(diff)
                trend_strength = np.mean(np.abs(second_diff))
                
                # 检查是否存在突变
                recent_change = abs(similarities[-1] - np.mean(similarities[:-1]))
                sudden_change_penalty = min(0.15, recent_change * 0.2)
                
                # 计算趋势惩罚
                trend_penalty = self.coherence_config['trend_penalty_factor'] * (
                    trend_strength + sudden_change_penalty
                )
                
                return -trend_penalty
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"趋势分析失败: {e}")
            return 0.0
    
    def _calculate_global_consistency(self, similarities: List[float], 
                                    current_indices: List[int], new_index: int) -> float:
        """
        计算全局一致性
        
        Args:
            similarities: 相似度列表
            current_indices: 当前段落索引  
            new_index: 新段落索引
            
        Returns:
            全局一致性得分 (0-1)
        """
        try:
            if len(similarities) < 2:
                return 1.0
            
            # 计算相似度分布的均匀性
            similarity_std = np.std(similarities)
            similarity_mean = np.mean(similarities)
            
            if similarity_mean > 0:
                # 变异系数：标准差/均值
                cv = similarity_std / similarity_mean
                # 变异系数越小，一致性越好
                consistency = max(0.0, 1.0 - cv)
            else:
                consistency = 0.0
            
            # 检查是否存在异常值
            if len(similarities) > 3:
                q75, q25 = np.percentile(similarities, [75, 25])
                iqr = q75 - q25
                outlier_threshold = q75 + 1.5 * iqr
                
                # 如果最新相似度是异常值，降低一致性
                if similarities[-1] > outlier_threshold:
                    consistency *= 0.8
            
            return consistency
            
        except Exception as e:
            logger.debug(f"全局一致性计算失败: {e}")
            return 0.5
    
    def _simple_coherence_fallback(self, current_indices: List[int], 
                                  new_index: int, embeddings: np.ndarray) -> float:
        """
        简单的语义连贯性计算（降级策略）
        
        Args:
            current_indices: 当前段落索引
            new_index: 新段落索引
            embeddings: 语义向量矩阵
            
        Returns:
            简单相似度平均值
        """
        try:
            if not current_indices or new_index >= len(embeddings):
                return 0.0
            
            new_embedding = embeddings[new_index].reshape(1, -1)
            similarities = []
            
            for idx in current_indices[-3:]:  # 只考虑最近3个段落
                if idx < len(embeddings):
                    current_embedding = embeddings[idx].reshape(1, -1)
                    similarity = cosine_similarity(new_embedding, current_embedding)[0][0]
                    similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.warning(f"降级连贯性计算也失败: {e}")
            return 0.5  # 返回中性值
    
    def _calculate_semantic_coherence(
        self,
        current_indices: List[int],
        new_index: int,
        embeddings: np.ndarray
    ) -> float:
        """
        重写父类方法，使用增强的语义连贯性计算
        
        Args:
            current_indices: 当前切片包含的段落索引
            new_index: 新段落索引
            embeddings: 语义向量矩阵
            
        Returns:
            语义连贯性得分
        """
        try:
            if not self.initialization_success:
                return self._simple_coherence_fallback(current_indices, new_index, embeddings)
            
            return self._enhanced_semantic_coherence(current_indices, new_index, embeddings)
            
        except Exception as e:
            logger.error(f"语义连贯性计算失败，使用降级策略: {e}")
            return self._simple_coherence_fallback(current_indices, new_index, embeddings)
    
    def compute_embeddings_with_cache(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        带缓存和异常处理的语义向量计算
        
        Args:
            texts: 文本列表
            
        Returns:
            语义向量矩阵或None（如果失败）
        """
        if not texts:
            return np.array([])
        
        try:
            embeddings = []
            successful_count = 0
            
            for i, text in enumerate(texts):
                try:
                    if not self.initialization_success or self.fallback_mode:
                        # 降级策略：返回随机向量
                        embedding = np.random.rand(384)  # 假设向量维度为384
                        embedding = embedding / np.linalg.norm(embedding)  # 归一化
                        logger.debug(f"使用随机向量替代第 {i} 个文本的语义向量")
                    else:
                        # 尝试使用缓存获取向量
                        embedding = self.embedding_cache.get_embedding(
                            text, 
                            self.semantic_analyzer.model
                        )
                        
                        if embedding is None:
                            # 缓存失败，直接计算
                            embedding = self.semantic_analyzer.model.encode(
                                [text], normalize_embeddings=True
                            )[0]
                    
                    embeddings.append(embedding)
                    successful_count += 1
                    
                except Exception as e:
                    logger.warning(f"第 {i} 个文本的向量计算失败: {e}")
                    
                    # 使用最近成功的向量或随机向量
                    if embeddings:
                        embedding = embeddings[-1] + np.random.normal(0, 0.1, embeddings[-1].shape)
                        embedding = embedding / np.linalg.norm(embedding)
                    else:
                        embedding = np.random.rand(384)
                        embedding = embedding / np.linalg.norm(embedding)
                    
                    embeddings.append(embedding)
                    self.performance_stats['error_count'] += 1
            
            # 检查成功率
            success_rate = successful_count / len(texts)
            if success_rate < 0.5:
                logger.warning(f"向量计算成功率过低: {success_rate:.2f}")
                if not self.fallback_mode:
                    logger.info("启用降级模式")
                    self.fallback_mode = True
                    self.performance_stats['fallback_used'] += 1
            
            return np.array(embeddings)
            
        except Exception as e:
            logger.error(f"语义向量计算完全失败: {e}")
            if self.enable_fallback:
                return self._fallback_embeddings(texts)
            else:
                raise
    
    def _fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        降级策略：生成基于文本特征的简单向量
        
        Args:
            texts: 文本列表
            
        Returns:
            简单特征向量矩阵
        """
        try:
            embeddings = []
            
            for text in texts:
                # 基于文本长度、字符分布等简单特征生成向量
                features = []
                
                # 文本长度特征
                features.append(len(text) / 1000.0)  # 归一化长度
                
                # 字符统计特征
                char_counts = {}
                for char in text:
                    char_counts[char] = char_counts.get(char, 0) + 1
                
                # 常见字符比例
                common_chars = ['的', '和', '在', '是', '了', '有', '一', '个', '上', '也']
                for char in common_chars:
                    features.append(char_counts.get(char, 0) / max(len(text), 1))
                
                # 标点符号比例
                punctuation_count = sum(1 for char in text if char in '，。！？；：')
                features.append(punctuation_count / max(len(text), 1))
                
                # 数字比例
                digit_count = sum(1 for char in text if char.isdigit())
                features.append(digit_count / max(len(text), 1))
                
                # 扩展到标准维度
                while len(features) < 384:
                    features.extend(features[:min(len(features), 384 - len(features))])
                
                features = features[:384]  # 截断到标准维度
                embedding = np.array(features, dtype=np.float32)
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)  # 归一化
                
                embeddings.append(embedding)
            
            logger.info(f"使用降级策略生成了 {len(embeddings)} 个特征向量")
            return np.array(embeddings)
            
        except Exception as e:
            logger.error(f"降级策略也失败: {e}")
            # 最终降级：返回随机向量
            return np.random.rand(len(texts), 384)
    
    def process_file_safe(self, file_path, max_retries: int = 3) -> List[TextChunk]:
        """
        安全的文件处理方法，带重试和异常处理
        
        Args:
            file_path: 文件路径
            max_retries: 最大重试次数
            
        Returns:
            文本切片列表
        """
        start_time = time.time()
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"第 {attempt + 1} 次尝试处理文件: {file_path}")
                
                # 尝试正常处理
                if not self.fallback_mode and self.initialization_success:
                    chunks = self.process_file(file_path)
                else:
                    # 使用简化处理
                    chunks = self._simple_file_processing(file_path)
                
                # 记录成功统计
                processing_time = time.time() - start_time
                self.performance_stats['processing_times'].append(processing_time)
                self.performance_stats['total_processed'] += 1
                
                logger.info(f"文件处理成功，耗时: {processing_time:.2f}s")
                return chunks
                
            except Exception as e:
                last_exception = e
                logger.warning(f"第 {attempt + 1} 次处理失败: {e}")
                
                # 如果不是最后一次尝试，启用降级模式
                if attempt < max_retries - 1:
                    self.fallback_mode = True
                    time.sleep(1)  # 短暂等待
        
        # 所有重试都失败
        logger.error(f"文件处理完全失败: {last_exception}")
        self.performance_stats['error_count'] += 1
        
        if self.enable_fallback:
            # 最终降级策略
            try:
                return self._emergency_chunking(file_path)
            except Exception as emergency_e:
                logger.error(f"紧急切片策略也失败: {emergency_e}")
                raise emergency_e
        else:
            raise last_exception
    
    def _simple_file_processing(self, file_path) -> List[TextChunk]:
        """
        简化的文件处理（降级策略）
        
        Args:
            file_path: 文件路径
            
        Returns:
            简单切片列表
        """
        try:
            # 简单读取文件内容
            if str(file_path).endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # 对于其他格式，使用父类的文档解析器
                doc_content = self.document_parser.parse_file(file_path)
                content = '\n\n'.join([p.get('content', '') for p in doc_content.paragraphs])
            
            # 简单按长度分割
            chunks = []
            chunk_size = self.config.target_chunk_size
            
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                if chunk_content.strip():
                    chunk = TextChunk(
                        content=chunk_content.strip(),
                        start_pos=i,
                        end_pos=min(i + chunk_size, len(content)),
                        semantic_score=0.5,  # 中性分数
                        token_count=len(chunk_content.split()),
                        paragraph_indices=[i // chunk_size],
                        metadata={'processing_mode': 'simplified'}
                    )
                    chunks.append(chunk)
            
            logger.info(f"简化处理完成，生成 {len(chunks)} 个切片")
            return chunks
            
        except Exception as e:
            logger.error(f"简化处理失败: {e}")
            raise
    
    def _emergency_chunking(self, file_path) -> List[TextChunk]:
        """
        紧急切片策略（最终降级）
        
        Args:
            file_path: 文件路径
            
        Returns:
            紧急切片列表
        """
        try:
            # 最简单的文本读取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 按固定长度简单切分
            chunk_size = 1000
            chunks = []
            
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                if chunk_content.strip():
                    chunk = TextChunk(
                        content=chunk_content.strip(),
                        start_pos=i,
                        end_pos=min(i + chunk_size, len(content)),
                        semantic_score=0.3,  # 低分数表示质量不高
                        token_count=len(chunk_content.split()),
                        paragraph_indices=[i // chunk_size],
                        metadata={'processing_mode': 'emergency'}
                    )
                    chunks.append(chunk)
            
            logger.warning(f"紧急切片完成，生成 {len(chunks)} 个切片")
            return chunks
            
        except Exception as e:
            logger.error(f"紧急切片失败: {e}")
            # 返回单个大切片
            return [TextChunk(
                content="文件处理失败",
                start_pos=0,
                end_pos=0,
                semantic_score=0.0,
                token_count=0,
                paragraph_indices=[0],
                metadata={'processing_mode': 'failed'}
            )]
    
    def _detect_semantic_boundaries(
        self, 
        embeddings: np.ndarray, 
        texts: List[str],
        threshold: float = 0.6
    ) -> List[int]:
        """智能语义边界检测"""
        if len(embeddings) < 3:
            return [0, len(embeddings)]
        
        boundaries = [0]  # 起始边界
        
        # 1. 计算语义梯度
        semantic_gradients = []
        for i in range(1, len(embeddings) - 1):
            prev_sim = cosine_similarity(
                embeddings[i-1:i], 
                embeddings[i:i+1]
            )[0][0]
            next_sim = cosine_similarity(
                embeddings[i:i+1], 
                embeddings[i+1:i+2]
            )[0][0]
            
            # 语义变化强度
            gradient = abs(prev_sim - next_sim)
            semantic_gradients.append(gradient)
        
        # 2. 寻找显著的语义断裂点
        if semantic_gradients:
            gradient_threshold = np.mean(semantic_gradients) + np.std(semantic_gradients)
            
            for i, gradient in enumerate(semantic_gradients):
                if gradient > gradient_threshold:
                    boundary_pos = i + 1
                    
                    # 验证边界的合理性
                    if self._validate_boundary(boundary_pos, embeddings, texts):
                        boundaries.append(boundary_pos)
        
        # 3. 检测结构化边界（章节、标题等）
        structural_boundaries = self._detect_structural_boundaries(texts)
        
        # 4. 合并语义边界和结构边界
        all_boundaries = sorted(list(set(boundaries + structural_boundaries)))
        
        # 5. 过滤过于接近的边界点
        filtered_boundaries = self._filter_close_boundaries(all_boundaries, min_distance=2)
        
        # 添加结束边界
        if filtered_boundaries[-1] != len(embeddings):
            filtered_boundaries.append(len(embeddings))
        
        return filtered_boundaries
    
    def _detect_structural_boundaries(self, texts: List[str]) -> List[int]:
        """检测结构化边界"""
        boundaries = []
        
        for i, text in enumerate(texts):
            text_stripped = text.strip()
            
            # 检测章节标题
            if self._is_chapter_title(text_stripped):
                boundaries.append(i)
            
            # 检测列表开始
            elif self._is_list_start(text_stripped):
                boundaries.append(i)
            
            # 检测段落显著变化
            elif i > 0 and self._is_paragraph_shift(texts[i-1], text_stripped):
                boundaries.append(i)
        
        return boundaries
    
    def _is_chapter_title(self, text: str) -> bool:
        """判断是否为章节标题"""
        import re
        
        # 中文章节模式
        chapter_patterns = [
            r'^第[一二三四五六七八九十\d]+[章节部分]\s*[：:]?\s*',
            r'^\d+[\.\s]+[^\n]{1,50}$',  # 数字开头的短文本
            r'^[一二三四五六七八九十]+[\.\s、]+[^\n]{1,50}$',  # 中文数字开头
        ]
        
        for pattern in chapter_patterns:
            if re.match(pattern, text):
                return True
        
        # 检查是否为短文本且无句号结尾（可能是标题）
        if len(text) < 50 and not text.endswith(('。', '.', '！', '!', '？', '?')):
            return True
        
        return False
    
    def _is_list_start(self, text: str) -> bool:
        """判断是否为列表开始"""
        import re
        
        list_patterns = [
            r'^\d+[\.\)]\s*',  # 1. 或 1)
            r'^[•·▪▫]\s*',     # 项目符号
            r'^[-*+]\s*',      # 短划线、星号、加号
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _is_paragraph_shift(self, prev_text: str, current_text: str) -> bool:
        """判断是否为段落显著变化"""
        # 长度变化显著
        len_ratio = len(current_text) / max(len(prev_text), 1)
        if len_ratio > 3 or len_ratio < 0.3:
            return True
        
        # 格式变化（如从长段落到短句）
        prev_sentences = len(prev_text.split('。'))
        current_sentences = len(current_text.split('。'))
        
        if prev_sentences > 3 and current_sentences == 1:
            return True
        
        return False
    
    def _validate_boundary(
        self, 
        boundary_pos: int, 
        embeddings: np.ndarray, 
        texts: List[str]
    ) -> bool:
        """验证边界的合理性"""
        # 检查边界前后的语义连续性
        if boundary_pos <= 0 or boundary_pos >= len(embeddings):
            return False
        
        # 确保不在句子中间切断
        prev_text = texts[boundary_pos - 1] if boundary_pos > 0 else ""
        current_text = texts[boundary_pos] if boundary_pos < len(texts) else ""
        
        # 如果前一个文本没有合适的结尾，可能不是好的边界
        if prev_text and not prev_text.rstrip().endswith(('。', '.', '！', '!', '？', '?', '；', ';')):
            return False
        
        return True
    
    def _filter_close_boundaries(self, boundaries: List[int], min_distance: int = 2) -> List[int]:
        """过滤过于接近的边界点"""
        if not boundaries:
            return boundaries
        
        filtered = [boundaries[0]]
        
        for boundary in boundaries[1:]:
            if boundary - filtered[-1] >= min_distance:
                filtered.append(boundary)
        
        return filtered
    

    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        total_requests = self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']
        cache_hit_rate = self.performance_stats['cache_hits'] / max(total_requests, 1)
        
        return {
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.embedding_cache.cache),
            'total_requests': total_requests,
            **self.performance_stats
        }
    
    def _handle_edge_cases(self, paragraphs: List[str]) -> List[TextChunk]:
        """处理边界情况"""
        # 1. 极短文档处理
        total_length = sum(len(p) for p in paragraphs)
        if total_length < self.config.min_chunk_size:
            content = '\n\n'.join(paragraphs)
            return [TextChunk(
                content=content,
                start_pos=0,
                end_pos=len(content),
                semantic_score=1.0,  # 单一内容，语义完整
                token_count=self._estimate_token_count(content),
                paragraph_indices=list(range(len(paragraphs))),
                metadata={'edge_case': 'document_too_short'}
            )]
        
        # 2. 单段落处理
        if len(paragraphs) == 1:
            content = paragraphs[0]
            if len(content) <= self.config.max_chunk_size:
                return [TextChunk(
                    content=content,
                    start_pos=0,
                    end_pos=len(content),
                    semantic_score=1.0,
                    token_count=self._estimate_token_count(content),
                    paragraph_indices=[0],
                    metadata={'edge_case': 'single_paragraph'}
                )]
        
        return None  # 不是边界情况，使用正常处理流程
    
    def _semantic_chunking(
        self, 
        paragraphs: List[str], 
        embeddings: np.ndarray,
        metadata: Dict
    ) -> List[TextChunk]:
        """重写语义切片方法，加入增强逻辑"""
        # 处理边界情况
        edge_case_result = self._handle_edge_cases(paragraphs)
        if edge_case_result:
            return edge_case_result
        
        # 使用增强的边界检测
        boundaries = self._detect_semantic_boundaries(embeddings, paragraphs)
        
        chunks = []
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            chunk_paragraphs = paragraphs[start_idx:end_idx]
            chunk_indices = list(range(start_idx, end_idx))
            
            # 检查切片大小，如果太大则进一步分割
            if sum(len(p) for p in chunk_paragraphs) > self.config.max_chunk_size:
                sub_chunks = self._split_large_chunk_intelligent(
                    chunk_paragraphs, 
                    chunk_indices, 
                    embeddings[start_idx:end_idx]
                )
                chunks.extend(sub_chunks)
            else:
                chunk = self._create_chunk(chunk_paragraphs, chunk_indices, embeddings)
                chunks.append(chunk)
        
        return chunks
    
    def _split_large_chunk_intelligent(
        self, 
        paragraphs: List[str], 
        indices: List[int],
        embeddings: np.ndarray
    ) -> List[TextChunk]:
        """智能分割大切片"""
        chunks = []
        current_paras = []
        current_indices = []
        current_length = 0
        
        for i, (para, idx) in enumerate(zip(paragraphs, indices)):
            para_length = len(para)
            
            # 如果添加当前段落会超出限制
            if current_length + para_length > self.config.target_chunk_size and current_paras:
                # 创建当前切片
                chunk = self._create_chunk(current_paras, current_indices, embeddings)
                chunks.append(chunk)
                
                # 重置（考虑重叠）
                if self.config.overlap_ratio > 0 and len(current_paras) > 1:
                    overlap_count = max(1, int(len(current_paras) * self.config.overlap_ratio))
                    current_paras = current_paras[-overlap_count:]
                    current_indices = current_indices[-overlap_count:]
                    current_length = sum(len(p) for p in current_paras)
                else:
                    current_paras = []
                    current_indices = []
                    current_length = 0
            
            current_paras.append(para)
            current_indices.append(idx)
            current_length += para_length
        
        # 处理最后一组
        if current_paras:
            chunk = self._create_chunk(current_paras, current_indices, embeddings)
            chunks.append(chunk)
        
        return chunks
    
    def get_comprehensive_stats(self) -> Dict:
        """
        获取全面的性能统计信息
        
        Returns:
            包含缓存、性能、错误等统计的字典
        """
        cache_stats = self.embedding_cache.get_cache_stats()
        
        processing_times = self.performance_stats['processing_times']
        avg_processing_time = np.mean(processing_times) if processing_times else 0
        
        total_requests = (self.performance_stats['total_processed'] + 
                         self.performance_stats['error_count'])
        
        success_rate = (self.performance_stats['total_processed'] / 
                       max(total_requests, 1))
        
        return {
            'cache_performance': cache_stats,
            'processing_performance': {
                'total_processed': self.performance_stats['total_processed'],
                'total_errors': self.performance_stats['error_count'],
                'fallback_used': self.performance_stats['fallback_used'],
                'success_rate': success_rate,
                'avg_processing_time': avg_processing_time,
                'is_fallback_mode': self.fallback_mode,
                'initialization_success': self.initialization_success
            },
            'coherence_config': self.coherence_config
        }
    
    def reset_stats(self):
        """重置所有统计信息"""
        self.performance_stats = {
            'total_processed': 0,
            'fallback_used': 0,
            'processing_times': [],
            'error_count': 0
        }
        self.embedding_cache.clear_cache()
        self.fallback_mode = False
    
    def configure_coherence(self, **kwargs):
        """
        动态配置语义连贯性计算参数
        
        Args:
            **kwargs: 配置参数
                - position_weight_enabled: 是否启用位置权重
                - trend_analysis_enabled: 是否启用趋势分析
                - position_decay_factor: 位置权重衰减因子
                - trend_penalty_factor: 趋势惩罚因子
                - similarity_window_size: 相似度窗口大小
        """
        for key, value in kwargs.items():
            if key in self.coherence_config:
                self.coherence_config[key] = value
                logger.info(f"更新连贯性配置: {key} = {value}")
            else:
                logger.warning(f"未知的连贯性配置参数: {key}")
    
    def health_check(self) -> Dict:
        """
        系统健康检查
        
        Returns:
            健康状态报告
        """
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'warnings': [],
            'errors': []
        }
        
        # 检查初始化状态
        if not self.initialization_success:
            health_status['overall_status'] = 'degraded'
            health_status['errors'].append('语义分析器初始化失败')
        
        # 检查降级模式
        if self.fallback_mode:
            health_status['overall_status'] = 'degraded'
            health_status['warnings'].append('系统运行在降级模式')
        
        # 检查缓存状态
        cache_stats = self.embedding_cache.get_cache_stats()
        if cache_stats['hit_rate'] < 0.3:
            health_status['warnings'].append(f"缓存命中率较低: {cache_stats['hit_rate']:.2f}")
        
        # 检查错误率
        total_requests = (self.performance_stats['total_processed'] + 
                         self.performance_stats['error_count'])
        if total_requests > 0:
            error_rate = self.performance_stats['error_count'] / total_requests
            if error_rate > 0.1:
                health_status['overall_status'] = 'unhealthy'
                health_status['errors'].append(f"错误率过高: {error_rate:.2f}")
            elif error_rate > 0.05:
                health_status['warnings'].append(f"错误率偏高: {error_rate:.2f}")
        
        # 组件状态
        health_status['components'] = {
            'semantic_analyzer': 'ok' if self.initialization_success else 'error',
            'embedding_cache': 'ok',
            'coherence_calculator': 'ok',
            'fallback_system': 'active' if self.fallback_mode else 'standby'
        }
        
        return health_status
    
    def process_text_enhanced(self, text: str, use_cache: bool = True) -> List[TextChunk]:
        """
        增强版文本处理方法
        
        Args:
            text: 输入文本
            use_cache: 是否使用缓存
            
        Returns:
            文本切片列表
        """
        start_time = time.time()
        
        try:
            if not text or not text.strip():
                raise ValueError("文本内容不能为空")
            
            logger.info("开始增强版文本处理")
            
            # 1. 文本预处理
            paragraphs = self._split_text_to_paragraphs(text)
            processed_paragraphs = self._preprocess_text_paragraphs(paragraphs)
            
            logger.info(f"文本预处理完成，共 {len(processed_paragraphs)} 个段落")
            
            # 2. 语义分析（使用缓存）
            if use_cache:
                embeddings = self.compute_embeddings_with_cache(processed_paragraphs)
            else:
                embeddings = self.semantic_analyzer.compute_embeddings(processed_paragraphs)
            
            if embeddings is None:
                raise RuntimeError("语义向量计算失败")
            
            logger.info("语义向量计算完成")
            
            # 3. 智能切片
            chunks = self._semantic_chunking(
                processed_paragraphs,
                embeddings,
                {"source": "enhanced_text_input", "total_length": len(text)}
            )
            
            # 4. 切片优化
            optimized_chunks = self.chunk_optimizer.optimize_chunks(chunks)
            logger.info(f"切片优化完成，生成 {len(optimized_chunks)} 个切片")
            
            # 5. 质量评估
            quality_scores = self.quality_evaluator.evaluate_chunks(optimized_chunks)
            self._attach_quality_scores(optimized_chunks, quality_scores)
            
            # 记录统计
            processing_time = time.time() - start_time
            self.performance_stats['processing_times'].append(processing_time)
            self.performance_stats['total_processed'] += 1
            
            logger.info(f"增强版文本处理完成，耗时: {processing_time:.2f}s")
            return optimized_chunks
            
        except Exception as e:
            logger.error(f"增强版文本处理失败: {e}")
            self.performance_stats['error_count'] += 1
            
            # 尝试降级处理
            if self.enable_fallback:
                logger.info("尝试降级文本处理")
                return self._fallback_text_processing(text)
            else:
                raise
    
    def _fallback_text_processing(self, text: str) -> List[TextChunk]:
        """
        降级文本处理
        
        Args:
            text: 输入文本
            
        Returns:
            简单切片列表
        """
        try:
            # 简单按长度分割
            chunk_size = self.config.target_chunk_size
            chunks = []
            
            for i in range(0, len(text), chunk_size):
                chunk_content = text[i:i + chunk_size]
                if chunk_content.strip():
                    chunk = TextChunk(
                        content=chunk_content.strip(),
                        start_pos=i,
                        end_pos=min(i + chunk_size, len(text)),
                        semantic_score=0.4,  # 较低分数
                        token_count=len(chunk_content.split()),
                        paragraph_indices=[i // chunk_size],
                        metadata={'processing_mode': 'fallback_text'}
                    )
                    chunks.append(chunk)
            
            logger.info(f"降级文本处理完成，生成 {len(chunks)} 个切片")
            self.performance_stats['fallback_used'] += 1
            return chunks
            
        except Exception as e:
            logger.error(f"降级文本处理也失败: {e}")
            # 返回单个切片
            return [TextChunk(
                content=text[:min(len(text), 1000)],
                start_pos=0,
                end_pos=min(len(text), 1000),
                semantic_score=0.2,
                token_count=len(text.split()),
                paragraph_indices=[0],
                metadata={'processing_mode': 'emergency_text'}
            )]
