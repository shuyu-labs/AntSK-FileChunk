"""
AntSK 语义文本切片服务
====================================

基于语义理解的智能文本切片工具，支持PDF和Word文档的语义切片处理。

主要功能：
- 段落级语义切片，避免简单按长度切分
- 智能文档解析，支持PDF和Word格式
- 自适应切片大小，平衡语义完整性和处理效率
- 质量评估体系，提供优化建议

增强版功能（EnhancedSemanticChunker）：
- 🧠 增强语义连贯性计算：位置权重 + 趋势分析
- 💾 高效缓存机制：LRU策略 + TTL管理
- 🛡️ 完善异常处理：降级策略 + 边界情况处理

基础使用示例：
    from antsk_filechunk import SemanticChunker
    
    chunker = SemanticChunker()
    chunks = chunker.process_file("document.pdf")
    
    for chunk in chunks:
        print(f"Content: {chunk.content}")
        print(f"Score: {chunk.semantic_score}")

增强版使用示例：
    from antsk_filechunk import EnhancedSemanticChunker, ChunkConfig
    
    config = ChunkConfig(target_chunk_size=1000, semantic_threshold=0.7)
    chunker = EnhancedSemanticChunker(config=config, cache_size=500, enable_fallback=True)
    chunks = chunker.process_text_enhanced(text, use_cache=True)
    
    # 配置增强功能
    chunker.configure_coherence(position_weight_enabled=True, trend_analysis_enabled=True)
    
    # 监控系统状态
    health = chunker.health_check()
    stats = chunker.get_comprehensive_stats()
"""

__version__ = "1.0.0"
__author__ = "AntSK Team"

from .enhanced_semantic_chunker import SemanticChunker, ChunkConfig, TextChunk, EnhancedSemanticChunker, EmbeddingCache

__all__ = ["SemanticChunker", "EnhancedSemanticChunker", "ChunkConfig", "TextChunk", "EmbeddingCache"]
