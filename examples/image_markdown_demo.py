#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片Markdown展示演示
展示修复后的图片在切片中的markdown格式展示功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.antsk_filechunk.enhanced_semantic_chunker import SemanticChunker, ChunkConfig

def demo_image_markdown():
    """演示图片markdown展示功能"""
    
    print("🖼️ 图片Markdown展示演示")
    print("=" * 50)
    
    # 创建切片器配置
    config = ChunkConfig(
        min_chunk_size=200,
        max_chunk_size=1500,
        target_chunk_size=800,
        semantic_threshold=0.6
    )
    
    # 初始化切片器（使用正确的图片URL配置）
    chunker = SemanticChunker(
        config=config,
        image_base_url="http://localhost:8000"  # 修复后的正确端口
    )
    
    print(f"✅ 切片器初始化完成")
    print(f"   - 图片基础URL: {chunker.image_base_url}")
    print(f"   - 文档解析器图片URL: {chunker.document_parser.image_base_url}")
    
    # 创建包含图片引用的测试文本
    test_text = """
    # 产品介绍文档
    
    这是我们的新产品介绍。产品具有以下特点：
    
    1. 高性能处理能力
    2. 用户友好的界面设计
    3. 强大的数据分析功能
    
    下面是产品的架构图：
    
    ![产品架构图](http://localhost:8000/static/images/architecture.png)
    
    从架构图可以看出，我们的系统采用了模块化设计，包括：
    - 数据采集层
    - 处理引擎层  
    - 展示层
    
    这种设计确保了系统的可扩展性和维护性。
    
    ![系统流程图](http://localhost:8000/static/images/workflow.png)
    
    系统的工作流程如上图所示，数据从输入到输出经过多个处理阶段。
    """
    
    print(f"\n📝 处理测试文本...")
    print(f"   - 文本长度: {len(test_text)} 字符")
    
    try:
        # 处理文本
        chunks = chunker.process_text(test_text)
        
        print(f"\n🔧 切片结果:")
        print(f"   - 生成切片数量: {len(chunks)}")
        
        # 展示每个切片的内容
        for i, chunk in enumerate(chunks):
            print(f"\n📄 切片 {i+1}:")
            print(f"   - 类型: {chunk.chunk_type}")
            print(f"   - 长度: {len(chunk.content)} 字符")
            print(f"   - 语义得分: {chunk.semantic_score:.3f}")
            
            # 检查是否包含图片
            has_image = '![' in chunk.content and '](' in chunk.content
            if has_image:
                print(f"   - 包含图片: ✅")
                # 提取图片markdown
                import re
                image_matches = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', chunk.content)
                for alt_text, url in image_matches:
                    print(f"     * 图片: {alt_text} -> {url}")
            else:
                print(f"   - 包含图片: ❌")
            
            print(f"   - 内容预览:")
            preview = chunk.content[:200].replace('\n', ' ')
            if len(chunk.content) > 200:
                preview += "..."
            print(f"     {preview}")
        
        # 统计信息
        total_images = sum(1 for chunk in chunks if '![' in chunk.content)
        print(f"\n📊 统计信息:")
        print(f"   - 总切片数: {len(chunks)}")
        print(f"   - 包含图片的切片: {total_images}")
        print(f"   - 平均切片长度: {sum(len(c.content) for c in chunks) / len(chunks):.0f} 字符")
        
        if total_images > 0:
            print(f"✅ 图片markdown格式已正确保留在切片中！")
        else:
            print(f"⚠️  未检测到图片markdown格式")
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_image_markdown()
