"""
语义文本切片器核心模块
提供基于语义理解的智能文本切片功能
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import nltk
import jieba
from tqdm import tqdm

from ..parsers.document_parser import DocumentParser
from ..analyzers.semantic_analyzer import SemanticAnalyzer
from ..optimizers.chunk_optimizer import ChunkOptimizer
from ..evaluators.quality_evaluator import QualityEvaluator

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
