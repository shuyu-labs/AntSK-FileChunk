#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 验证AntSK文件切片功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.antsk_filechunk import SemanticChunker, ChunkConfig

def test_text_processing():
    """测试文本处理功能"""
    print("=" * 50)
    print("🧪 测试文本处理功能")
    print("=" * 50)
    
    # 创建测试文本
    test_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于开发能够模拟、延伸和扩展人类智能的理论、方法、技术及应用系统。
    
    机器学习是人工智能的核心技术之一，通过算法使计算机能够从数据中学习并做出决策或预测。深度学习作为机器学习的一个子集，使用神经网络来处理复杂的模式识别任务。
    
    自然语言处理（NLP）是人工智能的另一个重要分支，专注于使计算机能够理解、解释和生成人类语言。现代NLP系统可以进行文本翻译、情感分析、文本摘要等多种任务。
    
    计算机视觉技术使机器能够从图像或视频中提取信息和理解视觉内容。这项技术广泛应用于自动驾驶、医学影像分析、人脸识别等领域。
    
    随着技术的不断发展，人工智能正在改变我们的生活和工作方式，从智能手机助手到自动驾驶汽车，从推荐系统到智能制造，AI技术无处不在。
    """
    
    try:
        # 创建配置
        config = ChunkConfig(
            min_chunk_size=100,
            max_chunk_size=500,
            target_chunk_size=300,
            language="zh"
        )
        
        # 创建切片器
        print("📝 正在初始化语义切片器...")
        chunker = SemanticChunker(config)
        
        # 处理文本
        print("🔄 正在处理文本...")
        chunks = chunker.process_text(test_text)
        
        # 显示结果
        print(f"✅ 处理完成！共生成 {len(chunks)} 个切片")
        print("=" * 50)
        
        for i, chunk in enumerate(chunks, 1):
            print(f"切片 {i}:")
            print(f"  内容长度: {len(chunk.content)} 字符")
            print(f"  Token数量: {chunk.token_count}")
            print(f"  语义得分: {chunk.semantic_score:.3f}")
            print(f"  内容预览: {chunk.content[:100]}...")
            print("-" * 30)
        
        print("🎉 测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 AntSK 文件切片服务 - 功能测试")
    
    # 测试文本处理
    success = test_text_processing()
    
    if success:
        print("\n✅ 所有测试通过！服务可以正常启动。")
        print("\n📋 下一步操作:")
        print("1. 运行 'python start_server.py' 启动API服务")
        print("2. 访问 http://localhost:8000 查看测试页面")
        print("3. 访问 http://localhost:8000/docs 查看API文档")
    else:
        print("\n❌ 测试失败！请检查环境配置。")
        sys.exit(1)

if __name__ == "__main__":
    main()
