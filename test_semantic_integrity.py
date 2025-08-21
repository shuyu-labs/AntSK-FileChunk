#!/usr/bin/env python3
"""
测试语义完整性保护功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from antsk_filechunk.core.semantic_chunker import SemanticChunker, ChunkConfig

def test_semantic_integrity():
    """测试语义完整性是否得到保护"""
    
    # 创建有明显语义转换的测试文本
    test_text = """
    机器学习是人工智能的核心技术之一。它通过算法让计算机从数据中学习模式和规律。监督学习需要标注数据来训练模型，而无监督学习则可以发现数据中的隐藏结构。深度学习作为机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。
    
    卷积神经网络在图像识别方面表现出色。它通过卷积层提取图像特征，池化层减少参数数量，最后通过全连接层进行分类。ResNet、VGG、AlexNet等经典架构为计算机视觉的发展奠定了基础。目标检测和语义分割是计算机视觉的重要应用场景。
    
    自然语言处理让计算机能够理解人类语言。从词袋模型到Word2Vec，再到BERT和GPT系列模型，NLP技术经历了巨大的发展。预训练语言模型通过在大规模文本数据上学习，获得了强大的语言理解和生成能力。
    
    强化学习解决的是决策问题。智能体通过与环境交互，学习最优的行动策略。Q-learning、策略梯度、Actor-Critic等方法是强化学习的核心算法。AlphaGo和OpenAI Five展示了强化学习在复杂游戏中的威力。
    
    现在让我们转到一个完全不同的话题：烹饪艺术。
    
    中式烹饪有着悠久的历史和丰富的技巧。炒、蒸、煮、炸、炖是中式烹饪的基本方法。川菜以麻辣著称，粤菜注重原汁原味，鲁菜历史悠久，苏菜精致清淡。每个地区的菜系都有其独特的特色和文化内涵。
    
    食材的选择和处理是烹饪的关键。新鲜的食材是美味菜肴的基础。不同的食材需要不同的处理方法：肉类需要去腥，蔬菜需要保持脆嫩，海鲜要保持鲜美。调料的搭配也至关重要，盐、糖、醋、生抽、老抽等基础调料的合理使用能让菜肴更加美味。
    
    再次转换话题：太空探索的意义。
    
    人类对太空的探索始于20世纪中叶。从第一颗人造卫星到载人航天，从月球登陆到火星探测，人类不断挑战着太空的边界。国际空间站是人类在太空中的重要据点，为科学研究提供了宝贵的平台。
    
    太空探索不仅推动了科技发展，也激发了人类的想象力。GPS导航、卫星通信、气象预报等技术都源于太空探索。未来的太空旅游和移民计划可能会彻底改变人类的生活方式。
    """
    
    print("=== 语义完整性保护测试 ===\n")
    
    # 使用默认配置
    print("1. 使用标准语义保护配置:")
    chunker = SemanticChunker()
    chunks = chunker.process_text(test_text)
    
    print(f"生成切片数量: {len(chunks)}\n")
    
    for i, chunk in enumerate(chunks):
        print(f"切片 {i+1}:")
        print(f"长度: {len(chunk.content)} 字符")
        print(f"语义得分: {chunk.semantic_score:.3f}")
        print("内容:")
        print(chunk.content)
        print("-" * 80)
    
    # 检查语义边界是否合理
    print("\n2. 语义边界分析:")
    topics = [
        "机器学习/深度学习/计算机视觉/自然语言处理/强化学习",
        "烹饪艺术",
        "太空探索"
    ]
    
    for i, chunk in enumerate(chunks):
        content = chunk.content
        topic_found = []
        if any(word in content for word in ["机器学习", "深度学习", "神经网络", "算法", "人工智能", "强化学习"]):
            topic_found.append("人工智能技术")
        if any(word in content for word in ["烹饪", "菜系", "食材", "调料", "川菜", "粤菜"]):
            topic_found.append("烹饪艺术")  
        if any(word in content for word in ["太空", "航天", "卫星", "火星", "宇宙"]):
            topic_found.append("太空探索")
        
        print(f"切片 {i+1} 包含主题: {', '.join(topic_found) if topic_found else '未识别主题'}")
    
    # 使用更严格的语义保护配置
    print("\n3. 使用更严格的语义保护配置:")
    config = ChunkConfig(
        min_chunk_size=300,
        max_chunk_size=2000,  
        target_chunk_size=1000,
        semantic_threshold=0.8,  # 更高的阈值，更严格的语义保护
        paragraph_merge_threshold=0.9
    )
    
    chunker_strict = SemanticChunker(config)
    chunks_strict = chunker_strict.process_text(test_text)
    
    print(f"严格配置生成切片数量: {len(chunks_strict)}\n")
    
    for i, chunk in enumerate(chunks_strict):
        print(f"严格切片 {i+1}:")
        print(f"长度: {len(chunk.content)} 字符")
        print(f"语义得分: {chunk.semantic_score:.3f}")
        print("内容预览:", chunk.content[:150] + "...")
        print("-" * 60)

def test_semantic_boundary_detection():
    """测试语义边界检测功能"""
    
    print("\n=== 语义边界检测测试 ===\n")
    
    # 创建有清晰语义分界的文本
    boundary_text = """
    第一部分：关于编程语言的讨论。Python是一种高级编程语言，语法简洁易读。它支持面向对象、函数式和过程式编程范式。Python有丰富的标准库和第三方库生态。
    
    JavaScript是Web开发的核心语言。它既可以用于前端开发，也可以通过Node.js用于后端开发。ES6引入了许多新特性，使JavaScript更加现代化。
    
    第二部分：关于运动健身的内容。跑步是最简单有效的有氧运动之一。规律的跑步可以增强心肺功能，提高身体素质。正确的跑步姿势和呼吸节奏很重要。
    
    力量训练能够增强肌肉力量和耐力。深蹲、硬拉、卧推是三大基础复合动作。合理的训练计划和充足的休息同样重要。
    """
    
    chunker = SemanticChunker()
    chunks = chunker.process_text(boundary_text)
    
    print(f"语义边界检测结果 - 生成 {len(chunks)} 个切片:")
    
    for i, chunk in enumerate(chunks):
        print(f"\n切片 {i+1}:")
        print(f"长度: {len(chunk.content)} 字符")
        print(f"语义得分: {chunk.semantic_score:.3f}")
        print("内容:", chunk.content)

if __name__ == "__main__":
    test_semantic_integrity()
    test_semantic_boundary_detection()
