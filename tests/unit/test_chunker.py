"""
语义文本切片服务单元测试
"""

import unittest
import tempfile
import json
from pathlib import Path

from src.antsk_filechunk.core.enhanced_semantic_chunker import SemanticChunker, ChunkConfig, TextChunk


class TestSemanticChunker(unittest.TestCase):
    """语义切片器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.config = ChunkConfig(
            min_chunk_size=50,
            max_chunk_size=300,
            target_chunk_size=150,
            semantic_threshold=0.7,
            language="zh"
        )
        self.chunker = SemanticChunker(self.config)
        
        self.sample_text = """
        这是关于人工智能的第一段内容。人工智能是计算机科学的一个重要分支，
        致力于研究如何让机器具备智能行为。

        第二段讨论机器学习技术。机器学习是人工智能的核心技术之一，
        它使计算机能够从数据中学习规律，而不需要明确编程。

        第三段转向深度学习话题。深度学习基于人工神经网络，
        通过多层网络结构学习复杂的数据特征。

        最后一段总结AI的应用前景。人工智能技术正在各个领域发挥重要作用，
        从医疗健康到自动驾驶，AI正在改变我们的生活方式。
        """
    
    def test_basic_chunking(self):
        """测试基础切片功能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = Path(f.name)
        
        try:
            chunks = self.chunker.process_file(temp_path)
            
            # 验证基本属性
            self.assertGreater(len(chunks), 0, "应该生成至少一个切片")
            
            for chunk in chunks:
                self.assertIsInstance(chunk, TextChunk, "应该返回TextChunk对象")
                self.assertGreater(len(chunk.content), 0, "切片内容不应为空")
                self.assertGreaterEqual(chunk.semantic_score, 0, "语义得分应该非负")
                self.assertLessEqual(chunk.semantic_score, 1, "语义得分应该不超过1")
                self.assertGreater(chunk.token_count, 0, "Token数应该大于0")
                
        finally:
            temp_path.unlink()
    
    def test_chunk_size_constraints(self):
        """测试切片大小约束"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text * 3)  # 重复文本增加长度
            temp_path = Path(f.name)
        
        try:
            chunks = self.chunker.process_file(temp_path)
            
            for chunk in chunks:
                # 检查大小约束（允许一定误差）
                chunk_length = len(chunk.content)
                self.assertLessEqual(
                    chunk_length, 
                    self.config.max_chunk_size + 100,  # 允许100字符误差
                    f"切片长度 {chunk_length} 超过最大限制 {self.config.max_chunk_size}"
                )
                
        finally:
            temp_path.unlink()
    
    def test_empty_input(self):
        """测试空输入"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            chunks = self.chunker.process_file(temp_path)
            self.assertEqual(len(chunks), 0, "空输入应该返回空切片列表")
            
        finally:
            temp_path.unlink()
    
    def test_single_paragraph(self):
        """测试单段落输入"""
        single_para = "这是一个单独的段落，用于测试单段落的切片行为。虽然内容不长，但应该能够正常处理。"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(single_para)
            temp_path = Path(f.name)
        
        try:
            chunks = self.chunker.process_file(temp_path)
            self.assertGreaterEqual(len(chunks), 1, "单段落应该生成至少一个切片")
            
        finally:
            temp_path.unlink()
    
    def test_statistics(self):
        """测试统计信息"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = Path(f.name)
        
        try:
            chunks = self.chunker.process_file(temp_path)
            stats = self.chunker.get_chunking_statistics(chunks)
            
            # 验证统计信息
            self.assertEqual(stats['total_chunks'], len(chunks))
            self.assertGreater(stats['avg_length'], 0)
            self.assertGreaterEqual(stats['min_length'], 0)
            self.assertGreaterEqual(stats['max_length'], stats['min_length'])
            self.assertGreaterEqual(stats['avg_semantic_score'], 0)
            self.assertLessEqual(stats['avg_semantic_score'], 1)
            
            # 验证长度分布
            dist = stats['length_distribution']
            total_dist = sum(dist.values())
            self.assertEqual(total_dist, len(chunks), "长度分布总数应该等于切片数量")
            
        finally:
            temp_path.unlink()
    
    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # 处理并保存
            chunks = self.chunker.process_file(temp_path)
            self.chunker.save_chunks(chunks, output_path)
            
            # 验证文件存在
            self.assertTrue(output_path.exists(), "输出文件应该存在")
            
            # 加载并验证
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn('chunks', data, "保存的数据应该包含chunks字段")
            self.assertIn('statistics', data, "保存的数据应该包含statistics字段")
            self.assertIn('config', data, "保存的数据应该包含config字段")
            
            # 验证切片数据
            saved_chunks = data['chunks']
            self.assertEqual(len(saved_chunks), len(chunks), "保存的切片数量应该一致")
            
            for saved_chunk in saved_chunks:
                self.assertIn('content', saved_chunk)
                self.assertIn('semantic_score', saved_chunk)
                self.assertIn('token_count', saved_chunk)
                
        finally:
            temp_path.unlink()
            if output_path.exists():
                output_path.unlink()


class TestChunkConfig(unittest.TestCase):
    """切片配置测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ChunkConfig()
        
        # 验证默认值
        self.assertEqual(config.min_chunk_size, 200)
        self.assertEqual(config.max_chunk_size, 1500)
        self.assertEqual(config.target_chunk_size, 800)
        self.assertEqual(config.overlap_ratio, 0.1)
        self.assertEqual(config.semantic_threshold, 0.7)
        self.assertEqual(config.language, "zh")
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ChunkConfig(
            min_chunk_size=100,
            max_chunk_size=1000,
            target_chunk_size=500,
            semantic_threshold=0.8,
            language="en"
        )
        
        self.assertEqual(config.min_chunk_size, 100)
        self.assertEqual(config.max_chunk_size, 1000)
        self.assertEqual(config.target_chunk_size, 500)
        self.assertEqual(config.semantic_threshold, 0.8)
        self.assertEqual(config.language, "en")


class TestTextChunk(unittest.TestCase):
    """文本切片测试类"""
    
    def test_chunk_creation(self):
        """测试切片创建"""
        chunk = TextChunk(
            content="这是测试内容",
            start_pos=0,
            end_pos=7,
            semantic_score=0.85,
            token_count=10,
            paragraph_indices=[0, 1],
            chunk_type="content"
        )
        
        self.assertEqual(chunk.content, "这是测试内容")
        self.assertEqual(chunk.start_pos, 0)
        self.assertEqual(chunk.end_pos, 7)
        self.assertEqual(chunk.semantic_score, 0.85)
        self.assertEqual(chunk.token_count, 10)
        self.assertEqual(chunk.paragraph_indices, [0, 1])
        self.assertEqual(chunk.chunk_type, "content")
        self.assertIsInstance(chunk.metadata, dict)
    
    def test_chunk_with_metadata(self):
        """测试带元数据的切片"""
        metadata = {"source": "test", "page": 1}
        
        chunk = TextChunk(
            content="测试内容",
            start_pos=0,
            end_pos=4,
            semantic_score=0.9,
            token_count=5,
            paragraph_indices=[0],
            metadata=metadata
        )
        
        self.assertEqual(chunk.metadata["source"], "test")
        self.assertEqual(chunk.metadata["page"], 1)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestSemanticChunker,
        TestChunkConfig,
        TestTextChunk
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
