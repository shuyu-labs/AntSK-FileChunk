import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from antsk_filechunk.semantic_analyzer import SemanticAnalyzer


class FakeSentenceTransformer:
    init_calls = 0
    encode_calls = 0

    def __init__(self, model_name):
        self.model_name = model_name
        FakeSentenceTransformer.init_calls += 1

    def encode(self, texts, show_progress_bar=False, batch_size=32, normalize_embeddings=True):
        FakeSentenceTransformer.encode_calls += 1
        rows = []
        for text in texts:
            base = float(len(text) or 1)
            embedding = np.array([base, base + 1, base + 2, base + 3], dtype=float)
            if normalize_embeddings:
                embedding = embedding / np.linalg.norm(embedding)
            rows.append(embedding)
        return np.asarray(rows)


class SemanticAnalyzerCacheTests(unittest.TestCase):
    def setUp(self):
        SemanticAnalyzer.clear_caches()
        FakeSentenceTransformer.init_calls = 0
        FakeSentenceTransformer.encode_calls = 0

    @patch("antsk_filechunk.semantic_analyzer.SentenceTransformer", FakeSentenceTransformer)
    def test_model_instances_are_reused(self):
        SemanticAnalyzer(model_name="mock-model", language="zh")
        SemanticAnalyzer(model_name="mock-model", language="zh")
        self.assertEqual(FakeSentenceTransformer.init_calls, 1)

    @patch("antsk_filechunk.semantic_analyzer.SentenceTransformer", FakeSentenceTransformer)
    def test_embedding_cache_deduplicates_texts(self):
        analyzer = SemanticAnalyzer(model_name="mock-model", language="zh")

        first_result = analyzer.compute_embeddings(["alpha", "beta", "alpha"])
        second_result = analyzer.compute_embeddings(["alpha", "beta"])

        self.assertEqual(FakeSentenceTransformer.encode_calls, 1)
        self.assertEqual(first_result.shape, (3, 4))
        self.assertEqual(second_result.shape, (2, 4))
        np.testing.assert_allclose(first_result[0], first_result[2])
        np.testing.assert_allclose(first_result[0], second_result[0])


if __name__ == "__main__":
    unittest.main()
