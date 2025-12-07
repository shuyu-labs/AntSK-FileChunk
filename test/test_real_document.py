#!/usr/bin/env python3
"""
测试真实文档的图片提取功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from antsk_filechunk.unified_document_parser import UnifiedDocumentParser
from antsk_filechunk.enhanced_semantic_chunker import EnhancedSemanticChunker

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_with_images(file_path):
    """测试包含图片的文档"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    try:
        print(f"📄 正在测试文档: {file_path}")
        print("=" * 60)
        
        # 创建解析器和切片器
        parser = UnifiedDocumentParser(
            image_base_url="http://localhost:8000",
            image_save_dir="./static/images"
        )
        chunker = EnhancedSemanticChunker()
        
        # 1. 解析文档
        print("🔍 正在解析文档...")
        document_content = parser.parse_file(file_path)
        
        print(f"📊 解析结果:")
        print(f"   - 段落数: {len(document_content.paragraphs)}")
        print(f"   - 表格数: {len(document_content.tables)}")
        print(f"   - 图片数: {len(document_content.images)}")
        
        # 显示图片信息
        if document_content.images:
            print(f"\n🖼️ 提取的图片:")
            for i, img in enumerate(document_content.images):
                print(f"   {i+1}. 文件名: {img.get('filename')}")
                print(f"      格式: {img.get('format')}")
                print(f"      大小: {img.get('size', 0)} bytes")
                print(f"      URL: {img.get('url')}")
                print(f"      路径: {img.get('path')}")
                print()
        else:
            print("⚠️ 未检测到图片")
        
        # 2. 检查markdown内容
        print("📝 检查markdown内容:")
        if '![' in document_content.markdown_content:
            print("✅ markdown内容包含图片引用")
            # 提取所有图片引用
            import re
            image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', document_content.markdown_content)
            for alt_text, url in image_refs:
                print(f"   - {alt_text}: {url}")
        else:
            print("❌ markdown内容不包含图片引用")
        
        # 3. 进行切片处理
        print(f"\n🔧 正在进行语义切片...")
        chunks = chunker.process_document(document_content)
        
        print(f"📊 切片结果:")
        print(f"   - 切片总数: {len(chunks)}")
        
        # 检查包含图片的切片
        image_chunks = []
        for i, chunk in enumerate(chunks):
            if '![' in chunk.content:
                image_chunks.append((i, chunk))
        
        print(f"   - 包含图片的切片: {len(image_chunks)}")
        
        if image_chunks:
            print(f"\n🖼️ 包含图片的切片详情:")
            for i, (chunk_idx, chunk) in enumerate(image_chunks):
                print(f"\n   切片 {chunk_idx + 1}:")
                print(f"   - 类型: {chunk.chunk_type}")
                print(f"   - 长度: {len(chunk.content)} 字符")
                print(f"   - 语义得分: {chunk.semantic_score:.3f}")
                
                # 提取图片信息
                import re
                image_matches = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', chunk.content)
                for alt_text, url in image_matches:
                    print(f"   - 图片: {alt_text} -> {url}")
                
                # 显示内容预览
                preview = chunk.content[:200].replace('\n', ' ')
                if len(chunk.content) > 200:
                    preview += "..."
                print(f"   - 内容预览: {preview}")
        
        # 4. 总结
        print(f"\n📋 测试总结:")
        print(f"   - 文档解析: {'✅ 成功' if document_content else '❌ 失败'}")
        print(f"   - 图片提取: {'✅ 成功' if document_content.images else '⚠️ 无图片'}")
        print(f"   - markdown生成: {'✅ 成功' if '![' in document_content.markdown_content else '❌ 失败'}")
        print(f"   - 切片处理: {'✅ 成功' if chunks else '❌ 失败'}")
        print(f"   - 图片切片: {'✅ 成功' if image_chunks else '⚠️ 无图片切片'}")
        
        if document_content.images and image_chunks:
            print(f"\n🎉 图片提取和切片功能工作正常！")
        elif document_content.images and not image_chunks:
            print(f"\n⚠️ 图片已提取但未出现在切片中，可能需要进一步检查")
        else:
            print(f"\n📝 文档中没有图片，无法测试图片功能")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 真实文档图片提取测试")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # 使用命令行参数指定的文件
        for file_path in sys.argv[1:]:
            test_document_with_images(file_path)
            print("\n" + "="*60 + "\n")
    else:
        print("使用方法:")
        print("  python test_real_document.py <文档文件路径>")
        print("\n示例:")
        print("  python test_real_document.py document_with_images.docx")
        print("  python test_real_document.py document_with_images.pdf")
        print("\n支持的格式: .pdf, .docx, .txt, .xlsx, .xls, .pptx")
