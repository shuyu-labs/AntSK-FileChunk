#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证AntSK文件切片服务
"""

import requests
import json

def test_text_chunking():
    """测试文本切片功能"""
    
    # 测试文本
    test_text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

深度学习是机器学习的子集，是一种以人工神经网络为架构，对数据进行表征学习的算法。深度学习已经在语音识别、图像识别、自然语言处理等领域取得了重大突破。

自然语言处理是人工智能和语言学领域的分支学科。此领域探讨如何处理及运用自然语言。自然语言认知则是指让电脑"懂"人类的语言。

机器学习是一种数据分析的自动化方法。它是人工智能的一个分支，基于数据构建数学模型，以便进行预测或决策，而无需进行明确编程。
    """
    
    # API 请求 (使用Form数据格式)
    url = "http://localhost:8000/api/process-text"
    payload = {
        "text": test_text,
        "target_chunk_size": 200,
        "semantic_threshold": 0.7,
        "language": "zh"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ 测试成功！")
            print(f"📊 生成了 {len(result['chunks'])} 个切片")
            print("\n切片结果预览：")
            for i, chunk in enumerate(result['chunks'][:2]):  # 只显示前2个
                print(f"\n📄 切片 {i+1}:")
                print(f"   内容: {chunk['content'][:100]}...")
                print(f"   语义得分: {chunk['semantic_score']:.3f}")
                print(f"   Token数量: {chunk['token_count']}")
            
            # 显示统计信息
            stats = result.get('statistics', {})
            if stats:
                print(f"\n📈 统计信息:")
                print(f"   平均长度: {stats.get('avg_length', 0):.1f}")
                print(f"   平均语义得分: {stats.get('avg_semantic_score', 0):.3f}")
                
        else:
            print(f"❌ 测试失败: {response.status_code}")
            print(response.text)
    except requests.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        print("💡 运行命令: python start_server.py")
    except Exception as e:
        print(f"❌ 测试出错: {e}")

def test_server_status():
    """测试服务器状态"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"⚠️ 服务器状态异常: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ 检查服务器状态出错: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AntSK 文件切片服务 - 快速测试")
    print("=" * 50)
    
    # 检查服务器状态
    if test_server_status():
        print("\n📝 测试文本切片功能...")
        test_text_chunking()
    
    print("\n🔗 更多测试请访问:")
    print("   • API文档: http://localhost:8000/docs")
    print("   • 测试页面: http://localhost:8000")
