#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - AntSK 文件切片服务
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from api_server import app

if __name__ == "__main__":
    # 创建必要的目录
    Path("temp").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    
    print("🚀 启动 AntSK 文件切片服务...")
    print("📖 API文档地址: http://localhost:8000/docs")
    print("🌐 测试页面地址: http://localhost:8000")
    print("=" * 50)
    
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境建议设为False
        log_level="info",
        access_log=True
    )
