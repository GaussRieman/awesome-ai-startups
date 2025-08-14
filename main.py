#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创业公司分析器 - 主入口
使用增强版报告生成器，支持可视化图表
"""

import os
from llm_client import LLMClient
from analyzer import StartupAnalyzer
from report_generator import ReportGeneratorPro


def main():
    """主函数"""
    print("🚀 创业公司分析器启动")
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 OPENAI_API_KEY 环境变量")
        print("   在 .env 文件中添加: OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
        # 读取示例数据
        with open("data.txt", "r", encoding='utf-8') as f:
            sample_text = f.read()
        
        # 初始化 LLM 客户端
        llm_client = LLMClient(api_key=api_key)
        
        # 初始化分析器
        analyzer = StartupAnalyzer(llm_client)
        
        # 执行分析（启用流式输出）
        analysis = analyzer.analyze_startup(sample_text, stream=True)
        
        # 直接保存原始分析结果
        print("💾 保存原始分析结果...")
        with open("analysis_raw_result.md", "w", encoding="utf-8") as f:
            f.write(analysis.raw_response)
        
        print("✅ 分析完成！")
        print(f"📄 原始结果已保存到: analysis_raw_result.md")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main() 