#!/usr/bin/env python3
"""
开发环境设置脚本
"""
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ 成功: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失败: {description}")
        print(f"错误信息: {e.stderr}")
        return False

def setup_development_environment():
    """设置开发环境"""
    print("=" * 50)
    print("AntSK-FileChunk 开发环境设置")
    print("=" * 50)
    
    commands = [
        ("python -m pip install --upgrade pip", "升级pip"),
        ("pip install -e .", "安装项目（可编辑模式）"),
        ("pip install -e .[dev]", "安装开发依赖"),
        ("python -m nltk.downloader punkt stopwords", "下载NLTK数据"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n⚠️  警告: {description} 失败，请手动执行: {command}")
    
    print("\n" + "=" * 50)
    print("开发环境设置完成！")
    print("=" * 50)
    
    print("\n下一步:")
    print("1. 运行测试: pytest tests/")
    print("2. 运行示例: python examples/demo.py")
    print("3. 查看文档: docs/guides/USER_GUIDE.md")

if __name__ == "__main__":
    setup_development_environment()
