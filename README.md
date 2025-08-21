# AntSK 语义文本切片服务

## 项目简介

AntSK-FileChunk 是一个基于语义理解的智能文本切片服务，专门用于处理PDF和Word文档，能够根据段落语义进行合理切片，避免传统基于Token数量切分导致的语义割裂问题。

## 项目结构

```
AntSK-FileChunk/
├── src/                          # 源代码目录
│   └── antsk_filechunk/
│       ├── core/                 # 核心功能模块
│       │   └── semantic_chunker.py
│       ├── parsers/              # 文档解析器
│       │   └── document_parser.py
│       ├── analyzers/            # 语义分析器
│       │   └── semantic_analyzer.py
│       ├── optimizers/           # 切片优化器
│       │   └── chunk_optimizer.py
│       ├── evaluators/           # 质量评估器
│       │   └── quality_evaluator.py
│       └── utils/                # 工具模块
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── fixtures/                 # 测试数据
├── docs/                         # 文档目录
│   ├── guides/                   # 使用指南
│   └── api/                      # API文档
├── examples/                     # 示例和演示
│   └── data/                     # 示例数据
├── config/                       # 配置文件
├── scripts/                      # 脚本工具
├── data/                         # 数据目录
│   ├── sample/                   # 示例数据
│   └── models/                   # 模型文件
└── requirements.txt              # 依赖文件
```

## 核心特性

- **段落级语义切片**: 以段落为基本单位，确保每个切片语义完整
- **智能文档解析**: 支持Word(.docx)和PDF文件的格式识别和内容提取
- **自适应切片大小**: 根据语义内容动态调整切片长度
- **语义连贯性检测**: 处理跨段落语义关联和延展情况
- **质量评估体系**: 提供切片质量评估和优化建议

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基础使用
```python
from antsk_filechunk import SemanticChunker

# 创建切片器
chunker = SemanticChunker()

# 处理文档
chunks = chunker.process_file("document.pdf")

# 查看结果
for chunk in chunks:
    print(f"内容: {chunk.content[:100]}...")
    print(f"语义得分: {chunk.semantic_score}")
```

### 命令行使用
```bash
python scripts/cli.py document.pdf --output chunks.json
```

## 文档链接

- [用户指南](docs/guides/USER_GUIDE.md)
- [算法设计](docs/guides/ALGORITHM_DESIGN.md)
- [完整文档](docs/README.md)

## 许可证

MIT License
