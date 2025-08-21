#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API测试脚本 - 验证FastAPI服务是否正常工作
"""

import requests
import json
from pathlib import Path

def test_api():
    """测试API接口"""
    base_url = "http://localhost:8000"
    
    print("🧪 测试API接口...")
    
    # 测试健康检查
    print("1. 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 测试默认配置获取
    print("\n2. 测试获取默认配置...")
    try:
        response = requests.get(f"{base_url}/api/config/default")
        if response.status_code == 200:
            print("✅ 默认配置获取成功")
            config = response.json()
            print(f"   配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 配置获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试文本处理
    print("\n3. 测试文本处理接口...")
    test_text = """
    人工智能是计算机科学的一个分支，致力于开发能够模拟人类智能的系统。
    
    机器学习是人工智能的核心技术之一，通过算法使计算机能够从数据中学习。
    
    深度学习作为机器学习的子集，使用神经网络来处理复杂的模式识别任务。
    """
    
    try:
        data = {
            "text": test_text,
            "config": json.dumps({
                "min_chunk_size": 50,
                "max_chunk_size": 300,
                "target_chunk_size": 150,
                "language": "zh"
            })
        }
        
        response = requests.post(f"{base_url}/api/process-text", data=data)
        if response.status_code == 200:
            print("✅ 文本处理成功")
            result = response.json()
            print(f"   总切片数: {result['total_chunks']}")
            print(f"   处理时间: {result['processing_time']:.2f}秒")
            
            for i, chunk in enumerate(result['chunks'][:2], 1):  # 只显示前2个切片
                print(f"   切片 {i}: {len(chunk['content'])} 字符, 得分: {chunk['semantic_score']:.3f}")
        else:
            print(f"❌ 文本处理失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n🎉 API测试完成！")
    return True

if __name__ == "__main__":
    test_api()
