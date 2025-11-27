"""
质量评估器模块
评估切片质量和提供优化建议
"""

import logging
from typing import List, Dict, Tuple, Optional
import statistics

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class QualityEvaluator:
    """质量评估器主类"""
    
    def __init__(self, semantic_analyzer):
        """
        初始化质量评估器
        
        Args:
            semantic_analyzer: 语义分析器实例
        """
        self.semantic_analyzer = semantic_analyzer
        self.evaluation_metrics = [
            'coherence',        # 连贯性
            'completeness',     # 完整性
            'length_balance',   # 长度平衡性
            'semantic_density', # 语义密度
            'boundary_quality'  # 边界质量
        ]
    
    def evaluate_chunks(self, chunks: List) -> Dict:
        """
        评估切片质量
        
        Args:
            chunks: 切片列表
            
        Returns:
            质量评估结果
        """
        if not chunks:
            return self._empty_evaluation()
        
        logger.info(f"开始评估 {len(chunks)} 个切片的质量")
        
        try:
            evaluation_results = {}
            
            # 1. 连贯性评估
            coherence_scores = self._evaluate_coherence(chunks)
            evaluation_results['coherence_scores'] = coherence_scores
            evaluation_results['avg_coherence'] = np.mean(coherence_scores)
            
            # 2. 完整性评估
            completeness_scores = self._evaluate_completeness(chunks)
            evaluation_results['completeness_scores'] = completeness_scores
            evaluation_results['avg_completeness'] = np.mean(completeness_scores)
            
            # 3. 长度平衡性评估
            length_balance_score = self._evaluate_length_balance(chunks)
            evaluation_results['length_balance'] = length_balance_score
            
            # 4. 语义密度评估
            semantic_density_scores = self._evaluate_semantic_density(chunks)
            evaluation_results['semantic_density_scores'] = semantic_density_scores
            evaluation_results['avg_semantic_density'] = np.mean(semantic_density_scores)
            
            # 5. 边界质量评估
            boundary_quality_score = self._evaluate_boundary_quality(chunks)
            evaluation_results['boundary_quality'] = boundary_quality_score
            
            # 6. 综合质量分数
            overall_score = self._calculate_overall_score(evaluation_results)
            evaluation_results['overall_score'] = overall_score
            
            # 7. 生成优化建议
            suggestions = self._generate_suggestions(evaluation_results, chunks)
            evaluation_results['suggestions'] = suggestions
            
            logger.info(f"质量评估完成，综合得分: {overall_score:.3f}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return self._empty_evaluation()
    
    def _empty_evaluation(self) -> Dict:
        """返回空的评估结果"""
        return {
            'coherence_scores': [],
            'avg_coherence': 0.0,
            'completeness_scores': [],
            'avg_completeness': 0.0,
            'length_balance': 0.0,
            'semantic_density_scores': [],
            'avg_semantic_density': 0.0,
            'boundary_quality': 0.0,
            'overall_score': 0.0,
            'suggestions': []
        }
    
    def _evaluate_coherence(self, chunks: List) -> List[float]:
        """
        评估每个切片的内部连贯性
        
        Args:
            chunks: 切片列表
            
        Returns:
            连贯性得分列表
        """
        coherence_scores = []
        
        for chunk in chunks:
            try:
                # 使用切片自身的语义得分
                if hasattr(chunk, 'semantic_score') and chunk.semantic_score is not None:
                    coherence_score = chunk.semantic_score
                else:
                    # 重新计算连贯性
                    coherence_score = self._calculate_internal_coherence(chunk.content)
                
                coherence_scores.append(max(0.0, min(1.0, coherence_score)))
                
            except Exception as e:
                logger.warning(f"连贯性评估失败: {e}")
                coherence_scores.append(0.5)  # 默认中等分数
        
        return coherence_scores
    
    def _calculate_internal_coherence(self, content: str) -> float:
        """
        计算文本内部连贯性
        
        Args:
            content: 文本内容
            
        Returns:
            连贯性得分 (0-1)
        """
        try:
            # 将文本分割成句子
            sentences = self._split_into_sentences(content)
            
            if len(sentences) <= 1:
                return 1.0
            
            # 计算句子间的语义相似度
            embeddings = self.semantic_analyzer.compute_embeddings(sentences)
            
            if len(embeddings) < 2:
                return 1.0
            
            # 计算相邻句子的平均相似度
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity(
                    embeddings[i:i+1], 
                    embeddings[i+1:i+2]
                )[0][0]
                similarities.append(sim)
            
            return np.mean(similarities)
            
        except Exception as e:
            logger.warning(f"内部连贯性计算失败: {e}")
            return 0.5
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        import re
        
        # 中文句子分割
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        return sentences
    
    def _evaluate_completeness(self, chunks: List) -> List[float]:
        """
        评估每个切片的完整性
        
        Args:
            chunks: 切片列表
            
        Returns:
            完整性得分列表
        """
        completeness_scores = []
        
        for chunk in chunks:
            try:
                completeness_score = self._calculate_completeness(chunk.content)
                completeness_scores.append(max(0.0, min(1.0, completeness_score)))
            except Exception as e:
                logger.warning(f"完整性评估失败: {e}")
                completeness_scores.append(0.5)
        
        return completeness_scores
    
    def _calculate_completeness(self, content: str) -> float:
        """
        计算切片的完整性
        
        Args:
            content: 文本内容
            
        Returns:
            完整性得分 (0-1)
        """
        # 简化的完整性评估
        score = 1.0
        
        # 检查是否以句号等结尾
        if not content.rstrip().endswith(('。', '.', '！', '!', '？', '?', '；', ';')):
            score -= 0.3
        
        # 检查是否以不完整的句子开头
        first_sentence = content.split('。')[0]
        if len(first_sentence) < 10:  # 过短的开头可能不完整
            score -= 0.2
        
        # 检查是否包含明显的截断标志
        # 只有当这些标志出现在内容末尾时才扣分（表示实际的截断）
        # 而不是出现在内容中间（可能是正常的省略号或引用）
        content_stripped = content.rstrip()
        
        # 强截断指示符 - 只在末尾检查，且需要较高的惩罚
        strong_truncation_indicators = ['(续)', '(未完)', '（续）', '（未完）']
        if any(content_stripped.endswith(indicator) for indicator in strong_truncation_indicators):
            score -= 0.4
        
        # 弱截断指示符 - 在末尾检查，使用较低的惩罚
        # '...' 和 '……' 只有在作为内容的结尾时才可能表示截断
        weak_truncation_indicators = ['...', '……']
        if any(content_stripped.endswith(indicator) for indicator in weak_truncation_indicators):
            # 检查是否可能是对话中的省略号（如果在引号内则不扣分）
            if not self._is_ellipsis_in_dialogue(content_stripped):
                score -= 0.2
        
        # '详见' 作为引用不应该被惩罚，只有在末尾且没有具体说明时才扣分
        if content_stripped.endswith('详见'):
            score -= 0.2
        
        return max(0.1, score)
    
    def _is_ellipsis_in_dialogue(self, content: str) -> bool:
        """
        检查省略号是否出现在对话引号内
        
        Args:
            content: 文本内容
            
        Returns:
            如果省略号在对话中返回True，否则返回False
        """
        # 检查内容末尾是否是以引号+省略号结尾
        # 常见模式: "..."、'...'、"……"、'……'
        dialogue_endings = [
            '"..."', "'...'", '"……"', "'……'",
            '..."', "...'", '……"', "……'",
            '"...', "'...", '"……', "'……"
        ]
        return any(content.endswith(ending) for ending in dialogue_endings)
    
    def _evaluate_length_balance(self, chunks: List) -> float:
        """
        评估切片长度的平衡性
        
        Args:
            chunks: 切片列表
            
        Returns:
            长度平衡性得分 (0-1)
        """
        if not chunks:
            return 0.0
        
        lengths = [len(chunk.content) for chunk in chunks]
        
        if len(lengths) <= 1:
            return 1.0
        
        # 计算长度的变异系数
        mean_length = np.mean(lengths)
        std_length = np.std(lengths)
        
        if mean_length == 0:
            return 0.0
        
        cv = std_length / mean_length  # 变异系数
        
        # 将变异系数转换为得分 (变异系数越小，平衡性越好)
        balance_score = max(0.0, 1.0 - cv)
        
        return balance_score
    
    def _evaluate_semantic_density(self, chunks: List) -> List[float]:
        """
        评估每个切片的语义密度
        
        Args:
            chunks: 切片列表
            
        Returns:
            语义密度得分列表
        """
        density_scores = []
        
        for chunk in chunks:
            try:
                density_score = self._calculate_semantic_density(chunk.content)
                density_scores.append(max(0.0, min(1.0, density_score)))
            except Exception as e:
                logger.warning(f"语义密度评估失败: {e}")
                density_scores.append(0.5)
        
        return density_scores
    
    def _calculate_semantic_density(self, content: str) -> float:
        """
        计算语义密度
        
        Args:
            content: 文本内容
            
        Returns:
            语义密度得分 (0-1)
        """
        try:
            # 简化的语义密度计算
            # 基于信息量和文本长度的比值
            
            # 计算唯一词汇数量
            words = content.split()
            unique_words = set(word.lower() for word in words if word.isalpha())
            
            if not words:
                return 0.0
            
            # 词汇丰富度 (Type-Token Ratio)
            vocabulary_richness = len(unique_words) / len(words)
            
            # 句子长度多样性
            sentences = self._split_into_sentences(content)
            if len(sentences) > 1:
                sentence_lengths = [len(s.split()) for s in sentences]
                length_diversity = np.std(sentence_lengths) / (np.mean(sentence_lengths) + 1e-6)
                length_diversity = min(1.0, length_diversity)  # 归一化
            else:
                length_diversity = 0.0
            
            # 综合密度得分
            density_score = (vocabulary_richness * 0.7 + length_diversity * 0.3)
            
            return density_score
            
        except Exception as e:
            logger.warning(f"语义密度计算失败: {e}")
            return 0.5
    
    def _evaluate_boundary_quality(self, chunks: List) -> float:
        """
        评估切片边界质量
        
        Args:
            chunks: 切片列表
            
        Returns:
            边界质量得分 (0-1)
        """
        if len(chunks) <= 1:
            return 1.0
        
        try:
            boundary_scores = []
            
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i]
                next_chunk = chunks[i + 1]
                
                # 检查边界处的语义断裂程度
                boundary_score = self._calculate_boundary_score(current_chunk, next_chunk)
                boundary_scores.append(boundary_score)
            
            return np.mean(boundary_scores)
            
        except Exception as e:
            logger.warning(f"边界质量评估失败: {e}")
            return 0.5
    
    def _calculate_boundary_score(self, chunk1, chunk2) -> float:
        """
        计算两个切片之间边界的质量
        
        Args:
            chunk1: 第一个切片
            chunk2: 第二个切片
            
        Returns:
            边界质量得分 (0-1)
        """
        try:
            # 获取边界附近的文本
            end_text = chunk1.content[-100:] if len(chunk1.content) > 100 else chunk1.content
            start_text = chunk2.content[:100] if len(chunk2.content) > 100 else chunk2.content
            
            # 计算边界处的语义相似度
            similarity = self.semantic_analyzer.calculate_text_similarity(end_text, start_text)
            
            # 边界质量与相似度负相关（相似度低说明边界好）
            boundary_score = 1.0 - similarity
            
            # 检查是否在合适的位置断开（句子边界等）
            if chunk1.content.rstrip().endswith(('。', '.', '！', '!', '？', '?')):
                boundary_score += 0.2
            
            if chunk2.content.lstrip().startswith(('第', '章', '节', '一', '二', '三', '四', '五')):
                boundary_score += 0.1
            
            return min(1.0, boundary_score)
            
        except Exception as e:
            logger.warning(f"边界得分计算失败: {e}")
            return 0.5
    
    def _calculate_overall_score(self, evaluation_results: Dict) -> float:
        """
        计算综合质量得分
        
        Args:
            evaluation_results: 评估结果字典
            
        Returns:
            综合得分 (0-1)
        """
        try:
            # 权重配置
            weights = {
                'avg_coherence': 0.3,
                'avg_completeness': 0.25,
                'length_balance': 0.15,
                'avg_semantic_density': 0.15,
                'boundary_quality': 0.15
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for metric, weight in weights.items():
                if metric in evaluation_results and evaluation_results[metric] is not None:
                    weighted_score += evaluation_results[metric] * weight
                    total_weight += weight
            
            if total_weight > 0:
                return weighted_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"综合得分计算失败: {e}")
            return 0.5
    
    def _generate_suggestions(self, evaluation_results: Dict, chunks: List) -> List[str]:
        """
        根据评估结果生成优化建议
        
        Args:
            evaluation_results: 评估结果
            chunks: 切片列表
            
        Returns:
            建议列表
        """
        suggestions = []
        
        try:
            # 连贯性建议
            if evaluation_results.get('avg_coherence', 0) < 0.6:
                suggestions.append("建议调整语义阈值，提高切片内部连贯性")
            
            # 完整性建议
            if evaluation_results.get('avg_completeness', 0) < 0.7:
                suggestions.append("建议优化切片边界，确保在句子或段落边界处切分")
            
            # 长度平衡性建议
            if evaluation_results.get('length_balance', 0) < 0.6:
                lengths = [len(chunk.content) for chunk in chunks]
                if max(lengths) / (min(lengths) + 1) > 3:
                    suggestions.append("存在长度差异过大的切片，建议分割长切片或合并短切片")
            
            # 语义密度建议
            if evaluation_results.get('avg_semantic_density', 0) < 0.4:
                suggestions.append("部分切片语义密度较低，可能包含过多重复或无关内容")
            
            # 边界质量建议
            if evaluation_results.get('boundary_quality', 0) < 0.6:
                suggestions.append("建议提高语义阈值或调整重叠比例，改善切片边界质量")
            
            # 综合建议
            overall_score = evaluation_results.get('overall_score', 0)
            if overall_score < 0.5:
                suggestions.append("整体切片质量较低，建议重新调整配置参数")
            elif overall_score > 0.8:
                suggestions.append("切片质量良好，可以用于后续处理")
            
        except Exception as e:
            logger.warning(f"建议生成失败: {e}")
            suggestions.append("评估过程中出现异常，建议检查输入数据")
        
        return suggestions
    
    def generate_quality_report(self, evaluation_results: Dict, chunks: List) -> str:
        """
        生成质量评估报告
        
        Args:
            evaluation_results: 评估结果
            chunks: 切片列表
            
        Returns:
            质量报告字符串
        """
        report = []
        
        report.append("=" * 50)
        report.append("文本切片质量评估报告")
        report.append("=" * 50)
        
        # 基本统计
        report.append(f"切片数量: {len(chunks)}")
        if chunks:
            lengths = [len(chunk.content) for chunk in chunks]
            report.append(f"平均长度: {np.mean(lengths):.1f} 字符")
            report.append(f"长度范围: {min(lengths)} - {max(lengths)} 字符")
        
        report.append("")
        
        # 质量指标
        report.append("质量指标:")
        report.append(f"  连贯性得分: {evaluation_results.get('avg_coherence', 0):.3f}")
        report.append(f"  完整性得分: {evaluation_results.get('avg_completeness', 0):.3f}")
        report.append(f"  长度平衡性: {evaluation_results.get('length_balance', 0):.3f}")
        report.append(f"  语义密度: {evaluation_results.get('avg_semantic_density', 0):.3f}")
        report.append(f"  边界质量: {evaluation_results.get('boundary_quality', 0):.3f}")
        report.append(f"  综合得分: {evaluation_results.get('overall_score', 0):.3f}")
        
        report.append("")
        
        # 优化建议
        suggestions = evaluation_results.get('suggestions', [])
        if suggestions:
            report.append("优化建议:")
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"  {i}. {suggestion}")
        else:
            report.append("当前切片质量良好，无需特殊优化。")
        
        report.append("")
        report.append("=" * 50)
        
        return "\n".join(report)
