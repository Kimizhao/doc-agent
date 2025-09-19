#!/usr/bin/env python3
"""
文档一级标题提取助理 API 测试脚本

测试API的各个功能，包括文件上传、结构提取等。
"""

import json
import requests
from pathlib import Path

# API配置
API_BASE_URL = "http://127.0.0.1:53518"


def test_health():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_supported_formats():
    """测试支持格式接口"""
    print("\n📝 测试支持格式接口...")
    try:
        response = requests.get(f"{API_BASE_URL}/supported-formats")
        result = response.json()
        print(f"支持的格式: {result['supported_formats']}")
        return True
    except Exception as e:
        print(f"❌ 获取支持格式失败: {e}")
        return False


def create_test_document():
    """创建测试文档"""
    test_content = """
人工智能技术发展报告
2024年度总结

第一章：人工智能概述

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它致力于理解和构建智能实体。
AI技术正在快速发展，并在各个领域产生深远影响。

## 1.1 定义与发展历程

AI的定义包括多个层面：
- 模拟人类智能行为
- 机器学习和深度学习
- 自然语言处理

第二章：核心技术

本章将详细介绍AI的核心技术组成部分。

## 2.1 机器学习

机器学习是AI的重要分支，包括监督学习、无监督学习和强化学习。

### 2.1.1 监督学习
监督学习使用标记数据进行训练。

### 2.1.2 无监督学习
无监督学习处理未标记的数据。

## 2.2 深度学习

深度学习基于神经网络，能够处理复杂的模式识别任务。

第三章：应用领域

AI技术在多个领域都有广泛应用。

## 3.1 医疗健康
- 医学影像分析
- 药物发现
- 疾病诊断

## 3.2 金融服务
- 风险评估
- 算法交易
- 反欺诈检测

第四章：未来展望

AI技术将继续快速发展，预计在以下方面取得突破：
1. 通用人工智能(AGI)
2. 量子计算与AI结合
3. AI安全与伦理

结论

人工智能技术正在重塑我们的世界，带来前所未有的机遇和挑战。
    """

    test_file_path = "test_document.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    return test_file_path


def test_extract_sections():
    """测试文档结构提取接口"""
    print("\n📋 测试文档结构提取接口...")

    # 创建测试文档
    test_file_path = create_test_document()

    try:
        # 上传文件并提取结构
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{API_BASE_URL}/extract-sections", files=files)

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"文件名: {result['file_name']}")
            print(f"文件大小: {result['file_size']}")
            print(f"处理状态: {result['processing_status']}")
            print(f"提取到 {len(result['sections'])} 个章节:")

            for section in result["sections"]:
                print(f"\n{section['index']}. {section['title']}")
                print(f"内容预览: {section['content'][:100]}...")

            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 文档结构提取失败: {e}")
        return False
    finally:
        # 清理测试文件
        try:
            Path(test_file_path).unlink()
        except:
            pass


def test_api_info():
    """测试API基础信息接口"""
    print("\n📡 测试API基础信息接口...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        result = response.json()
        print(f"API名称: {result['message']}")
        print(f"版本: {result['version']}")
        print(f"可用端点: {list(result['endpoints'].keys())}")
        return True
    except Exception as e:
        print(f"❌ 获取API信息失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试文档一级标题提取助理 API")
    print("=" * 50)

    tests = [
        ("API基础信息", test_api_info),
        ("健康检查", test_health),
        ("支持格式", test_supported_formats),
        ("文档结构提取", test_extract_sections),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))

    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("🎉 所有测试通过！API工作正常。")
    else:
        print("⚠️  部分测试失败，请检查API服务状态。")


if __name__ == "__main__":
    main()
