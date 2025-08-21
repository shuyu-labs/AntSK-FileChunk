"""
测试配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 测试数据目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_DATA_DIR = project_root / "data" / "sample"

@pytest.fixture
def sample_text():
    """提供示例文本"""
    return """
    人工智能发展历程与现状分析

    第一章 人工智能的起源与发展

    人工智能（Artificial Intelligence，简称AI）是计算机科学的一个重要分支，
    旨在开发能够执行通常需要人类智能的任务的计算机系统。

    第二章 机器学习的兴起

    20世纪80年代以来，机器学习逐渐成为AI研究的核心。
    机器学习是一种让计算机系统能够从数据中自动学习和改进性能的方法。

    第三章 深度学习革命

    2006年Geoffrey Hinton等人提出深度信念网络，标志着深度学习时代的开始。
    深度学习基于人工神经网络，特别是具有多个隐藏层的深度神经网络。
    """

@pytest.fixture
def temp_file(tmp_path, sample_text):
    """创建临时测试文件"""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text(sample_text, encoding='utf-8')
    return file_path
