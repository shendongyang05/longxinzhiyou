#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI调优功能的脚本
"""

import os
import sys
import django
import json
import re

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KylinTuningSystem.settings')
django.setup()

from kylinApp.views.ai_api import ai_optimize_infer

def test_ai_optimize():
    """测试AI调优功能"""
    
    print("🧠 测试AI调优功能")
    print("=" * 50)
    
    try:
        print("1. 调用AI推理...")
        result = ai_optimize_infer()
        
        print(f"2. AI返回结果长度: {len(result) if result else 0}")
        print(f"3. AI返回结果前100字符: {result[:100] if result else 'None'}")
        
        print("\n4. 尝试解析JSON...")
        
        # 尝试直接解析
        try:
            json_result = json.loads(result)
            print("   ✅ 直接解析JSON成功")
            print(f"   JSON内容: {json.dumps(json_result, indent=2, ensure_ascii=False)}")
            
            # 检查必需字段
            required_fields = ["分析", "建议", "命令", "预期效果"]
            missing_fields = [field for field in required_fields if field not in json_result]
            
            if missing_fields:
                print(f"   ⚠️  缺少必需字段: {missing_fields}")
            else:
                print("   ✅ 所有必需字段都存在")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ 直接解析JSON失败: {e}")
            
            # 尝试提取JSON部分
            print("\n5. 尝试提取JSON部分...")
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                json_str = json_match.group(0)
                print(f"   提取的JSON字符串: {json_str[:200]}...")
                
                try:
                    extracted_json = json.loads(json_str)
                    print("   ✅ 提取的JSON解析成功")
                    print(f"   提取的JSON内容: {json.dumps(extracted_json, indent=2, ensure_ascii=False)}")
                    
                    # 检查必需字段
                    required_fields = ["分析", "建议", "命令", "预期效果"]
                    missing_fields = [field for field in required_fields if field not in extracted_json]
                    
                    if missing_fields:
                        print(f"   ⚠️  提取的JSON缺少必需字段: {missing_fields}")
                    else:
                        print("   ✅ 提取的JSON包含所有必需字段")
                        
                except json.JSONDecodeError as e2:
                    print(f"   ❌ 提取的JSON解析失败: {e2}")
            else:
                print("   ❌ 未找到JSON格式的内容")
        
        print("\n6. 完整结果内容:")
        print("-" * 50)
        if result:
            # 尝试格式化显示
            try:
                # 如果结果是JSON，格式化显示
                parsed = json.loads(result)
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
            except:
                # 如果不是JSON，直接显示
                print(result)
        else:
            print("结果为空")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("📝 问题分析:")
    print("1. AI返回的结果可能不是标准JSON格式")
    print("2. 结果可能包含额外的文本内容")
    print("3. JSON字段名可能不匹配")
    print("4. 需要改进结果解析逻辑")

if __name__ == "__main__":
    test_ai_optimize() 