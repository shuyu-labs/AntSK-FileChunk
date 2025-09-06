# 图片Markdown展示修复说明

## 问题描述

之前解析的图片没有使用markdown展示出来，主要存在以下问题：

1. **图片URL配置错误**：默认配置使用端口5000，但实际API服务器运行在端口8000
2. **图片markdown格式丢失**：在切片合并过程中，图片的markdown格式没有被正确保留
3. **图片处理逻辑不完善**：切片器中对图片元素的处理缺少markdown格式支持

## 修复内容

### 1. 修复图片URL配置

**文件**: `src/antsk_filechunk/unified_document_parser.py`

```python
# 修复前
def __init__(self, image_base_url: str = "http://localhost:5000", 
             image_save_dir: str = "./static/images"):

# 修复后  
def __init__(self, image_base_url: str = "http://localhost:8000", 
             image_save_dir: str = "./static/images"):
```

### 2. 增强切片器图片处理

**文件**: `src/antsk_filechunk/enhanced_semantic_chunker.py`

#### 2.1 添加图片URL参数支持

```python
# SemanticChunker类构造函数
def __init__(self, config: ChunkConfig = None, model_name: str = "all-MiniLM-L6-v2", 
             image_base_url: str = "http://localhost:8000"):

# EnhancedSemanticChunker类构造函数  
def __init__(self, config: ChunkConfig = None, model_name: str = "all-MiniLM-L6-v2", 
             cache_size: int = 1000, enable_fallback: bool = True, 
             image_base_url: str = "http://localhost:8000"):
```

#### 2.2 改进图片元素处理

```python
# 在_process_document_content_unified方法中添加markdown格式支持
processed_content['elements'].append({
    'type': 'image',
    'content': image_text,
    'markdown_content': markdown_image,  # 新增：预生成的markdown格式
    'original_data': image,
    'index': len(processed_content['elements'])
})
```

#### 2.3 优化切片内容合并

```python
# 在_merge_chunk_content方法中优先使用预生成的markdown格式
elif element_type == 'image':
    # 对于图片，优先使用预生成的markdown格式
    markdown_content = element.get('markdown_content', '')
    if markdown_content:
        content_parts.append(markdown_content)
    else:
        # 降级处理：从原始数据生成markdown
        original_data = element.get('original_data', {})
        image_url = original_data.get('url', '')
        image_filename = original_data.get('filename', '图片')
        if image_url:
            content_parts.append(f"![{image_filename}]({image_url})")
```

## 修复效果

### 修复前
- 图片URL使用错误端口：`http://localhost:5000/static/images/xxx.png`
- 切片中图片显示为：`[图片] http://localhost:5000/static/images/xxx.png`
- 无法在markdown渲染器中正确显示图片

### 修复后
- 图片URL使用正确端口：`http://localhost:8000/static/images/xxx.png`
- 切片中图片显示为：`![图片名称](http://localhost:8000/static/images/xxx.png)`
- 可以在markdown渲染器中正确显示图片

## 测试验证

运行演示脚本验证修复效果：

```bash
python examples/image_markdown_demo.py
```

**测试结果**：
- ✅ 图片URL配置正确（端口8000）
- ✅ 图片markdown格式正确保留
- ✅ 切片中包含图片的内容能正确识别和展示

## 支持的文档格式

修复后的功能支持以下文档格式中的图片提取和markdown展示：

1. **PDF文档** - 提取嵌入的图片
2. **Word文档(.docx)** - 提取文档中的图片
3. **PowerPoint文档(.pptx)** - 提取幻灯片中的图片
4. **Excel文档(.xlsx)** - 提取工作表中的图片

## 使用示例

```python
from src.antsk_filechunk.enhanced_semantic_chunker import SemanticChunker, ChunkConfig

# 创建配置
config = ChunkConfig(
    min_chunk_size=200,
    max_chunk_size=1500,
    target_chunk_size=800
)

# 初始化切片器（使用正确的图片URL）
chunker = SemanticChunker(
    config=config,
    image_base_url="http://localhost:8000"  # 正确的端口配置
)

# 处理包含图片的文档
chunks = chunker.process_file("document_with_images.pdf")

# 检查切片中的图片markdown格式
for chunk in chunks:
    if '![' in chunk.content:
        print(f"发现图片: {chunk.content}")
```

## 注意事项

1. **静态文件服务**：确保API服务器正确配置了静态文件服务，能够访问 `/static/images/` 路径下的图片
2. **图片格式支持**：支持常见的图片格式（PNG、JPG、JPEG、GIF、BMP、WEBP）
3. **URL配置**：如果API服务器运行在不同的端口或域名，需要相应调整 `image_base_url` 参数

## 相关文件

- `src/antsk_filechunk/unified_document_parser.py` - 文档解析器，负责图片提取
- `src/antsk_filechunk/enhanced_semantic_chunker.py` - 语义切片器，负责图片在切片中的处理
- `examples/image_markdown_demo.py` - 演示脚本，展示修复后的功能
- `api_server.py` - API服务器，提供静态文件服务
