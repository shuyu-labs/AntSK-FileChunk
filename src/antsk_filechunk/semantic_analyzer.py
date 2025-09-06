"""
语义分析器模块
提供文本语义向量计算和相似度分析功能
"""

import logging
from typing import List, Dict, Optional, Tuple
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """语义分析器主类"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", language: str = "zh"):
        """
        初始化语义分析器
        
        Args:
            model_name: 句子嵌入模型名称
            language: 语言设置 ("zh" 或 "en")
        """
        self.model_name = model_name
        self.language = language
        self.model = None
        self.stopwords_set = set()
        
        self._initialize_model()
        self._initialize_language_resources()
    
    def _initialize_model(self):
        """初始化语义嵌入模型"""
        try:
            logger.info(f"正在加载语义模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("语义模型加载完成")
        except Exception as e:
            logger.error(f"语义模型加载失败: {e}")
            # 使用备选模型
            fallback_models = [
                "paraphrase-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "distilbert-base-nli-stsb-mean-tokens"
            ]
            
            for fallback_model in fallback_models:
                try:
                    logger.info(f"尝试加载备选模型: {fallback_model}")
                    self.model = SentenceTransformer(fallback_model)
                    self.model_name = fallback_model
                    logger.info(f"成功加载备选模型: {fallback_model}")
                    break
                except Exception as e2:
                    logger.warning(f"备选模型 {fallback_model} 也加载失败: {e2}")
                    continue
            
            if self.model is None:
                raise RuntimeError("所有语义模型都加载失败")
    
    def _initialize_language_resources(self):
        """初始化语言处理资源"""
        try:
            if self.language == "en":
                # 下载NLTK资源
                try:
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    nltk.download('punkt', quiet=True)
                
                try:
                    nltk.data.find('corpora/stopwords')
                    self.stopwords_set = set(stopwords.words('english'))
                except LookupError:
                    nltk.download('stopwords', quiet=True)
                    self.stopwords_set = set(stopwords.words('english'))
            
            elif self.language == "zh":
                # 中文停用词（简化版）
                self.stopwords_set = {
                    '的', '了', '在', '是', '我', '有', '和', '就', 
                    '不', '人', '都', '一', '一个', '上', '也', '很', 
                    '到', '说', '要', '去', '你', '会', '着', '没有',
                    '看', '好', '自己', '这', '那', '里', '就是', '还'
                }
            
            logger.info(f"语言资源初始化完成 (语言: {self.language})")
            
        except Exception as e:
            logger.warning(f"语言资源初始化部分失败: {e}")
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        计算文本列表的语义向量
        
        Args:
            texts: 文本列表
            
        Returns:
            语义向量矩阵 (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        try:
            logger.info(f"正在计算 {len(texts)} 个文本的语义向量...")
            
            # 预处理文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 计算嵌入向量
            embeddings = self.model.encode(
                processed_texts,
                show_progress_bar=True,
                batch_size=32,
                normalize_embeddings=True  # 归一化向量
            )
            
            logger.info(f"语义向量计算完成，向量维度: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"语义向量计算失败: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        if not text or not text.strip():
            return ""
        
        # 检查是否是图片占位符
        if text.startswith('[IMAGE_PLACEHOLDER_'):
            # 对于图片占位符，返回一个通用的图片描述用于语义计算
            return "图片内容"
        
        # 基本清理
        text = text.strip()
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 限制文本长度（避免过长文本影响嵌入质量）
        max_length = 512 if self.language == "zh" else 256
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        计算语义向量之间的相似度矩阵
        
        Args:
            embeddings: 语义向量矩阵
            
        Returns:
            相似度矩阵 (n_texts, n_texts)
        """
        if embeddings.size == 0:
            return np.array([])
        
        try:
            similarity_matrix = cosine_similarity(embeddings)
            return similarity_matrix
        except Exception as e:
            logger.error(f"相似度矩阵计算失败: {e}")
            raise
    
    def find_semantic_boundaries(
        self, 
        embeddings: np.ndarray, 
        threshold: float = 0.6,  # 降低默认阈值以减少分割
        window_size: int = 5     # 增大窗口以更平滑地处理
    ) -> List[int]:
        """
        基于语义相似度找到语义边界点
        
        Args:
            embeddings: 语义向量矩阵
            threshold: 相似度阈值
            window_size: 滑动窗口大小
            
        Returns:
            语义边界点索引列表
        """
        if len(embeddings) < 2:
            return []
        
        boundaries = [0]  # 起始点
        
        try:
            # 计算连续段落间的相似度
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity(
                    embeddings[i:i+1], 
                    embeddings[i+1:i+2]
                )[0][0]
                similarities.append(sim)
            
            # 使用滑动窗口平滑相似度
            if len(similarities) > window_size:
                smoothed_similarities = []
                for i in range(len(similarities)):
                    start_idx = max(0, i - window_size // 2)
                    end_idx = min(len(similarities), i + window_size // 2 + 1)
                    avg_sim = np.mean(similarities[start_idx:end_idx])
                    smoothed_similarities.append(avg_sim)
                similarities = smoothed_similarities
            
            # 找到相似度显著下降的点
            for i, sim in enumerate(similarities):
                if sim < threshold:
                    boundaries.append(i + 1)
            
            # 添加结束点
            if boundaries[-1] != len(embeddings):
                boundaries.append(len(embeddings))
            
            logger.debug(f"发现 {len(boundaries) - 1} 个语义段落")
            return boundaries
            
        except Exception as e:
            logger.error(f"语义边界检测失败: {e}")
            return [0, len(embeddings)]
    
    def analyze_topic_coherence(
        self, 
        texts: List[str], 
        embeddings: Optional[np.ndarray] = None
    ) -> Dict:
        """
        分析文本集合的主题连贯性
        
        Args:
            texts: 文本列表
            embeddings: 预计算的嵌入向量（可选）
            
        Returns:
            主题连贯性分析结果
        """
        if not texts:
            return {'coherence_score': 0.0, 'topic_distribution': []}
        
        try:
            # 计算或使用提供的嵌入向量
            if embeddings is None:
                embeddings = self.compute_embeddings(texts)
            
            # 计算整体连贯性得分
            if len(embeddings) > 1:
                similarity_matrix = self.compute_similarity_matrix(embeddings)
                # 计算上三角矩阵的平均相似度（排除对角线）
                upper_triangle = np.triu(similarity_matrix, k=1)
                non_zero_count = np.count_nonzero(upper_triangle)
                coherence_score = np.sum(upper_triangle) / non_zero_count if non_zero_count > 0 else 0
            else:
                coherence_score = 1.0
            
            # 简化的主题分布分析
            topic_distribution = self._analyze_topic_distribution(texts, embeddings)
            
            return {
                'coherence_score': float(coherence_score),
                'topic_distribution': topic_distribution,
                'text_count': len(texts),
                'avg_similarity': float(coherence_score)
            }
            
        except Exception as e:
            logger.error(f"主题连贯性分析失败: {e}")
            return {'coherence_score': 0.0, 'topic_distribution': []}
    
    def _analyze_topic_distribution(
        self, 
        texts: List[str], 
        embeddings: np.ndarray
    ) -> List[Dict]:
        """
        分析主题分布（简化版）
        
        Args:
            texts: 文本列表
            embeddings: 嵌入向量
            
        Returns:
            主题分布信息
        """
        try:
            # 使用K-means进行简单聚类
            from sklearn.cluster import KMeans
            
            if len(embeddings) < 2:
                return [{'topic_id': 0, 'texts': list(range(len(texts))), 'centroid': embeddings[0] if len(embeddings) > 0 else []}]
            
            # 确定聚类数量
            n_clusters = min(max(2, len(texts) // 3), 5)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # 构建主题分布
            topic_distribution = []
            for i in range(n_clusters):
                cluster_indices = np.where(cluster_labels == i)[0]
                if len(cluster_indices) > 0:
                    topic_distribution.append({
                        'topic_id': i,
                        'texts': cluster_indices.tolist(),
                        'centroid': kmeans.cluster_centers_[i].tolist(),
                        'size': len(cluster_indices)
                    })
            
            return topic_distribution
            
        except Exception as e:
            logger.warning(f"主题分布分析失败: {e}")
            return []
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的语义相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度得分 (0-1)
        """
        try:
            embeddings = self.compute_embeddings([text1, text2])
            if len(embeddings) == 2:
                similarity = cosine_similarity(
                    embeddings[0:1], 
                    embeddings[1:2]
                )[0][0]
                return float(similarity)
            else:
                return 0.0
        except Exception as e:
            logger.error(f"文本相似度计算失败: {e}")
            return 0.0
    
    def extract_key_phrases(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取文本关键短语（简化版）
        
        Args:
            text: 输入文本
            top_k: 返回的关键短语数量
            
        Returns:
            关键短语列表
        """
        try:
            if self.language == "zh":
                # 中文分词
                words = jieba.cut(text)
                words = [w for w in words if len(w) > 1 and w not in self.stopwords_set]
            else:
                # 英文分词
                words = word_tokenize(text.lower())
                words = [w for w in words if w.isalpha() and w not in self.stopwords_set]
            
            # 简单的词频统计
            from collections import Counter
            word_counts = Counter(words)
            
            # 返回最频繁的词作为关键短语
            return [word for word, count in word_counts.most_common(top_k)]
            
        except Exception as e:
            logger.warning(f"关键短语提取失败: {e}")
            return []
    
    def detect_semantic_shifts(
        self, 
        embeddings: np.ndarray, 
        sensitivity: float = 0.3
    ) -> List[Tuple[int, float]]:
        """
        检测语义转换点
        
        Args:
            embeddings: 语义向量矩阵
            sensitivity: 敏感度参数，越小越敏感
            
        Returns:
            (索引, 变化强度) 的列表
        """
        if len(embeddings) < 3:
            return []
        
        try:
            shifts = []
            
            # 计算连续三个向量的语义变化
            for i in range(1, len(embeddings) - 1):
                # 前后语义相似度
                prev_sim = cosine_similarity(
                    embeddings[i-1:i], 
                    embeddings[i:i+1]
                )[0][0]
                
                next_sim = cosine_similarity(
                    embeddings[i:i+1], 
                    embeddings[i+1:i+2]
                )[0][0]
                
                # 计算语义变化强度
                shift_intensity = abs(prev_sim - next_sim)
                
                if shift_intensity > sensitivity:
                    shifts.append((i, shift_intensity))
            
            # 按变化强度排序
            shifts.sort(key=lambda x: x[1], reverse=True)
            
            return shifts
            
        except Exception as e:
            logger.error(f"语义转换检测失败: {e}")
            return []
