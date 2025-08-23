#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Docker 部署测试脚本
用于测试 Docker 容器中的 AntSK-FileChunk 服务是否正常工作
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_health_check(base_url="http://localhost:8000"):
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_default_config(base_url="http://localhost:8000"):
    """测试默认配置接口"""
    print("\n🔍 测试默认配置接口...")
    try:
        response = requests.get(f"{base_url}/api/config/default", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ 默认配置获取成功")
            print(f"   最小切片大小: {config['min_chunk_size']}")
            print(f"   最大切片大小: {config['max_chunk_size']}")
            print(f"   目标切片大小: {config['target_chunk_size']}")
            print(f"   语义阈值: {config['semantic_threshold']}")
            return True
        else:
            print(f"❌ 配置获取失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 配置获取异常: {e}")
        return False

def test_text_processing(base_url="http://localhost:8000"):
    """测试文本处理接口"""
    print("\n🔍 测试文本处理接口...")
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    
    机器学习是人工智能的一个重要分支，它是一种通过算法使机器能够自动学习和改进的技术。机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据进行预测或决策。
    
    深度学习是机器学习的一个子集，它使用人工神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。
    
    自然语言处理（Natural Language Processing，NLP）是人工智能的另一个重要分支，它致力于让计算机能够理解、解释和生成人类语言。NLP技术被广泛应用于机器翻译、情感分析、文本摘要等任务。
    
    计算机视觉是人工智能的一个分支，它使计算机能够从图像或视频中获取信息。计算机视觉技术在自动驾驶、医疗诊断、安防监控等领域有着广泛的应用。
    """
    
    try:
        # 准备请求数据
        data = {
            'text': test_text.strip(),
            'config': json.dumps({
                'min_chunk_size': 100,
                'max_chunk_size': 500,
                'target_chunk_size': 300,
                'semantic_threshold': 0.7,
                'language': 'zh'
            })
        }
        
        print("   发送文本处理请求...")
        response = requests.post(f"{base_url}/api/process-text", data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文本处理成功")
            print(f"   切片数量: {result['total_chunks']}")
            print(f"   处理时间: {result['processing_time']:.2f}秒")
            
            # 显示前几个切片的信息
            for i, chunk in enumerate(result['chunks'][:3]):
                print(f"   切片 {i+1}: {len(chunk['content'])} 字符, 语义得分: {chunk['semantic_score']:.3f}")
                print(f"           内容预览: {chunk['content'][:50]}...")
            
            if len(result['chunks']) > 3:
                print(f"   ... 还有 {len(result['chunks']) - 3} 个切片")
            
            return True
        else:
            print(f"❌ 文本处理失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 文本处理异常: {e}")
        return False

def test_file_upload(base_url="http://localhost:8000"):
    """测试文件上传接口"""
    print("\n🔍 测试文件上传接口...")
    
    # 创建测试文件
    test_file_path = Path("temp/test_document.txt")
    test_file_path.parent.mkdir(exist_ok=True)
    
    test_content = """
    AntSK-FileChunk 语义文本切片服务

    项目简介
    AntSK-FileChunk 是一个基于语义理解的智能文本切片服务，专门用于处理长文档的语义分割。与传统的基于Token数量或固定长度的切分方式不同，本项目采用先进的语义分析技术，确保每个切片在语义上的完整性和连贯性。

    核心功能
    1. 语义感知切片：基于Transformer模型进行语义理解，确保切片边界的合理性
    2. 多格式支持：支持PDF、Word（.docx/.doc）、纯文本等多种文档格式
    3. 智能文档解析：自动识别和处理文档结构、表格、图片等特殊内容
    4. 自适应切片：根据内容特点动态调整切片大小，平衡语义完整性和处理效率

    技术特点
    本项目采用了多项先进技术，包括但不限于：
    - 基于sentence-transformers的语义向量计算
    - 智能边界检测算法
    - 自适应切片大小调整
    - 多维度质量评估体系

    应用场景
    AntSK-FileChunk 适用于多种应用场景：
    1. 知识库构建：为RAG系统提供高质量的文档切片
    2. 内容分析：对长文档进行结构化分析
    3. 信息检索：提高文档检索的准确性和相关性
    4. 文档处理：批量处理和分析大量文档
    """
    
    try:
        # 写入测试文件
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content.strip())
        
        # 准备上传
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {
                'config': json.dumps({
                    'min_chunk_size': 150,
                    'max_chunk_size': 600,
                    'target_chunk_size': 400,
                    'semantic_threshold': 0.75,
                    'language': 'zh'
                })
            }
            
            print("   上传测试文件...")
            response = requests.post(f"{base_url}/api/process-file", files=files, data=data, timeout=30)
        
        # 清理测试文件
        test_file_path.unlink(missing_ok=True)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文件上传处理成功")
            print(f"   文件名: {result['file_info']['filename']}")
            print(f"   文件大小: {result['file_info']['size']} 字节")
            print(f"   切片数量: {result['total_chunks']}")
            print(f"   处理时间: {result['processing_time']:.2f}秒")
            
            # 显示切片统计
            chunk_sizes = [len(chunk['content']) for chunk in result['chunks']]
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            print(f"   平均切片大小: {avg_size:.0f} 字符")
            print(f"   切片大小范围: {min(chunk_sizes) if chunk_sizes else 0} - {max(chunk_sizes) if chunk_sizes else 0} 字符")
            
            return True
        else:
            print(f"❌ 文件上传失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 文件上传异常: {e}")
        return False
    finally:
        # 确保清理测试文件
        test_file_path.unlink(missing_ok=True)

def test_web_interface(base_url="http://localhost:8000"):
    """测试Web界面"""
    print("\n🔍 测试Web界面...")
    try:
        # 测试主页
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ 主页访问正常")
        else:
            print(f"❌ 主页访问失败: HTTP {response.status_code}")
            return False
        
        # 测试API文档
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API文档访问正常")
        else:
            print(f"❌ API文档访问失败: HTTP {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Web界面测试异常: {e}")
        return False

def wait_for_service(base_url="http://localhost:8000", max_wait=60):
    """等待服务启动"""
    print(f"⏳ 等待服务启动 (最多等待 {max_wait} 秒)...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 服务已启动 (等待了 {i+1} 秒)")
                return True
        except:
            pass
        
        if i % 10 == 0 and i > 0:
            print(f"   仍在等待... ({i}/{max_wait})")
        
        time.sleep(1)
    
    print(f"❌ 服务启动超时 (等待了 {max_wait} 秒)")
    return False

def main():
    """主测试函数"""
    print("🚀 AntSK-FileChunk Docker 部署测试")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        print(f"使用自定义服务地址: {base_url}")
    
    # 等待服务启动
    if not wait_for_service(base_url):
        print("\n❌ 服务未启动，请先启动 Docker 容器")
        print("   使用命令: docker-compose up -d")
        print("   或者: python docker-start.py")
        return False
    
    # 执行测试
    tests = [
        ("健康检查", test_health_check),
        ("默认配置", test_default_config),
        ("文本处理", test_text_processing),
        ("文件上传", test_file_upload),
        ("Web界面", test_web_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func(base_url):
                passed += 1
            else:
                print(f"   ⚠️  {test_name} 测试失败")
        except Exception as e:
            print(f"   ❌ {test_name} 测试异常: {e}")
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Docker 部署成功！")
        print(f"\n🌐 服务地址:")
        print(f"   Web界面: {base_url}")
        print(f"   API文档: {base_url}/docs")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查服务配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
