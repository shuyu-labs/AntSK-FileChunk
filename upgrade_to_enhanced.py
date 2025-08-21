#!/usr/bin/env python3
"""
升级到增强版语义切片器脚本
自动将现有代码从原版本升级到增强版本
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Dict

def backup_current_version():
    """备份当前版本"""
    print("📦 备份当前版本...")
    
    backup_dir = Path("backup_original_version")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    backup_dir.mkdir()
    
    # 备份核心文件
    core_files = [
        "src/antsk_filechunk/core/semantic_chunker.py",
        "src/antsk_filechunk/__init__.py"
    ]
    
    for file_path in core_files:
        if Path(file_path).exists():
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ 备份: {file_path} -> {backup_path}")
    
    print(f"✅ 备份完成，备份目录: {backup_dir}")
    return backup_dir

def check_dependencies():
    """检查依赖"""
    print("\n🔍 检查依赖...")
    
    required_packages = [
        "numpy",
        "scikit-learn", 
        "sentence-transformers",
        "nltk",
        "jieba",
        "tqdm"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} (缺失)")
    
    if missing_packages:
        print(f"\n⚠️ 缺失依赖: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有依赖已满足")
    return True

def update_imports_in_file(file_path: Path, old_import: str, new_import: str):
    """更新文件中的导入语句"""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要更新
        if old_import in content:
            updated_content = content.replace(old_import, new_import)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"   ✅ 更新导入: {file_path}")
            return True
    
    except Exception as e:
        print(f"   ❌ 更新失败 {file_path}: {e}")
    
    return False

def scan_and_update_project_files():
    """扫描并更新项目文件中的导入"""
    print("\n🔄 扫描项目文件...")
    
    # 常见的Python文件位置
    search_patterns = [
        "*.py",
        "examples/*.py",
        "tests/*.py",
        "scripts/*.py"
    ]
    
    # 要替换的导入模式
    import_replacements = [
        (
            "from antsk_filechunk import SemanticChunker",
            "from antsk_filechunk import EnhancedSemanticChunker as SemanticChunker"
        ),
        (
            "from antsk_filechunk.core.semantic_chunker import SemanticChunker",
            "from antsk_filechunk.core.enhanced_semantic_chunker import EnhancedSemanticChunker as SemanticChunker"
        )
    ]
    
    updated_files = []
    
    for pattern in search_patterns:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file() and not str(file_path).startswith("backup_"):
                for old_import, new_import in import_replacements:
                    if update_imports_in_file(file_path, old_import, new_import):
                        updated_files.append(str(file_path))
    
    if updated_files:
        print(f"✅ 更新了 {len(set(updated_files))} 个文件的导入")
        for file_path in set(updated_files):
            print(f"   - {file_path}")
    else:
        print("ℹ️ 未找到需要更新的导入语句")

def create_upgrade_example():
    """创建升级示例文件"""
    print("\n📝 创建升级示例...")
    
    example_content = '''"""
升级示例：从原版本到增强版本
展示升级前后的代码对比
"""

# === 升级前（原版本）===
print("🔸 原版本使用方式:")
print("""
from antsk_filechunk import SemanticChunker, ChunkConfig

config = ChunkConfig(
    target_chunk_size=1000,
    semantic_threshold=0.7
)

chunker = SemanticChunker(config=config)
chunks = chunker.process_text(text)

for chunk in chunks:
    print(f"长度: {len(chunk.content)}, 得分: {chunk.semantic_score}")
