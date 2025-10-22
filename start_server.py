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
from api_server import app, IMAGE_BASE_URL
import socket

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

if __name__ == "__main__":
    # 创建必要的目录
    Path("temp").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("static/images").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    
    # 获取本机IP
    local_ip = get_local_ip()
    port = 8000
    
    print("🚀 启动 AntSK 文件切片服务...")
    print("=" * 60)
    print(f"📖 本地访问: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{local_ip}:{port}")
    print(f"📚 API文档: http://{local_ip}:{port}/docs")
    print("=" * 60)
    
    if IMAGE_BASE_URL:
        print(f"🖼️  图片URL配置: {IMAGE_BASE_URL}")
    else:
        print(f"🖼️  图片URL: 自动检测 (当前: http://{local_ip}:{port})")
    
    print(f"💡 提示: 如需从外网访问,请在环境变量中设置 IMAGE_BASE_URL")
    print("=" * 60)
    
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境建议设为False
        log_level="info",
        access_log=True
    )
