"""
语义文本切片服务使用示例
演示各种功能和配置选项
"""

import os
import json
from pathlib import Path

from semantic_chunker import SemanticChunker, ChunkConfig


def example_basic_usage():
    """基础使用示例"""
    print("="*50)
    print("示例1: 基础用法")
    print("="*50)
    
    # 创建默认配置的切片器
    chunker = SemanticChunker()
    
    # 处理文档 (这里使用示例文本)
    sample_text = """
    这是第一段文本，讨论的是人工智能的发展历程。人工智能经历了多次起伏，从最初的符号主义到现在的深度学习，技术不断演进。

    第二段转向讨论机器学习的基本概念。机器学习是人工智能的一个重要分支，它使计算机能够从数据中学习规律，而不需要明确的编程指令。

    第三段专门介绍深度学习技术。深度学习基于人工神经网络，通过多层网络结构来学习数据的复杂特征和模式。

    最后一段总结了当前AI技术的应用前景。从自然语言处理到计算机视觉，AI技术正在改变我们的生活和工作方式。
    """
    
    # 创建临时文件
    temp_file = Path("temp_sample.txt")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    try:
        # 处理文件
        chunks = chunker.process_file(temp_file)
        
        # 显示结果
        print(f"生成了 {len(chunks)} 个切片:")
        for i, chunk in enumerate(chunks):
            print(f"\n切片 {i+1}:")
            print(f"  长度: {len(chunk.content)} 字符")
            print(f"  语义得分: {chunk.semantic_score:.3f}")
            print(f"  内容: {chunk.content[:100]}...")
        
        # 获取统计信息
        stats = chunker.get_chunking_statistics(chunks)
        print(f"\n平均切片长度: {stats['avg_length']:.1f}")
        print(f"平均语义得分: {stats['avg_semantic_score']:.3f}")
        
    finally:
        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()


