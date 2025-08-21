# AntSK 语义文本切片服务使用指南

## 快速开始

### 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果使用中文，下载jieba
pip install jieba

# 如果需要GPU加速（可选）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 基础使用
```python
from semantic_chunker import SemanticChunker

# 创建切片器
chunker = SemanticChunker()

# 处理文档
chunks = chunker.process_file("document.pdf")

# 查看结果
for i, chunk in enumerate(chunks):
    print(f"切片 {i+1}: {chunk.content[:100]}...")
    print(f"语义得分: {chunk.semantic_score:.3f}")
    print("-" * 50)
```

## 配置参数详解

### 1. 切片大小配置

```python
from semantic_chunker import ChunkConfig

config = ChunkConfig(
    min_chunk_size=200,      # 最小切片大小（字符数）
    max_chunk_size=1500,     # 最大切片大小（字符数）  
    target_chunk_size=800,   # 目标切片大小（字符数）
)
```

**参数选择建议：**
- **短文本场景** (如微博、评论): min=50, max=300, target=150
- **中等文本** (如新闻文章): min=200, max=800, target=400  
- **长文档** (如技术文档): min=300, max=1500, target=800
- **学术论文**: min=400, max=2000, target=1000

### 2. 语义阈值配置

```python
config = ChunkConfig(
    semantic_threshold=0.7,  # 语义相似度阈值 (0-1)
)
```

**阈值选择指南：**
- **0.8-0.9**: 严格切片，每个切片语义高度一致，适合精确的问答系统
- **0.7-0.8**: 平衡切片，适合大多数应用场景
- **0.6-0.7**: 宽松切片，适合主题多样的长文档
- **0.5-0.6**: 非常宽松，主要按长度切分

### 3. 重叠配置

```python
config = ChunkConfig(
    overlap_ratio=0.1,  # 重叠比例 (0-1)
)
```

**重叠比例说明：**
- **0.0**: 无重叠，节省存储但可能丢失边界信息
- **0.05-0.1**: 轻微重叠，推荐用于大多数场景
- **0.1-0.2**: 适度重叠，适合需要保持语义连续性的场景
- **0.2-0.3**: 高重叠，适合关键信息不能丢失的场景

### 4. 语言配置

```python
config = ChunkConfig(
    language="zh",  # "zh" 中文, "en" 英文
)
```

## 高级配置示例

### 1. 技术文档处理
```python
tech_doc_config = ChunkConfig(
    min_chunk_size=300,
    max_chunk_size=1200,
    target_chunk_size=800,
    semantic_threshold=0.8,     # 高精度
    overlap_ratio=0.15,         # 适度重叠
    language="zh",
    preserve_structure=True,    # 保持文档结构
    handle_special_content=True # 处理表格等特殊内容
)

chunker = SemanticChunker(config=tech_doc_config)
```

### 2. 新闻文章处理
```python
news_config = ChunkConfig(
    min_chunk_size=150,
    max_chunk_size=600,
    target_chunk_size=350,
    semantic_threshold=0.7,     # 平衡精度
    overlap_ratio=0.1,          # 轻微重叠
    language="zh"
)
```

### 3. 学术论文处理
```python
academic_config = ChunkConfig(
    min_chunk_size=400,
    max_chunk_size=2000,
    target_chunk_size=1000,
    semantic_threshold=0.75,    # 较高精度
    overlap_ratio=0.2,          # 高重叠保持连贯性
    language="en"
)
```

## 命令行使用

### 基本命令
```bash
# 处理PDF文件
python cli.py document.pdf --output chunks.json

# 自定义参数
python cli.py document.docx \
    --min-size 200 \
    --max-size 1000 \
    --target-size 600 \
    --semantic-threshold 0.8 \
    --overlap 0.15 \
    --language zh

# 显示预览和统计
python cli.py document.txt --preview --stats --verbose
```

### 高级选项
```bash
# 生成质量报告
python cli.py document.pdf --quality-report

# 使用不同的语义模型
python cli.py document.docx --model "paraphrase-multilingual-MiniLM-L12-v2"

# 处理特殊内容
python cli.py document.pdf --preserve-structure --handle-special
```

## 质量评估和优化

### 1. 查看质量得分
```python
chunks = chunker.process_file("document.pdf")

# 评估质量
quality_results = chunker.quality_evaluator.evaluate_chunks(chunks)

print(f"连贯性得分: {quality_results['avg_coherence']:.3f}")
print(f"完整性得分: {quality_results['avg_completeness']:.3f}")
print(f"综合得分: {quality_results['overall_score']:.3f}")

# 查看优化建议
for suggestion in quality_results['suggestions']:
    print(f"• {suggestion}")
```

### 2. 生成详细报告
```python
report = chunker.quality_evaluator.generate_quality_report(quality_results, chunks)
print(report)
```

### 3. 质量阈值建议
- **综合得分 > 0.8**: 优秀，可直接使用
- **综合得分 0.6-0.8**: 良好，可考虑微调参数
- **综合得分 < 0.6**: 需要调整配置或检查输入文档

## 性能优化建议

### 1. 硬件配置
```python
# GPU加速（如果可用）
import torch
if torch.cuda.is_available():
    print("使用GPU加速")
    chunker = SemanticChunker(model_name="all-MiniLM-L6-v2")  # GPU友好的模型
else:
    print("使用CPU处理")
    chunker = SemanticChunker(model_name="paraphrase-MiniLM-L6-v2")  # 轻量级模型
```

