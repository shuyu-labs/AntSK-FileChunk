"""
Tests for the quality_evaluator module.
Tests the improved completeness calculation logic (Issue #3).
"""

import unittest
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from antsk_filechunk.quality_evaluator import QualityEvaluator


class MockSemanticAnalyzer:
    """Mock semantic analyzer for testing."""
    
    def compute_embeddings(self, texts):
        import numpy as np
        return np.random.rand(len(texts), 384)
    
    def calculate_text_similarity(self, text1, text2):
        return 0.5


class TestCompletenessCalculation(unittest.TestCase):
    """Tests for the _calculate_completeness method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = QualityEvaluator(MockSemanticAnalyzer())
    
    def test_normal_sentence_with_period(self):
        """Normal sentence ending with period should have high completeness."""
        content = "这是一个正常的句子。"
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.7, "Normal sentence with period should score >= 0.7")
    
    def test_normal_sentence_without_period(self):
        """Sentence without period should have lower completeness."""
        content = "这是一个正常的句子"
        score = self.evaluator._calculate_completeness(content)
        self.assertLess(score, 0.8, "Sentence without period should score < 0.8")
    
    def test_ellipsis_in_middle_not_penalized(self):
        """Ellipsis in the middle of content should not be heavily penalized (Issue #3)."""
        content = "他沉默了一会儿……然后继续说话。"
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.9, "Ellipsis in middle should not be penalized")
    
    def test_xiangjian_in_middle_not_penalized(self):
        """'详见' in the middle of content should not be penalized (Issue #3)."""
        content = "详见第二章的内容。"
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.7, "'详见' in middle should not be penalized")
    
    def test_ellipsis_in_dialogue(self):
        """Ellipsis in dialogue should be recognized and not heavily penalized."""
        content = '小明说："你好..."'
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.6, "Ellipsis in dialogue should not be heavily penalized")
    
    def test_actual_truncation_with_xu(self):
        """Content ending with (续) should be penalized."""
        content = "(续)"
        score = self.evaluator._calculate_completeness(content)
        self.assertLessEqual(score, 0.2, "Content ending with (续) should be penalized")
    
    def test_actual_truncation_with_weiwan(self):
        """Content ending with (未完) should be penalized."""
        content = "(未完)"
        score = self.evaluator._calculate_completeness(content)
        self.assertLessEqual(score, 0.2, "Content ending with (未完) should be penalized")
    
    def test_actual_truncation_with_ellipsis_at_end(self):
        """Content ending with ellipsis (not in dialogue) should be penalized."""
        content = "这段话未完..."
        score = self.evaluator._calculate_completeness(content)
        self.assertLessEqual(score, 0.7, "Content ending with ellipsis should be penalized")
    
    def test_xiangjian_at_end(self):
        """Content ending with '详见' should be penalized."""
        content = "更多内容详见"
        score = self.evaluator._calculate_completeness(content)
        self.assertLessEqual(score, 0.5, "Content ending with '详见' should be penalized")
    
    def test_xiangjian_with_reference(self):
        """'详见' followed by a reference should not be penalized."""
        content = "参考文档详见附录A。"
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.7, "'详见' with reference should not be penalized")
    
    def test_dialogue_with_ellipsis_in_quotes(self):
        """Dialogue ending with ellipsis inside quotes should be recognized."""
        content = '他说："你想想..."'
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.6, "Dialogue with ellipsis in quotes should score >= 0.6")
    
    def test_long_complete_paragraph(self):
        """Long complete paragraph should have high completeness."""
        content = "这是一个很长的正常段落，描述了一些普通的内容，没有任何截断标志，应该获得较高的完整性分数。"
        score = self.evaluator._calculate_completeness(content)
        self.assertGreaterEqual(score, 0.9, "Long complete paragraph should score >= 0.9")


class TestIsEllipsisInDialogue(unittest.TestCase):
    """Tests for the _is_ellipsis_in_dialogue helper method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = QualityEvaluator(MockSemanticAnalyzer())
    
    def test_ellipsis_in_double_quotes(self):
        """Ellipsis inside double quotes should be recognized."""
        content = '他说："你好..."'
        self.assertTrue(self.evaluator._is_ellipsis_in_dialogue(content))
    
    def test_ellipsis_not_in_quotes(self):
        """Ellipsis not in quotes should not be recognized as dialogue."""
        content = "这段话未完..."
        self.assertFalse(self.evaluator._is_ellipsis_in_dialogue(content))
    
    def test_chinese_ellipsis_in_quotes(self):
        """Chinese ellipsis (……) inside quotes should be recognized."""
        content = '他说："你好……"'
        self.assertTrue(self.evaluator._is_ellipsis_in_dialogue(content))


if __name__ == '__main__':
    unittest.main()
