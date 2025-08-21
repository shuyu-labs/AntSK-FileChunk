# 项目目录结构说明

## 完整目录结构

```
AntSK-FileChunk/
├── 📁 src/                              # 源代码根目录
│   └── antsk_filechunk/                 # 主包目录
│       ├── __init__.py                  # 包初始化文件
│       ├── 📁 core/                     # 核心功能模块
│       │   ├── __init__.py
│       │   └── semantic_chunker.py      # 语义切片器主类
│       ├── 📁 parsers/                  # 文档解析器模块
│       │   ├── __init__.py
│       │   └── document_parser.py       # 文档解析器（PDF/Word/TXT）
│       ├── 📁 analyzers/                # 语义分析器模块
│       │   ├── __init__.py
│       │   └── semantic_analyzer.py     # 语义分析器
│       ├── 📁 optimizers/               # 切片优化器模块
│       │   ├── __init__.py
│       │   └── chunk_optimizer.py       # 切片优化器
│       ├── 📁 evaluators/               # 质量评估器模块
│       │   ├── __init__.py
│       │   └── quality_evaluator.py     # 质量评估器
│       └── 📁 utils/                    # 工具模块
│           └── __init__.py
├── 📁 tests/                           # 测试目录
│   ├── __init__.py
│   ├── conftest.py                     # 测试配置
│   ├── 📁 unit/                        # 单元测试
│   │   └── test_chunker.py             # 切片器单元测试
│   ├── 📁 integration/                 # 集成测试
│   └── 📁 fixtures/                    # 测试数据和夹具
├── 📁 docs/                            # 文档目录
│   ├── README.md                       # 完整项目文档
│   ├── 📁 guides/                      # 使用指南
│   │   ├── USER_GUIDE.md               # 用户使用指南
│   │   └── ALGORITHM_DESIGN.md         # 算法设计文档
│   └── 📁 api/                         # API文档
├── 📁 examples/                        # 示例和演示
│   ├── demo.py                         # 基础演示脚本
│   ├── examples.py                     # 各种使用示例
│   └── 📁 data/                        # 示例数据
│       └── demo_chunks_result.json     # 演示结果
├── 📁 config/                          # 配置文件
│   └── default.conf                    # 默认配置
├── 📁 scripts/                         # 脚本工具
│   ├── cli.py                          # 命令行工具
│   └── setup_dev.py                    # 开发环境设置脚本
├── 📁 data/                            # 数据目录
│   ├── 📁 sample/                      # 示例数据
│   └── 📁 models/                      # 模型文件
├── 📄 README.md                        # 项目说明
├── 📄 requirements.txt                 # 依赖文件
├── 📄 setup.py                         # 安装脚本
├── 📄 Makefile                         # 构建脚本
├── 📄 .gitignore                       # Git忽略文件
└── 📄 __init__.py                      # 根包初始化
```

## 目录功能说明

### 📁 src/antsk_filechunk/ - 主包目录
- **core/**: 核心功能实现，包含主要的语义切片器类
- **parsers/**: 文档解析功能，支持PDF、Word、TXT等格式
- **analyzers/**: 语义分析功能，基于Transformer模型
- **optimizers/**: 切片优化功能，合并小切片、分割大切片
- **evaluators/**: 质量评估功能，评估切片效果
- **utils/**: 通用工具和辅助函数

### 📁 tests/ - 测试目录
- **unit/**: 单元测试，测试各个模块的独立功能
- **integration/**: 集成测试，测试模块间的协同工作
- **fixtures/**: 测试数据和测试用例

### 📁 docs/ - 文档目录
- **guides/**: 详细的使用指南和算法设计文档
- **api/**: API接口文档（待生成）

### 📁 examples/ - 示例目录
- 包含各种使用场景的示例代码
- 演示数据和结果文件

### 📁 config/ - 配置目录
- 默认配置文件
- 各种场景的配置模板

### 📁 scripts/ - 脚本目录
- 命令行工具
- 开发和部署脚本

### 📁 data/ - 数据目录
- 示例数据
- 预训练模型文件（缓存）

## 设计原则

1. **分层架构**: 按功能模块分层，职责清晰
2. **松耦合**: 各模块间依赖关系简单，易于测试和维护  
3. **可扩展**: 新增功能时容易扩展
4. **标准化**: 遵循Python包的标准结构
5. **文档齐全**: 每个模块都有对应的文档和示例

## 使用方式

### 作为包安装使用
```python
from antsk_filechunk import SemanticChunker
chunker = SemanticChunker()
chunks = chunker.process_file("document.pdf")
```

### 命令行使用
```bash
python scripts/cli.py document.pdf --output chunks.json
```

### 开发模式
```bash
# 设置开发环境
python scripts/setup_dev.py

# 运行测试
make test

# 运行示例
make run-example
```