### 2. 大文档处理
```python
# 对于超大文档，建议分批处理
config = ChunkConfig(
    max_chunk_size=1000,  # 减小切片大小
    semantic_threshold=0.6,  # 降低阈值加速处理
)
```

### 3. 内存优化
```python
# 处理完成后清理内存
import gc
chunks = chunker.process_file("large_document.pdf")
del chunker  # 释放模型内存
gc.collect()
```

## 常见问题解决

### 1. 模型下载缓慢
```bash
# 设置镜像源
export HF_ENDPOINT=https://hf-mirror.com
pip install sentence-transformers
```

### 2. 中文处理问题
```python
# 确保正确设置语言
config = ChunkConfig(language="zh")

# 如果jieba分词有问题，可以添加自定义词典
import jieba
jieba.load_userdict("custom_dict.txt")
```

### 3. PDF解析失败
```python
# 尝试不同的PDF解析参数
chunker.document_parser.pdf_config = {
    'extract_images': False,  # 跳过图片提取
    'skip_empty_blocks': True,  # 跳过空文本块
}
```

### 4. 内存不足
```python
# 使用更轻量级的模型
chunker = SemanticChunker(model_name="all-MiniLM-L6-v2")

# 或者降低批处理大小
chunker.semantic_analyzer.batch_size = 16
```

## 集成示例

### 1. 与RAG系统集成
```python
from semantic_chunker import SemanticChunker
from your_vector_db import VectorDB

# 创建语义切片
chunker = SemanticChunker()
chunks = chunker.process_file("knowledge_base.pdf")

# 存储到向量数据库
vector_db = VectorDB()
for chunk in chunks:
    vector_db.add_document(
        content=chunk.content,
        metadata={
            'semantic_score': chunk.semantic_score,
            'token_count': chunk.token_count,
            'source': 'knowledge_base.pdf'
        }
    )
```

### 2. 批量文档处理
```python
import os
from pathlib import Path

def process_document_folder(folder_path, output_dir):
    chunker = SemanticChunker()
    
    for file_path in Path(folder_path).glob("**/*.pdf"):
        print(f"处理: {file_path}")
        
        try:
            chunks = chunker.process_file(file_path)
            
            # 保存结果
            output_file = Path(output_dir) / f"{file_path.stem}_chunks.json"
            chunker.save_chunks(chunks, output_file)
            
            print(f"完成: {len(chunks)} 个切片")
            
        except Exception as e:
            print(f"失败: {e}")

# 使用示例
process_document_folder("documents/", "output/")
```

### 3. Web API集成
```python
from flask import Flask, request, jsonify
from semantic_chunker import SemanticChunker

app = Flask(__name__)
chunker = SemanticChunker()

@app.route('/chunk', methods=['POST'])
def chunk_document():
    try:
        file = request.files['document']
        
        # 保存临时文件
        temp_path = f"temp_{file.filename}"
        file.save(temp_path)
        
        # 处理文件
        chunks = chunker.process_file(temp_path)
        
        # 转换为JSON格式
        result = [
            {
                'content': chunk.content,
                'semantic_score': chunk.semantic_score,
                'token_count': chunk.token_count
            }
            for chunk in chunks
        ]
        
        # 清理临时文件
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'chunks': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## 最佳实践

### 1. 参数调优流程
1. **从默认参数开始**: 使用`ChunkConfig()`默认配置
2. **评估质量**: 运行质量评估，查看综合得分
3. **根据建议调整**: 按照优化建议调整参数
4. **迭代优化**: 重复评估和调整过程

### 2. 不同场景的推荐配置

#### RAG系统
```python
rag_config = ChunkConfig(
    min_chunk_size=200,
    max_chunk_size=800,
    target_chunk_size=500,
    semantic_threshold=0.75,
    overlap_ratio=0.1
)
```

#### 问答系统
```python
qa_config = ChunkConfig(
    min_chunk_size=100,
    max_chunk_size=600,
    target_chunk_size=300,
    semantic_threshold=0.8,
    overlap_ratio=0.15
)
```

#### 文档摘要
```python
summary_config = ChunkConfig(
    min_chunk_size=300,
    max_chunk_size=1200,
    target_chunk_size=800,
    semantic_threshold=0.7,
    overlap_ratio=0.05
)
```

### 3. 质量验证方法
1. **人工抽样检查**: 随机选择10-20个切片进行人工评估
2. **下游任务测试**: 在实际应用中测试切片效果
3. **A/B对比**: 与其他切片方法进行对比测试

## 故障排除

### 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `FileNotFoundError` | 文件路径错误 | 检查文件路径是否正确 |
| `UnicodeDecodeError` | 编码问题 | 指定正确的文件编码 |
| `OutOfMemoryError` | 文档过大 | 使用轻量级模型或分批处理 |
| `ModuleNotFoundError` | 依赖未安装 | 运行 `pip install -r requirements.txt` |
| 语义得分异常低 | 阈值设置不当 | 降低 `semantic_threshold` 值 |
| 切片过大或过小 | 参数配置问题 | 调整 `min/max/target_chunk_size` |

有任何问题，请查看详细的错误日志或提交Issue。
