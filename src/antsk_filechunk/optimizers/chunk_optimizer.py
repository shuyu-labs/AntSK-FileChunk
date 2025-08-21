"""
切片优化器模块
对初步生成的切片进行优化处理
"""

import logging
from typing import List, Dict, Tuple, Optional
import re

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class ChunkOptimizer:
    """切片优化器主类"""
    
    def __init__(self, config):
        """
        初始化切片优化器
        
        Args:
            config: 切片配置对象
        """
        self.config = config
    
    def optimize_chunks(self, chunks: List) -> List:
        """
        优化切片列表
        
        Args:
            chunks: 初步生成的切片列表
            
        Returns:
            优化后的切片列表
        """
        if not chunks:
            return chunks
        
        logger.info(f"开始优化 {len(chunks)} 个切片")
        
        try:
            # 1. 合并过小的切片
            chunks = self._merge_small_chunks(chunks)
            
            # 2. 分割过大的切片
            chunks = self._split_large_chunks(chunks)
            
            # 3. 优化切片边界
            chunks = self._optimize_boundaries(chunks)
            
            # 4. 后处理
            chunks = self._post_process_chunks(chunks)
            
            logger.info(f"切片优化完成，最终生成 {len(chunks)} 个切片")
            return chunks
            
        except Exception as e:
            logger.error(f"切片优化失败: {e}")
            return chunks
    
    def _merge_small_chunks(self, chunks: List) -> List:
        """
        合并过小的切片
        
        Args:
            chunks: 原始切片列表
            
        Returns:
            合并后的切片列表
        """
        if len(chunks) <= 1:
            return chunks
        
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            chunk_length = len(chunk.content)
            
            # 如果当前切片过小，尝试合并
            if chunk_length < self.config.min_chunk_size:
                if current_chunk is None:
                    current_chunk = chunk
                else:
                    # 检查是否可以合并
                    merged_length = len(current_chunk.content) + chunk_length
                    if merged_length <= self.config.max_chunk_size:
                        current_chunk = self._merge_two_chunks(current_chunk, chunk)
                    else:
                        # 无法合并，保存当前切片并开始新的
                        merged_chunks.append(current_chunk)
                        current_chunk = chunk
            else:
                # 当前切片大小合适
                if current_chunk is not None:
                    # 检查是否可以与前一个小切片合并
                    if len(current_chunk.content) < self.config.target_chunk_size:
                        merged_length = len(current_chunk.content) + chunk_length
                        if merged_length <= self.config.max_chunk_size:
                            merged_chunk = self._merge_two_chunks(current_chunk, chunk)
                            merged_chunks.append(merged_chunk)
                            current_chunk = None
                            continue
                    
                    # 无法合并，分别保存
                    merged_chunks.append(current_chunk)
                    current_chunk = None
                
                merged_chunks.append(chunk)
        
        # 处理最后一个切片
        if current_chunk is not None:
            merged_chunks.append(current_chunk)
        
        logger.debug(f"小切片合并: {len(chunks)} -> {len(merged_chunks)}")
        return merged_chunks
    
    def _split_large_chunks(self, chunks: List) -> List:
        """
        分割过大的切片
        
        Args:
            chunks: 原始切片列表
            
        Returns:
            分割后的切片列表
        """
        split_chunks = []
        
        for chunk in chunks:
            chunk_length = len(chunk.content)
            
            if chunk_length > self.config.max_chunk_size:
                # 需要分割
                sub_chunks = self._split_single_chunk(chunk)
                split_chunks.extend(sub_chunks)
            else:
                split_chunks.append(chunk)
        
        logger.debug(f"大切片分割: {len(chunks)} -> {len(split_chunks)}")
        return split_chunks
    
    def _split_single_chunk(self, chunk) -> List:
        """
        分割单个过大的切片
        
        Args:
            chunk: 要分割的切片
            
        Returns:
            分割后的子切片列表
        """
        content = chunk.content
        target_size = self.config.target_chunk_size
        
        # 尝试按句子分割
        sentences = self._split_into_sentences(content)
        
        if len(sentences) <= 1:
            # 无法按句子分割，按字符强制分割
            return self._force_split_chunk(chunk)
        
        sub_chunks = []
        current_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.config.max_chunk_size and current_sentences:
                # 创建子切片
                sub_chunk = self._create_sub_chunk(
                    current_sentences, 
                    chunk, 
                    len(sub_chunks)
                )
                sub_chunks.append(sub_chunk)
                
                # 重置（考虑重叠）
                if self.config.overlap_ratio > 0 and len(current_sentences) > 1:
                    overlap_count = max(1, int(len(current_sentences) * self.config.overlap_ratio))
                    current_sentences = current_sentences[-overlap_count:]
                    current_length = sum(len(s) for s in current_sentences)
                else:
                    current_sentences = []
                    current_length = 0
            
            current_sentences.append(sentence)
            current_length += sentence_length
        
        # 处理最后一组句子
        if current_sentences:
            sub_chunk = self._create_sub_chunk(
                current_sentences, 
                chunk, 
                len(sub_chunks)
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks if sub_chunks else [chunk]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        if self.config.language == "zh":
            # 中文句子分割
            sentences = re.split(r'[。！？；]', text)
        else:
            # 英文句子分割
            sentences = re.split(r'[.!?;]', text)
        
        # 清理和过滤
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _force_split_chunk(self, chunk) -> List:
        """
        强制按字符分割切片
        
        Args:
            chunk: 要分割的切片
            
        Returns:
            分割后的子切片列表
        """
        content = chunk.content
        target_size = self.config.target_chunk_size
        overlap_size = int(target_size * self.config.overlap_ratio)
        
        sub_chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + target_size, len(content))
            
            # 尝试在单词边界分割（避免截断单词）
            if end < len(content):
                # 向后查找空格
                for i in range(min(50, len(content) - end)):
                    if content[end + i] in ' \n\t':
                        end = end + i
                        break
                # 向前查找空格
                else:
                    for i in range(min(50, end - start)):
                        if content[end - i] in ' \n\t':
                            end = end - i
                            break
            
            sub_content = content[start:end].strip()
            if sub_content:
                from .semantic_chunker import TextChunk
                sub_chunk = TextChunk(
                    content=sub_content,
                    start_pos=start,
                    end_pos=end,
                    semantic_score=chunk.semantic_score,
                    token_count=self._estimate_token_count(sub_content),
                    paragraph_indices=[],
                    chunk_type=chunk.chunk_type,
                    metadata=chunk.metadata.copy() if chunk.metadata else {}
                )
                sub_chunks.append(sub_chunk)
            
            # 计算下一个起始位置（考虑重叠）
            start = max(start + 1, end - overlap_size)
        
        return sub_chunks
    
    def _create_sub_chunk(self, sentences: List[str], parent_chunk, index: int):
        """
        创建子切片
        
        Args:
            sentences: 句子列表
            parent_chunk: 父切片
            index: 子切片索引
            
        Returns:
            子切片对象
        """
        content = ' '.join(sentences)
        
        from .semantic_chunker import TextChunk
        return TextChunk(
            content=content,
            start_pos=0,  # 相对位置
            end_pos=len(content),
            semantic_score=parent_chunk.semantic_score,
            token_count=self._estimate_token_count(content),
            paragraph_indices=parent_chunk.paragraph_indices,
            chunk_type=parent_chunk.chunk_type,
            metadata={
                **(parent_chunk.metadata or {}),
                'parent_chunk': True,
                'sub_chunk_index': index
            }
        )
    
    def _merge_two_chunks(self, chunk1, chunk2):
        """
        合并两个切片
        
        Args:
            chunk1: 第一个切片
            chunk2: 第二个切片
            
        Returns:
            合并后的切片
        """
        merged_content = chunk1.content + '\n\n' + chunk2.content
        merged_paragraphs = list(set(chunk1.paragraph_indices + chunk2.paragraph_indices))
        
        # 重新计算语义得分（简化为平均值）
        merged_score = (chunk1.semantic_score + chunk2.semantic_score) / 2
        
        from .semantic_chunker import TextChunk
        return TextChunk(
            content=merged_content,
            start_pos=chunk1.start_pos,
            end_pos=chunk1.start_pos + len(merged_content),
            semantic_score=merged_score,
            token_count=self._estimate_token_count(merged_content),
            paragraph_indices=merged_paragraphs,
            chunk_type='content',
            metadata={
                'merged': True,
                'original_chunks': [chunk1.chunk_type, chunk2.chunk_type]
            }
        )
    
    def _optimize_boundaries(self, chunks: List) -> List:
        """
        优化切片边界
        
        Args:
            chunks: 切片列表
            
        Returns:
            边界优化后的切片列表
        """
        if len(chunks) <= 1:
            return chunks
        
        optimized_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                optimized_chunks.append(chunk)
                continue
            
            prev_chunk = optimized_chunks[-1]
            
            # 检查是否需要调整边界
            boundary_adjustment = self._calculate_boundary_adjustment(prev_chunk, chunk)
            
            if boundary_adjustment != 0:
                # 调整边界
                adjusted_chunks = self._adjust_boundary(prev_chunk, chunk, boundary_adjustment)
                if len(adjusted_chunks) == 2:
                    optimized_chunks[-1] = adjusted_chunks[0]  # 更新前一个切片
                    optimized_chunks.append(adjusted_chunks[1])  # 添加当前切片
                else:
                    optimized_chunks.append(chunk)
            else:
                optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def _calculate_boundary_adjustment(self, chunk1, chunk2) -> int:
        """
        计算边界调整量
        
        Args:
            chunk1: 第一个切片
            chunk2: 第二个切片
            
        Returns:
            调整量（字符数，正数表示向后调整，负数表示向前调整）
        """
        # 简化的边界优化逻辑
        # 可以根据需要实现更复杂的边界检测算法
        return 0
    
    def _adjust_boundary(self, chunk1, chunk2, adjustment: int) -> List:
        """
        调整两个切片之间的边界
        
        Args:
            chunk1: 第一个切片
            chunk2: 第二个切片
            adjustment: 调整量
            
        Returns:
            调整后的切片列表
        """
        # 简化实现，返回原切片
        return [chunk1, chunk2]
    
    def _post_process_chunks(self, chunks: List) -> List:
        """
        对切片进行后处理
        
        Args:
            chunks: 切片列表
            
        Returns:
            后处理后的切片列表
        """
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 更新切片位置信息
            chunk.start_pos = i * 1000  # 简化的位置计算
            chunk.end_pos = chunk.start_pos + len(chunk.content)
            
            # 清理内容
            chunk.content = self._clean_chunk_content(chunk.content)
            
            # 重新计算token数量
            chunk.token_count = self._estimate_token_count(chunk.content)
            
            # 添加切片序号
            if chunk.metadata is None:
                chunk.metadata = {}
            chunk.metadata['chunk_id'] = i
            
            processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _clean_chunk_content(self, content: str) -> str:
        """
        清理切片内容
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        # 移除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除首尾空白
        content = content.strip()
        
        return content
    
    def _estimate_token_count(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        if self.config.language == "zh":
            # 中文按字符数估算
            return int(len(text) / 1.3)
        else:
            # 英文按单词数估算
            words = text.split()
            return int(len(words) / 0.75)
