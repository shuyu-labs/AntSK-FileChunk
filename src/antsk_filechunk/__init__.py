"""
AntSK 语义文本切片服务
====================================

基于语义理解的智能文本切片工具，支持PDF和Word文档的语义切片处理。

主要功能：
- 段落级语义切片，避免简单按长度切分
- 智能文档解析，支持PDF和Word格式
- 自适应切片大小，平衡语义完整性和处理效率
- 质量评估体系，提供优化建议

使用示例：
    from antsk_filechunk import SemanticChunker
    
    chunker = SemanticChunker()
    chunks = chunker.process_file("document.pdf")
    
    for chunk in chunks:
        print(f"Content: {chunk.content}")
        print(f"Score: {chunk.semantic_score}")
"""

__version__ = "1.0.0"
__author__ = "AntSK Team"

from .core.semantic_chunker import SemanticChunker, ChunkConfig, TextChunk

__all__ = ["SemanticChunker", "ChunkConfig", "TextChunk"]
