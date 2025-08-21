#!/usr/bin/env python3
"""
语义文本切片服务命令行工具
"""

import argparse
import logging
import json
from pathlib import Path
import sys

from src.antsk_filechunk.core.enhanced_semantic_chunker import SemanticChunker, ChunkConfig, TextChunk


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def create_config_from_args(args) -> ChunkConfig:
    """从命令行参数创建配置"""
    return ChunkConfig(
        min_chunk_size=args.min_size,
        max_chunk_size=args.max_size,
        target_chunk_size=args.target_size,
        overlap_ratio=args.overlap,
        semantic_threshold=args.semantic_threshold,
        paragraph_merge_threshold=args.paragraph_threshold,
        language=args.language,
        preserve_structure=args.preserve_structure,
        handle_special_content=args.handle_special
    )


def print_statistics(chunks, stats):
    """打印切片统计信息"""
    print("\n" + "="*50)
    print("切片统计信息")
    print("="*50)
    print(f"总切片数量: {stats['total_chunks']}")
    print(f"平均长度: {stats['avg_length']:.1f} 字符")
    print(f"最小长度: {stats['min_length']} 字符")
    print(f"最大长度: {stats['max_length']} 字符")
    print(f"长度标准差: {stats['length_std']:.1f}")
    print(f"平均Token数: {stats['avg_tokens']:.1f}")
    print(f"平均语义得分: {stats['avg_semantic_score']:.3f}")
    
    print(f"\n长度分布:")
    dist = stats['length_distribution']
    print(f"  < 500字符: {dist['under_500']} 个")
    print(f"  500-1000字符: {dist['500_1000']} 个")
    print(f"  1000-1500字符: {dist['1000_1500']} 个")
    print(f"  > 1500字符: {dist['over_1500']} 个")


def preview_chunks(chunks, max_preview=3):
    """预览切片内容"""
    print(f"\n切片预览 (前{min(max_preview, len(chunks))}个):")
    print("-"*50)
    
    for i, chunk in enumerate(chunks[:max_preview]):
        print(f"\n切片 {i+1}:")
        print(f"长度: {len(chunk.content)} 字符")
        print(f"Token数: {chunk.token_count}")
        print(f"语义得分: {chunk.semantic_score:.3f}")
        print(f"内容预览: {chunk.content[:200]}{'...' if len(chunk.content) > 200 else ''}")
        print("-"*30)


def main():
    parser = argparse.ArgumentParser(
        description="语义文本切片服务 - 基于语义理解的智能文档切片工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python cli.py document.pdf --output chunks.json
  python cli.py document.docx --min-size 300 --max-size 1200 --language zh
  python cli.py document.txt --semantic-threshold 0.8 --preview --verbose
        """
    )
    
    # 输入输出参数
    parser.add_argument('input_file', help='输入文件路径 (支持PDF, DOCX, TXT格式)')
    parser.add_argument('--output', '-o', help='输出文件路径 (JSON格式)')
    
    # 切片配置参数
    parser.add_argument('--min-size', type=int, default=200,
                       help='最小切片大小 (字符数, 默认: 200)')
    parser.add_argument('--max-size', type=int, default=1500,
                       help='最大切片大小 (字符数, 默认: 1500)')
    parser.add_argument('--target-size', type=int, default=800,
                       help='目标切片大小 (字符数, 默认: 800)')
    parser.add_argument('--overlap', type=float, default=0.1,
                       help='重叠比例 (0-1, 默认: 0.1)')
    parser.add_argument('--semantic-threshold', type=float, default=0.7,
                       help='语义相似度阈值 (0-1, 默认: 0.7)')
    parser.add_argument('--paragraph-threshold', type=float, default=0.8,
                       help='段落合并阈值 (0-1, 默认: 0.8)')
    
    # 语言和处理选项
    parser.add_argument('--language', choices=['zh', 'en'], default='zh',
                       help='文档语言 (默认: zh)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='语义嵌入模型名称')
    parser.add_argument('--preserve-structure', action='store_true',
                       help='保持文档结构')
    parser.add_argument('--handle-special', action='store_true',
                       help='处理特殊内容 (表格、图片等)')
    
    # 输出选项
    parser.add_argument('--preview', action='store_true',
                       help='显示切片预览')
    parser.add_argument('--stats', action='store_true',
                       help='显示详细统计信息')
    parser.add_argument('--quality-report', action='store_true',
                       help='生成质量评估报告')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 检查输入文件
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)
    
    try:
        # 创建配置
        config = create_config_from_args(args)
        
        print(f"正在处理文件: {input_path}")
        print(f"配置参数: 目标大小={config.target_chunk_size}, 语义阈值={config.semantic_threshold}")
        
        # 创建切片器
        chunker = SemanticChunker(config=config, model_name=args.model)
        
        # 处理文件
        chunks = chunker.process_file(input_path)
        
        if not chunks:
            print("警告: 未生成任何切片")
            sys.exit(0)
        
        print(f"切片处理完成，共生成 {len(chunks)} 个切片")
        
        # 获取统计信息
        stats = chunker.get_chunking_statistics(chunks)
        
        # 显示统计信息
        if args.stats or args.verbose:
            print_statistics(chunks, stats)
        
        # 显示预览
        if args.preview:
            preview_chunks(chunks)
        
        # 生成质量报告
        if args.quality_report:
            try:
                quality_scores = chunker.quality_evaluator.evaluate_chunks(chunks)
                report = chunker.quality_evaluator.generate_quality_report(quality_scores, chunks)
                print(f"\n{report}")
            except Exception as e:
                print(f"质量报告生成失败: {e}")
        
        # 保存结果
        if args.output:
            output_path = Path(args.output)
            chunker.save_chunks(chunks, output_path)
            print(f"切片结果已保存到: {output_path}")
        else:
            # 默认输出到同目录下的 JSON 文件
            default_output = input_path.with_suffix('.chunks.json')
            chunker.save_chunks(chunks, default_output)
            print(f"切片结果已保存到: {default_output}")
        
        print("处理完成!")
        
    except Exception as e:
        print(f"处理失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