def example_custom_config():
    """自定义配置示例"""
    print("\n" + "="*50)
    print("示例2: 自定义配置")
    print("="*50)
    
    # 创建自定义配置
    config = ChunkConfig(
        min_chunk_size=100,      # 更小的最小切片
        max_chunk_size=800,      # 更小的最大切片
        target_chunk_size=400,   # 更小的目标切片
        semantic_threshold=0.8,  # 更高的语义阈值
        overlap_ratio=0.15,      # 更大的重叠比例
        language="zh"
    )
    
    chunker = SemanticChunker(config=config)
    
    # 更长的示例文本
    long_text = """
    自然语言处理（Natural Language Processing, NLP）是计算机科学、人工智能和语言学的交叉领域。
    它致力于让计算机能够理解、解释和生成人类语言。随着深度学习技术的发展，NLP领域取得了突破性进展。

    在传统的NLP方法中，研究者主要依赖手工设计的特征和规则。这些方法在特定任务上可能表现良好，
    但泛化能力有限，且需要大量的领域专业知识。传统方法包括基于规则的方法和统计机器学习方法。

    深度学习的兴起彻底改变了NLP的研究范式。Word2Vec、GloVe等词嵌入技术让计算机能够将词汇映射到高维向量空间，
    捕捉词汇间的语义关系。这为后续的神经网络模型奠定了基础。

    循环神经网络（RNN）和长短期记忆网络（LSTM）的出现，让模型能够更好地处理序列数据。
    这些模型在机器翻译、文本摘要、情感分析等任务上取得了显著改进。

    Transformer架构的提出是NLP发展史上的里程碑事件。它引入了自注意力机制，能够并行处理序列中的所有位置，
    大大提高了训练效率。BERT、GPT等预训练模型基于Transformer架构，在各种NLP任务上刷新了性能记录。

    当前，大型语言模型（LLM）如GPT-3、ChatGPT等展现出了惊人的能力。它们不仅能够完成传统的NLP任务，
    还能进行复杂的推理、创作和对话。这些模型的出现标志着我们正在进入通用人工智能的新时代。

    尽管取得了巨大进展，NLP仍面临诸多挑战。模型的可解释性、偏见问题、计算资源消耗等都需要进一步解决。
    此外，如何让模型更好地理解上下文、常识和隐含意义，也是未来研究的重要方向。
    """
    
    temp_file = Path("temp_long_sample.txt")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(long_text)
    
    try:
        chunks = chunker.process_file(temp_file)
        
        print(f"使用自定义配置生成了 {len(chunks)} 个切片:")
        for i, chunk in enumerate(chunks):
            print(f"\n切片 {i+1}:")
            print(f"  长度: {len(chunk.content)} 字符")
            print(f"  语义得分: {chunk.semantic_score:.3f}")
            print(f"  段落数: {len(chunk.paragraph_indices)}")
            print(f"  前50字符: {chunk.content[:50]}...")
        
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_quality_evaluation():
    """质量评估示例"""
    print("\n" + "="*50)
    print("示例3: 质量评估")
    print("="*50)
    
    chunker = SemanticChunker()
    
    # 包含不同质量的文本
    mixed_quality_text = """
    这是一个语义连贯的段落，讨论机器学习的基本概念。机器学习是人工智能的重要分支，
    它使计算机能够从数据中自动学习和改进性能，而无需显式编程。

    突然转到完全不相关的话题。今天天气很好，我喜欢吃苹果。昨天看了电影。
    购物清单包括牛奶、面包和鸡蛋。

    回到技术话题，深度学习是机器学习的一个子领域。它基于人工神经网络，
    特别是具有多个隐藏层的神经网络。深度学习在图像识别、自然语言处理等领域取得了突破性进展。

    这个段落故意写得很短。

    这是最后一个段落，它试图总结前面的内容，但由于中间有不相关的内容，
    整体的语义连贯性受到了影响。不过，这正好可以用来测试我们的质量评估功能。
    """
    
    temp_file = Path("temp_quality_test.txt")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(mixed_quality_text)
    
    try:
        chunks = chunker.process_file(temp_file)
        
        # 进行质量评估
        quality_results = chunker.quality_evaluator.evaluate_chunks(chunks)
        
        print(f"质量评估结果:")
        print(f"  平均连贯性: {quality_results['avg_coherence']:.3f}")
        print(f"  平均完整性: {quality_results['avg_completeness']:.3f}")
        print(f"  长度平衡性: {quality_results['length_balance']:.3f}")
        print(f"  平均语义密度: {quality_results['avg_semantic_density']:.3f}")
        print(f"  边界质量: {quality_results['boundary_quality']:.3f}")
        print(f"  综合得分: {quality_results['overall_score']:.3f}")
        
        print(f"\n优化建议:")
        for suggestion in quality_results.get('suggestions', []):
            print(f"  • {suggestion}")
        
        # 生成详细报告
        report = chunker.quality_evaluator.generate_quality_report(quality_results, chunks)
        print(f"\n详细报告:\n{report}")
        
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_save_and_load():
    """保存和加载示例"""
    print("\n" + "="*50)
    print("示例4: 保存和加载切片结果")
    print("="*50)
    
    chunker = SemanticChunker()
    
    sample_text = """
    区块链技术是一种分布式账本技术，它以去中心化的方式存储交易记录。
    每个区块包含一定数量的交易，通过密码学哈希函数与前一个区块相连，形成链式结构。

    比特币是区块链技术的第一个成功应用。它展示了如何在没有中央机构的情况下，
    实现数字货币的发行和交易。比特币网络依靠全球分布的节点来维护账本的一致性。

    智能合约是区块链的另一个重要应用。智能合约是自执行的合约，
    合约条款直接写入代码中。以太坊平台使智能合约的大规模应用成为可能。

    去中心化金融（DeFi）是区块链技术的新兴应用领域。它旨在重新创建传统金融系统，
    但没有中央控制机构。DeFi应用包括去中心化交易所、借贷平台和保险产品。
    """
    
    temp_file = Path("temp_blockchain.txt")
    output_file = Path("blockchain_chunks.json")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    try:
        # 处理并保存
        chunks = chunker.process_file(temp_file)
        chunker.save_chunks(chunks, output_file)
        print(f"切片结果已保存到: {output_file}")
        
        # 读取并显示保存的结果
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print(f"\n从文件读取到 {len(saved_data['chunks'])} 个切片:")
        for i, chunk_data in enumerate(saved_data['chunks'][:2]):  # 只显示前2个
            print(f"\n切片 {i+1}:")
            print(f"  ID: {chunk_data['id']}")
            print(f"  长度: {len(chunk_data['content'])} 字符")
            print(f"  语义得分: {chunk_data['semantic_score']:.3f}")
            print(f"  Token数: {chunk_data['token_count']}")
        
        print(f"\n保存的配置信息:")
        config_data = saved_data['config']
        print(f"  目标切片大小: {config_data['target_chunk_size']}")
        print(f"  语义阈值: {config_data['semantic_threshold']}")
        print(f"  语言: {config_data['language']}")
        
        print(f"\n统计信息:")
        stats = saved_data['statistics']
        print(f"  平均长度: {stats['avg_length']:.1f}")
        print(f"  平均语义得分: {stats['avg_semantic_score']:.3f}")
        
    finally:
        # 清理文件
        for file in [temp_file, output_file]:
            if file.exists():
                file.unlink()


def main():
    """运行所有示例"""
    print("语义文本切片服务使用示例\n")
    
    try:
        example_basic_usage()
        example_custom_config()
        example_quality_evaluation()
        example_save_and_load()
        
        print("\n" + "="*50)
        print("所有示例运行完成!")
        print("="*50)
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
