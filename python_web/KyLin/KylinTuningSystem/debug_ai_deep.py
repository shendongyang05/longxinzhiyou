#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度调试AI调优功能的脚本
"""

import os
import sys
import django
import json
import re

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KylinTuningSystem.settings')
django.setup()

def debug_ai_deep():
    """深度调试AI调优功能"""
    
    print("🔍 深度调试AI调优功能")
    print("=" * 50)
    
    try:
        # 直接导入并调用AI函数
        from kylinApp.views.ai_api import ai_optimize_infer
        
        print("1. 调用AI推理函数...")
        result = ai_optimize_infer()
        
        print(f"2. 函数返回结果类型: {type(result)}")
        print(f"3. 函数返回结果长度: {len(result) if result else 0}")
        print(f"4. 函数返回结果前200字符: {repr(result[:200]) if result else 'None'}")
        
        # 检查结果是否为空或None
        if not result:
            print("   ❌ 函数返回空结果")
            return
        
        # 检查结果是否包含特殊字符
        print("5. 结果是否包含换行符:", '\n' in result)
        print("6. 结果是否包含制表符:", '\t' in result)
        print("7. 结果是否包含回车符:", '\r' in result)
        
        # 尝试清理结果
        print("\n8. 尝试清理结果...")
        cleaned_result = result.strip()
        print(f"   清理后长度: {len(cleaned_result)}")
        print(f"   清理后前100字符: {repr(cleaned_result[:100])}")
        
        # 尝试解析JSON
        print("\n9. 尝试解析JSON...")
        try:
            json_result = json.loads(cleaned_result)
            print("   ✅ 清理后的结果JSON解析成功")
            print(f"   JSON字段: {list(json_result.keys())}")
            
            # 检查必需字段
            required_fields = ["分析", "建议", "命令", "预期效果"]
            missing_fields = [field for field in required_fields if field not in json_result]
            
            if missing_fields:
                print(f"   ⚠️  缺少必需字段: {missing_fields}")
            else:
                print("   ✅ 所有必需字段都存在")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ 清理后的结果JSON解析失败: {e}")
            print(f"   错误位置: 第{e.lineno}行，第{e.colno}列")
            
            # 显示错误位置附近的内容
            lines = cleaned_result.split('\n')
            if e.lineno <= len(lines):
                print(f"   错误行内容: {repr(lines[e.lineno-1])}")
                if e.lineno > 1:
                    print(f"   上一行内容: {repr(lines[e.lineno-2])}")
                if e.lineno < len(lines):
                    print(f"   下一行内容: {repr(lines[e.lineno])}")
        
        # 尝试提取JSON部分
        print("\n10. 尝试提取JSON部分...")
        json_match = re.search(r'\{[\s\S]*\}', cleaned_result)
        if json_match:
            json_str = json_match.group(0)
            print(f"   提取的JSON字符串长度: {len(json_str)}")
            print(f"   提取的JSON字符串前100字符: {repr(json_str[:100])}")
            
            try:
                extracted_json = json.loads(json_str)
                print("   ✅ 提取的JSON解析成功")
                print(f"   JSON字段: {list(extracted_json.keys())}")
                
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
        
        # 显示完整结果（用repr显示特殊字符）
        print("\n11. 完整结果内容（用repr显示）:")
        print("-" * 50)
        print(repr(result))
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("📝 调试总结:")
    print("1. 检查函数返回结果的类型和内容")
    print("2. 检查结果是否包含特殊字符")
    print("3. 检查JSON解析失败的具体原因")
    print("4. 可能需要清理或预处理结果")

if __name__ == "__main__":
    debug_ai_deep() 