# AntSK 文件切片服务 - API接口和测试页面

## 📋 项目概述

成功为 AntSK 文件切片服务添加了完整的 FastAPI 接口和 HTML 测试页面，提供了用户友好的 Web 界面和完整的 API 文档。

## 🚀 已完成的功能

### 1. FastAPI API接口

#### 🌐 主要端点
- **GET /**  - 主页测试界面
- **GET /health** - 健康检查接口
- **POST /api/process-file** - 文件上传和处理接口
- **POST /api/process-text** - 文本内容处理接口
- **GET /api/config/default** - 获取默认配置接口

#### 📖 API文档
- **Swagger文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

### 2. HTML测试页面

#### 🎨 功能特性
- **现代化UI设计**: 渐变背景、卡片式布局、响应式设计
- **多标签页界面**:
  - 📁 文件上传标签页 - 支持拖拽上传
  - 📝 文本输入标签页 - 直接输入文本处理
  - 📚 API文档标签页 - 接口说明
- **可配置参数**:
  - 切片大小控制（最小、最大、目标大小）
  - 重叠比例设置
  - 语义阈值调整
  - 语言选择（中文/英文）
  - 文档结构保持选项
- **实时结果展示**:
  - 处理进度提示
  - 切片结果详细显示
  - 语义得分可视化
  - 错误处理和提示

### 3. 技术特性

#### 🔧 后端改进
- **数据类型转换**: 解决了numpy类型序列化问题
- **异常处理**: 完善的错误处理和日志记录
- **文件管理**: 自动临时文件清理
- **配置验证**: Pydantic模型验证

#### 🖥️ 前端特性
- **拖拽上传**: 支持文件拖拽到指定区域
- **实时反馈**: Ajax异步请求和加载状态显示
- **响应式设计**: 适配不同屏幕尺寸
- **用户体验**: 友好的错误提示和成功反馈

## 📦 文件结构

```
📁 项目根目录/
├── 🚀 api_server.py          # FastAPI应用主文件
├── 🎯 start_server.py        # 服务启动脚本
├── 🧪 test_service.py        # 功能测试脚本
├── 🔍 test_api.py            # API接口测试脚本
├── 📁 templates/
│   └── 🏠 index.html         # 主测试页面模板
├── 📁 static/                # 静态资源目录（可扩展）
└── 📁 temp/                  # 临时文件目录
```

## 🛠️ 使用方法

### 启动服务
```bash
# 方法1: 使用启动脚本
python start_server.py

# 方法2: 直接运行API服务器
python api_server.py
```

### 访问服务
- **测试页面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 功能测试
```bash
# 测试核心功能
python test_service.py

# 测试API接口
python test_api.py
```

## 🎯 支持的文件格式

- **PDF文档** (.pdf)
- **Word文档** (.docx, .doc) 
- **纯文本** (.txt)
- **直接文本输入**

## ⚙️ 配置参数说明

| 参数名称 | 类型 | 默认值 | 说明 |
|---------|------|--------|------|
| min_chunk_size | int | 200 | 最小切片字符数 (50-1000) |
| max_chunk_size | int | 1500 | 最大切片字符数 (500-5000) |
| target_chunk_size | int | 800 | 目标切片字符数 (200-2000) |
| overlap_ratio | float | 0.1 | 重叠比例 (0.0-0.5) |
| semantic_threshold | float | 0.7 | 语义相似度阈值 (0.0-1.0) |
| paragraph_merge_threshold | float | 0.8 | 段落合并阈值 (0.0-1.0) |
| language | str | "zh" | 语言设置 ("zh"/"en") |
| preserve_structure | bool | true | 是否保持文档结构 |
| handle_special_content | bool | true | 是否处理特殊内容 |

## 📊 API响应格式

### 处理成功响应
```json
{
  "success": true,
  "message": "处理成功",
  "chunks": [
    {
      "content": "切片内容...",
      "start_pos": 0,
      "end_pos": 100,
      "semantic_score": 0.85,
      "token_count": 50,
      "paragraph_indices": [0, 1],
      "chunk_type": "content",
      "metadata": {}
    }
  ],
  "total_chunks": 4,
  "processing_time": 2.34,
  "file_info": {
    "filename": "example.pdf",
    "size": 12345,
    "type": ".pdf"
  }
}
```

## 🐛 问题解决

### 已解决的问题
1. ✅ **Numpy类型序列化错误** - 添加了安全类型转换函数
2. ✅ **模型加载超时** - 优化了启动流程
3. ✅ **文件上传限制** - 添加了文件大小和类型检查
4. ✅ **跨域请求问题** - 配置了适当的CORS设置

### 注意事项
- 🔸 首次启动需要下载语义模型，可能需要几分钟时间
- 🔸 建议使用虚拟环境运行项目
- 🔸 文件大小建议控制在10MB以内以获得最佳性能

## 🎉 成果展示

### ✨ 主要亮点
1. **完整的Web界面** - 美观易用的测试页面
2. **RESTful API** - 标准的HTTP接口设计  
3. **自动API文档** - Swagger/OpenAPI集成
4. **错误处理** - 完善的异常处理机制
5. **类型安全** - Pydantic数据验证
6. **实时反馈** - 用户友好的交互体验

### 🔥 技术栈
- **后端**: FastAPI + Uvicorn
- **前端**: HTML5 + CSS3 + JavaScript
- **文档**: Swagger UI + ReDoc
- **验证**: Pydantic
- **AI模型**: SentenceTransformers

---

🎊 **项目已成功完成！** 现在用户可以通过美观的Web界面或标准的REST API来使用AntSK文件切片服务的所有功能。
