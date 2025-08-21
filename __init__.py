"""
AntSK 语义文本切片服务
基于语义理解的智能文档切片工具

主要功能:
- 支持Word和PDF文档解析
- 基于语义相似度的智能切片
- 自适应切片大小调整
- 切片质量评估和优化建议
- 多语言支持 (中文/英文)
"""

from src.antsk_filechunk.core.enhanced_semantic_chunker import SemanticChunker, ChunkConfig, TextChunk, EnhancedSemanticChunker
from src.antsk_filechunk.parsers.document_parser import DocumentParser, DocumentContent
from src.antsk_filechunk.analyzers.semantic_analyzer import SemanticAnalyzer
from src.antsk_filechunk.optimizers.chunk_optimizer import ChunkOptimizer
from src.antsk_filechunk.evaluators.quality_evaluator import QualityEvaluator

__version__ = "1.0.0"
__author__ = "AntSK Team"
__email__ = "support@antsk.com"

__all__ = [
    # 主要类
    "SemanticChunker",
    "EnhancedSemanticChunker",
    "ChunkConfig", 
    "TextChunk",
    
    # 组件类
    "DocumentParser",
    "DocumentContent",
    "SemanticAnalyzer",
    "ChunkOptimizer",
    "QualityEvaluator",
]

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": "基于语义理解的智能文档切片工具",
    "features": [
        "Word/PDF文档解析",
        "语义相似度分析",
        "智能切片优化",
        "质量评估系统",
        "多语言支持"
    ]
}

def get_version():
    """获取版本信息"""
    return __version__

def get_version_info():
    """获取详细版本信息"""
    return VERSION_INFO

# 快速创建实例的便捷函数
def create_chunker(
    min_size: int = 200,
    max_size: int = 1500, 
    target_size: int = 800,
    semantic_threshold: float = 0.7,
    language: str = "zh",
    model_name: str = "all-MiniLM-L6-v2"
) -> SemanticChunker:
    """
    快速创建语义切片器实例
    
    Args:
        min_size: 最小切片大小
        max_size: 最大切片大小  
        target_size: 目标切片大小
        semantic_threshold: 语义相似度阈值
        language: 语言设置
        model_name: 语义模型名称
        
    Returns:
        配置好的SemanticChunker实例
    """
    config = ChunkConfig(
        min_chunk_size=min_size,
        max_chunk_size=max_size,
        target_chunk_size=target_size,
        semantic_threshold=semantic_threshold,
        language=language
    )
    
    return SemanticChunker(config=config, model_name=model_name)

# 预设配置
PRESET_CONFIGS = {
    "default": ChunkConfig(),
    
    "small_chunks": ChunkConfig(
        min_chunk_size=100,
        max_chunk_size=500,
        target_chunk_size=300,
        semantic_threshold=0.8
    ),
    
    "large_chunks": ChunkConfig(
        min_chunk_size=500,
        max_chunk_size=2000,
        target_chunk_size=1200,
        semantic_threshold=0.6
    ),
    
    "high_precision": ChunkConfig(
        min_chunk_size=200,
        max_chunk_size=800,
        target_chunk_size=500,
        semantic_threshold=0.85,
        overlap_ratio=0.2
    ),
    
    "fast_processing": ChunkConfig(
        min_chunk_size=300,
        max_chunk_size=1200,
        target_chunk_size=800,
        semantic_threshold=0.6,
        overlap_ratio=0.05
    )
}

def create_preset_chunker(preset_name: str, model_name: str = "all-MiniLM-L6-v2") -> SemanticChunker:
    """
    使用预设配置创建切片器
    
    Args:
        preset_name: 预设配置名称 ('default', 'small_chunks', 'large_chunks', 'high_precision', 'fast_processing')
        model_name: 语义模型名称
        
    Returns:
        配置好的SemanticChunker实例
    """
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"未知的预设配置: {preset_name}，可用配置: {list(PRESET_CONFIGS.keys())}")
    
    config = PRESET_CONFIGS[preset_name]
    return SemanticChunker(config=config, model_name=model_name)
