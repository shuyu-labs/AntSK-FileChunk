"""
AntSK semantic chunking package.
"""

from typing import TYPE_CHECKING

__version__ = "1.0.0"
__author__ = "AntSK Team"

__all__ = [
    "SemanticChunker",
    "EnhancedSemanticChunker",
    "ChunkConfig",
    "TextChunk",
    "EmbeddingCache",
]

if TYPE_CHECKING:
    from .enhanced_semantic_chunker import (
        ChunkConfig,
        EmbeddingCache,
        EnhancedSemanticChunker,
        SemanticChunker,
        TextChunk,
    )


def __getattr__(name):
    if name in __all__:
        from .enhanced_semantic_chunker import (
            ChunkConfig,
            EmbeddingCache,
            EnhancedSemanticChunker,
            SemanticChunker,
            TextChunk,
        )

        exports = {
            "SemanticChunker": SemanticChunker,
            "EnhancedSemanticChunker": EnhancedSemanticChunker,
            "ChunkConfig": ChunkConfig,
            "TextChunk": TextChunk,
            "EmbeddingCache": EmbeddingCache,
        }
        return exports[name]

    raise AttributeError(f"module 'antsk_filechunk' has no attribute {name!r}")
