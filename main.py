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
        
        # 执行分析
        analysis = analyzer.analyze_startup(sample_text)
        
        # 使用增强版报告生成器生成多种格式
        print("📊 生成可视化报告...")
        results = ReportGeneratorPro.save_all(
            analysis,
            md_path="startup_analysis_report.md",
            html_path="startup_analysis_report.html",
            pdf_path="startup_analysis_report.pdf",
            pptx_path="startup_analysis_report.pptx"
        )
        
        print("✅ 分析完成！")
        print(f"📄 报告文件:")
        for format_name, file_path in results.items():
            if file_path:
                print(f"   - {format_name.upper()}: {file_path}")
        
        # 显示分析结果摘要
        print("\n📊 分析结果摘要:")
        print("-" * 50)
        print(analysis.raw_response[:500] + "..." if len(analysis.raw_response) > 500 else analysis.raw_response)
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main() 