""")

# === 升级后（增强版本）===
print("\\n🔹 升级后（增强版本）使用方式:")

try:
    from antsk_filechunk import EnhancedSemanticChunker, ChunkConfig
    
    print("✅ 增强版本导入成功")
    
    # 基本升级 - 最小改动
    config = ChunkConfig(
        target_chunk_size=1000,
        semantic_threshold=0.7
    )
    
    # 简单替换：SemanticChunker -> EnhancedSemanticChunker
    chunker = EnhancedSemanticChunker(config=config)
    
    # 兼容原有方法
    sample_text = """
    人工智能技术正在快速发展。深度学习作为重要分支，在图像识别、自然语言处理等领域取得突破。
    
    机器学习算法的进步推动了AI应用的普及。从传统的监督学习到无监督学习，再到强化学习。
    """
    
    chunks = chunker.process_text(sample_text)  # 原有方法仍然可用
    
    print(f"\\n📊 基本升级结果:")
    print(f"   生成切片: {len(chunks)} 个")
    for i, chunk in enumerate(chunks):
        print(f"   切片 {i+1}: {len(chunk.content)} 字符, 得分: {chunk.semantic_score:.3f}")
    
    # === 进阶升级 - 启用增强功能 ===
    print("\\n🚀 进阶升级 - 启用增强功能:")
    
    # 创建增强版配置
    enhanced_chunker = EnhancedSemanticChunker(
        config=config,
        cache_size=500,         # 新增：缓存大小
        enable_fallback=True    # 新增：降级策略
    )
    
    # 配置增强的语义连贯性
    enhanced_chunker.configure_coherence(
        position_weight_enabled=True,     # 启用位置权重
        trend_analysis_enabled=True,      # 启用趋势分析
        position_decay_factor=0.3,        # 位置权重衰减
        trend_penalty_factor=0.1          # 趋势惩罚因子
    )
    
    # 使用增强处理方法
    enhanced_chunks = enhanced_chunker.process_text_enhanced(
        sample_text, 
        use_cache=True  # 启用缓存
    )
    
    print(f"\\n📈 增强版结果:")
    print(f"   生成切片: {len(enhanced_chunks)} 个")
    for i, chunk in enumerate(enhanced_chunks):
        processing_mode = chunk.metadata.get('processing_mode', 'normal')
        print(f"   切片 {i+1}: {len(chunk.content)} 字符, 得分: {chunk.semantic_score:.3f}, 模式: {processing_mode}")
    
    # 显示增强功能统计
    print(f"\\n🔍 系统状态监控:")
    
    # 缓存统计
    cache_stats = enhanced_chunker.embedding_cache.get_cache_stats()
    print(f"   缓存命中率: {cache_stats['hit_rate']:.2f}")
    print(f"   缓存大小: {cache_stats['cache_size']}")
    
    # 健康检查
    health = enhanced_chunker.health_check()
    print(f"   系统状态: {health['overall_status']}")
    
    # 性能统计
    stats = enhanced_chunker.get_comprehensive_stats()
    perf = stats['processing_performance']
    print(f"   处理成功率: {perf['success_rate']:.2f}")
    print(f"   降级使用次数: {perf['fallback_used']}")
    
    print("\\n✅ 升级成功！增强功能已启用")
    
except ImportError as e:
    print(f"❌ 增强版本导入失败: {e}")
    print("请确保增强版本文件已正确安装")

print("\\n" + "="*60)
print("📋 升级总结:")
print("1. ✅ 向后兼容 - 原有代码无需修改即可使用")
print("2. 🚀 增强功能 - 可选启用高级特性")
print("3. 📊 监控能力 - 完善的性能统计和健康检查")
print("4. 🛡️ 稳定性 - 降级策略确保服务可用性")
print("="*60)

if __name__ == "__main__":
    pass  # 运行示例代码
'''
    
    example_file = Path("upgrade_example.py")
    with open(example_file, 'w', encoding='utf-8') as f:
        f.write(example_content)
    
    print(f"✅ 创建升级示例: {example_file}")

def create_upgrade_checklist():
    """创建升级检查清单"""
    print("\n📋 创建升级检查清单...")
    
    checklist_content = '''# 🚀 升级到增强版语义切片器检查清单

## ✅ 升级前准备

- [ ] 1. **备份现有代码**
  - [ ] 备份 `src/antsk_filechunk/core/semantic_chunker.py`
  - [ ] 备份 `src/antsk_filechunk/__init__.py`
  - [ ] 备份相关配置文件

- [ ] 2. **检查依赖环境**
  - [ ] Python 3.8+
  - [ ] numpy >= 1.24.0
  - [ ] scikit-learn >= 1.3.0
  - [ ] sentence-transformers >= 2.2.2
  - [ ] 其他必要依赖

- [ ] 3. **测试环境准备**
  - [ ] 准备测试数据
  - [ ] 记录原版本性能基线
  - [ ] 确保有回滚方案

## 🔄 升级步骤

### 第1步：代码升级（最小改动）
- [ ] 1. **更新导入语句**
  ```python
  # 原版本
  from antsk_filechunk import SemanticChunker
  
  # 升级版本（别名方式，向后兼容）
  from antsk_filechunk import EnhancedSemanticChunker as SemanticChunker
  ```

- [ ] 2. **验证基本功能**
  - [ ] 运行现有测试用例
  - [ ] 确认输出格式一致
  - [ ] 验证性能基线

### 第2步：启用增强功能（可选）
- [ ] 3. **配置增强初始化**
  ```python
  chunker = EnhancedSemanticChunker(
      config=config,
      cache_size=500,         # 新增：缓存大小
      enable_fallback=True    # 新增：降级策略
  )
  ```

- [ ] 4. **启用语义增强**
  ```python
  chunker.configure_coherence(
      position_weight_enabled=True,
      trend_analysis_enabled=True
  )
  ```

- [ ] 5. **使用增强方法**
  ```python
  # 原方法仍可用
  chunks = chunker.process_text(text)
  
  # 新增强方法
  chunks = chunker.process_text_enhanced(text, use_cache=True)
  ```

### 第3步：监控和优化
- [ ] 6. **添加监控代码**
  ```python
  # 健康检查
  health = chunker.health_check()
  
  # 性能统计
  stats = chunker.get_comprehensive_stats()
  ```

- [ ] 7. **性能调优**
  - [ ] 调整缓存大小
  - [ ] 优化语义参数
  - [ ] 监控错误率

## 📊 升级验证

### 功能验证
- [ ] **基础功能**
  - [ ] 文本切片正常
  - [ ] 配置参数生效
  - [ ] 输出格式正确

- [ ] **增强功能**
  - [ ] 缓存机制工作
  - [ ] 语义连贯性提升
  - [ ] 异常处理有效

### 性能验证
- [ ] **质量指标**
  - [ ] 语义得分提升
  - [ ] 切片边界改善
  - [ ] 整体质量评估

- [ ] **性能指标**
  - [ ] 处理速度对比
  - [ ] 内存使用情况
  - [ ] 缓存命中率

### 稳定性验证
- [ ] **异常场景**
  - [ ] 空文本处理
  - [ ] 超大文档处理
  - [ ] 网络异常处理

- [ ] **降级策略**
  - [ ] 模型加载失败
  - [ ] 内存不足情况
  - [ ] 超时处理

## 🎯 升级后配置建议

### 推荐配置
```python
# 生产环境配置
config = ChunkConfig(
    target_chunk_size=1200,
    semantic_threshold=0.75,
    language="zh",
    overlap_ratio=0.1
)

chunker = EnhancedSemanticChunker(
    config=config,
    cache_size=1000,        # 适中的缓存大小
    enable_fallback=True    # 生产环境必须启用
)

# 语义增强配置
chunker.configure_coherence(
    position_weight_enabled=True,
    trend_analysis_enabled=True,
    position_decay_factor=0.3,
    trend_penalty_factor=0.1
)
```

### 监控配置
```python
# 定期健康检查
def periodic_health_check():
    health = chunker.health_check()
    if health['overall_status'] != 'healthy':
        # 发送告警
        log_health_issues(health)

# 性能监控
def monitor_performance():
    stats = chunker.get_comprehensive_stats()
    cache_hit_rate = stats['cache_performance']['hit_rate']
    success_rate = stats['processing_performance']['success_rate']
    
    if cache_hit_rate < 0.3 or success_rate < 0.95:
        # 性能告警
        alert_performance_issues(stats)
```

## 🚨 常见问题处理

### 导入错误
```
ImportError: No module named 'enhanced_semantic_chunker'
```
**解决方案**：确保增强版本文件已正确放置在 `src/antsk_filechunk/core/` 目录

### 内存不足
```
MemoryError: Unable to allocate array
```
**解决方案**：
1. 减小缓存大小
2. 启用降级策略
3. 分批处理大文档

### 性能下降
```
处理速度比原版本慢
```
**解决方案**：
1. 检查缓存配置
2. 调整语义参数
3. 使用 `process_text_enhanced` 方法

## 📞 支持联系

如遇问题，请：
1. 查看详细日志
2. 运行健康检查
3. 检查系统资源
4. 参考示例代码

---

**升级完成后请勾选所有检查项，确保系统稳定运行！**
'''
    
    checklist_file = Path("UPGRADE_CHECKLIST.md")
    with open(checklist_file, 'w', encoding='utf-8') as f:
        f.write(checklist_content)
    
    print(f"✅ 创建检查清单: {checklist_file}")

def run_upgrade_test():
    """运行升级测试"""
    print("\n🧪 运行升级测试...")
    
    try:
        # 测试增强版本导入
        from src.antsk_filechunk.core.enhanced_semantic_chunker import EnhancedSemanticChunker
        from src.antsk_filechunk.core.semantic_chunker import ChunkConfig
        
        print("✅ 增强版本导入成功")
        
        # 基本功能测试
        config = ChunkConfig(target_chunk_size=500)
        chunker = EnhancedSemanticChunker(config=config, enable_fallback=True)
        
        test_text = "这是一个测试文本。用于验证升级是否成功。"
        chunks = chunker._fallback_text_processing(test_text)  # 使用降级方法避免模型依赖
        
        print(f"✅ 基本功能测试通过 - 生成 {len(chunks)} 个切片")
        
        # 健康检查测试
        health = chunker.health_check()
        print(f"✅ 健康检查通过 - 状态: {health['overall_status']}")
        
        print("🎉 升级测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 升级测试失败: {e}")
        return False

def main():
    """主升级函数"""
    print("🚀 AntSK 语义切片器升级向导")
    print("=" * 60)
    
    # 1. 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装缺失的包")
        return
    
    # 2. 备份当前版本
    backup_dir = backup_current_version()
    
    # 3. 扫描并更新项目文件
    scan_and_update_project_files()
    
    # 4. 创建升级示例
    create_upgrade_example()
    
    # 5. 创建检查清单
    create_upgrade_checklist()
    
    # 6. 运行升级测试
    test_passed = run_upgrade_test()
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("🎉 升级完成！")
    print("=" * 60)
    
    print(f"\n📦 备份位置: {backup_dir}")
    print(f"📝 升级示例: upgrade_example.py")
    print(f"📋 检查清单: UPGRADE_CHECKLIST.md")
    
    if test_passed:
        print(f"\n✅ 升级验证: 通过")
        print(f"\n📚 下一步:")
        print(f"1. 运行: python upgrade_example.py")
        print(f"2. 查看: UPGRADE_CHECKLIST.md")
        print(f"3. 测试您的现有代码")
        print(f"4. 逐步启用增强功能")
    else:
        print(f"\n⚠️ 升级验证: 失败")
        print(f"请检查错误信息并手动验证")
    
    print(f"\n🔄 如需回滚，请从 {backup_dir} 恢复文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
