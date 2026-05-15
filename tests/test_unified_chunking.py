import sys
import types
import unittest
from pathlib import Path

import numpy as np


def _install_test_stubs():
    sklearn = types.ModuleType("sklearn")
    metrics = types.ModuleType("sklearn.metrics")
    pairwise = types.ModuleType("sklearn.metrics.pairwise")

    def cosine_similarity(a, b=None):
        left = np.asarray(a, dtype=float)
        right = left if b is None else np.asarray(b, dtype=float)

        if left.ndim == 1:
            left = left.reshape(1, -1)
        if right.ndim == 1:
            right = right.reshape(1, -1)

        left_norm = np.linalg.norm(left, axis=1, keepdims=True)
        right_norm = np.linalg.norm(right, axis=1, keepdims=True)
        left_norm[left_norm == 0] = 1.0
        right_norm[right_norm == 0] = 1.0
        return (left @ right.T) / (left_norm @ right_norm.T)

    pairwise.cosine_similarity = cosine_similarity
    metrics.pairwise = pairwise
    sklearn.metrics = metrics

    sentence_transformers = types.ModuleType("sentence_transformers")

    class FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, **kwargs):
            return np.asarray([[float(index + 1), 1.0] for index, _ in enumerate(texts)])

    sentence_transformers.SentenceTransformer = FakeSentenceTransformer

    nltk = types.ModuleType("nltk")
    nltk.data = types.SimpleNamespace(find=lambda *args, **kwargs: True)
    nltk.download = lambda *args, **kwargs: None
    nltk_corpus = types.ModuleType("nltk.corpus")
    nltk_corpus.stopwords = types.SimpleNamespace(words=lambda language: [])
    nltk_tokenize = types.ModuleType("nltk.tokenize")
    nltk_tokenize.word_tokenize = lambda text: text.split()

    jieba = types.ModuleType("jieba")
    jieba.cut = lambda text: list(text)

    pandas = types.ModuleType("pandas")
    tqdm = types.ModuleType("tqdm")
    tqdm.tqdm = lambda items, *args, **kwargs: items

    docx = types.ModuleType("docx")
    docx_shared = types.ModuleType("docx.shared")
    docx_shared.Inches = lambda value: value
    docx_enum = types.ModuleType("docx.enum")
    docx_enum_text = types.ModuleType("docx.enum.text")
    docx_enum_text.WD_PARAGRAPH_ALIGNMENT = types.SimpleNamespace(CENTER=1)

    fitz = types.ModuleType("fitz")
    fitz.Pixmap = object

    pil = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")
    pil.Image = pil_image

    chardet = types.ModuleType("chardet")
    chardet.detect = lambda data: {"encoding": "utf-8"}

    pptx = types.ModuleType("pptx")
    pptx.Presentation = None
    openpyxl = types.ModuleType("openpyxl")
    openpyxl.load_workbook = None
    xlrd = types.ModuleType("xlrd")

    sys.modules.setdefault("sklearn", sklearn)
    sys.modules.setdefault("sklearn.metrics", metrics)
    sys.modules.setdefault("sklearn.metrics.pairwise", pairwise)
    sys.modules.setdefault("sentence_transformers", sentence_transformers)
    sys.modules.setdefault("nltk", nltk)
    sys.modules.setdefault("nltk.corpus", nltk_corpus)
    sys.modules.setdefault("nltk.tokenize", nltk_tokenize)
    sys.modules.setdefault("jieba", jieba)
    sys.modules.setdefault("pandas", pandas)
    sys.modules.setdefault("tqdm", tqdm)
    sys.modules.setdefault("docx", docx)
    sys.modules.setdefault("docx.shared", docx_shared)
    sys.modules.setdefault("docx.enum", docx_enum)
    sys.modules.setdefault("docx.enum.text", docx_enum_text)
    sys.modules.setdefault("fitz", fitz)
    sys.modules.setdefault("PIL", pil)
    sys.modules.setdefault("PIL.Image", pil_image)
    sys.modules.setdefault("chardet", chardet)
    sys.modules.setdefault("pptx", pptx)
    sys.modules.setdefault("openpyxl", openpyxl)
    sys.modules.setdefault("xlrd", xlrd)


_install_test_stubs()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from antsk_filechunk.enhanced_semantic_chunker import ChunkConfig, SemanticChunker
from antsk_filechunk.unified_document_parser import DocumentContent


class UnifiedChunkingTests(unittest.TestCase):
    def _build_chunker(self, config=None):
        chunker = SemanticChunker.__new__(SemanticChunker)
        chunker.config = config or ChunkConfig(language="zh")
        return chunker

    def test_process_document_content_preserves_markdown_order(self):
        chunker = self._build_chunker()
        document_content = DocumentContent(
            paragraphs=[
                {"content": "第一段文字内容足够长。", "index": 0, "type": "paragraph", "block_index": 0},
                {"content": "第二段文字内容也足够长。", "index": 1, "type": "paragraph", "block_index": 2},
            ],
            tables=[
                {
                    "index": 0,
                    "type": "table",
                    "data": [["列1"], ["值1"]],
                    "markdown": ["| 列1 |", "| --- |", "| 值1 |"],
                }
            ],
            images=[
                {"url": "http://example.com/a.png", "filename": "diagram.png", "type": "image"}
            ],
            metadata={},
            structure={},
            markdown_content=(
                "第一段文字内容足够长。\n\n"
                "| 列1 |\n| --- |\n| 值1 |\n\n"
                "第二段文字内容也足够长。\n\n"
                "![diagram.png](http://example.com/a.png)"
            ),
            file_info={"name": "demo.md", "format": "md"},
        )

        processed_content = chunker._process_document_content_unified(document_content)

        self.assertEqual(
            [element["type"] for element in processed_content["elements"]],
            ["paragraph", "table", "paragraph", "image"],
        )
        self.assertEqual(processed_content["texts"][-1], "[IMAGE_PLACEHOLDER_0]")

    def test_semantic_chunking_unified_uses_sequential_decision(self):
        config = ChunkConfig(
            min_chunk_size=5,
            max_chunk_size=100,
            target_chunk_size=80,
            overlap_ratio=0.0,
            semantic_threshold=0.95,
            language="en",
        )
        chunker = self._build_chunker(config)
        chunker.semantic_analyzer = types.SimpleNamespace(
            find_semantic_boundaries=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not be called"))
        )

        processed_content = {
            "texts": ["alpha topic", "beta topic", "gamma topic"],
            "elements": [
                {"type": "paragraph", "content": "alpha topic", "original_data": {"type": "paragraph"}, "index": 0},
                {"type": "paragraph", "content": "beta topic", "original_data": {"type": "paragraph"}, "index": 1},
                {"type": "paragraph", "content": "gamma topic", "original_data": {"type": "paragraph"}, "index": 2},
            ],
            "element_types": ["paragraph", "paragraph", "paragraph"],
            "markdown_content": "",
        }
        embeddings = np.asarray(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 0.0],
            ]
        )

        chunks = chunker._semantic_chunking_unified(
            processed_content,
            embeddings,
            types.SimpleNamespace(file_info={"name": "demo.txt", "format": "txt"}),
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].paragraph_indices, [0, 1, 2])
        self.assertIn("alpha topic", chunks[0].content)
        self.assertIn("gamma topic", chunks[0].content)


if __name__ == "__main__":
    unittest.main()