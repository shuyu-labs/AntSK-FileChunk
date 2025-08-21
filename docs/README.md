# AntSK 语义文本切片服务

## 项目简介

这是一个基于语义理解的智能文本切片服务，专门用于处理Word和PDF文档，能够根据段落语义进行合理切片，避免传统基于Token数量切分导致的语义割裂问题。

## 核心特性

1. **段落级语义切片**: 以段落为基本单位，确保每个切片语义完整
2. **智能文档解析**: 支持Word(.docx)和PDF文件的格式识别和内容提取
3. **自适应切片大小**: 根据语义内容动态调整切片长度
4. **语义连贯性检测**: 处理跨段落语义关联和延展情况
5. **异常内容处理**: 智能处理表格、图片、特殊符号等非文本内容

## 技术架构

- **文档解析层**: 基于python-docx和PyMuPDF进行文档解析
- **语义分析层**: 使用sentence-transformers进行语义向量计算
- **切片算法层**: 基于语义相似度和长度约束的智能切片
- **质量评估层**: 切片效果验证和优化建议

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用示例

```python
from antsk_filechunk.core.enhanced_semantic_chunker import SemanticChunker

# 创建切片器实例
chunker = SemanticChunker()

# 处理文档
chunks = chunker.process_file("document.pdf")

# 查看切片结果
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk.content[:100]}...")
    print(f"Semantic Score: {chunk.semantic_score}")
    print(f"Token Count: {chunk.token_count}")
    print("-" * 50)
```

## 切片质量验证

系统提供多种验证方式：
- 语义连贯性评分
- 切片长度分布分析
- 跨切片语义重叠检测
- 人工评估接口
