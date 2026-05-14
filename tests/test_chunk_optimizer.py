import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from antsk_filechunk.chunk_optimizer import ChunkOptimizer
from antsk_filechunk.enhanced_semantic_chunker import ChunkConfig, TextChunk


class ChunkOptimizerTests(unittest.TestCase):
    def setUp(self):
        self.config = ChunkConfig(
            min_chunk_size=1,
            max_chunk_size=12,
            target_chunk_size=6,
            overlap_ratio=0.0,
            language="en",
        )
        self.optimizer = ChunkOptimizer(self.config)

    def test_force_split_chunk_uses_valid_textchunk_import(self):
        chunk = TextChunk(
            content="alpha beta gamma delta",
            start_pos=0,
            end_pos=22,
            semantic_score=0.8,
            token_count=4,
            paragraph_indices=[0],
            chunk_type="content",
            metadata={},
        )

        sub_chunks = self.optimizer._force_split_chunk(chunk)

        self.assertGreater(len(sub_chunks), 1)
        self.assertTrue(all(isinstance(item, TextChunk) for item in sub_chunks))

    def test_post_process_chunks_uses_contiguous_positions(self):
        chunks = [
            TextChunk(
                content="abc",
                start_pos=10,
                end_pos=13,
                semantic_score=0.9,
                token_count=1,
                paragraph_indices=[0],
                metadata={},
            ),
            TextChunk(
                content="defgh",
                start_pos=30,
                end_pos=35,
                semantic_score=0.8,
                token_count=1,
                paragraph_indices=[1],
                metadata={},
            ),
        ]

        processed = self.optimizer._post_process_chunks(chunks)

        self.assertEqual(processed[0].start_pos, 0)
        self.assertEqual(processed[0].end_pos, 3)
        self.assertEqual(processed[1].start_pos, 3)
        self.assertEqual(processed[1].end_pos, 8)


if __name__ == "__main__":
    unittest.main()
