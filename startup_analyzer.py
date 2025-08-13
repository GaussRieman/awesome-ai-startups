#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创业公司分析器 - 单文件版本
从文本输入中提取关键要素并生成一页纸分析报告
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

@dataclass
class CompanyInfo:
    """公司基础信息"""
    name: str
    founded_date: str
    website: str
    industry: str
    description: str
    value_proposition: str
    product_description: str
    story_line: str  # 创业故事线：痛点 + 解决方案 + 市场机会

@dataclass
class FounderInfo:
    """创始人信息"""
    name: str
    education: str
    key_experience: str
    personal_story: str  # 个人故事或关键经历与创业目标的关联
    vision_quote: str    # 创始人愿景或名言

@dataclass
class FundingInfo:
    """融资信息"""
    latest_round: str
    funding_date: str
    amount: str
    investors: str

@dataclass
class MarketInfo:
    """市场与竞争信息"""
    target_customers: str
    competitors: str
    market_trend: str    # 市场趋势和势能描述
    growth_rate: str     # 市场增长率
    market_size: str     # 潜在收入规模

@dataclass
class InvestmentScore:
    """投资评分维度"""
    team_strength: int      # 团队实力 (1-10)
    market_potential: int   # 市场潜力 (1-10)
    product_innovation: int # 产品创新 (1-10)
    competitive_advantage: int  # 竞争优势 (1-10)
    execution_ability: int  # 执行能力 (1-10)

@dataclass
class AnalysisInfo:
    """分析信号"""
    investment_view: str
    core_risks: List[str]
    catalysts: List[str]
    investment_score: InvestmentScore  # 投资评分
    key_insight: str  # 核心洞察：一句话表达投资价值或关注点

@dataclass
class StartupAnalysis:
    """完整的创业公司分析"""
    company: CompanyInfo
    founders: List[FounderInfo]
    funding: FundingInfo
    market: MarketInfo
    analysis: AnalysisInfo
    extracted_at: str
    source_text: str

class LLMClient:
    """LLM 客户端，支持 OpenAI 兼容接口"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "deepseek-chat")
        self.client = OpenAI(api_key=self.api_key)
        
        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")
    
    def call_llm(self, prompt: str, temperature: float = 0.1) -> str:
        """调用 LLM 接口"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
        ],
            max_tokens=8000,
            temperature=0.1,
            stream=False
        )
        return response.choices[0].message.content

class StartupAnalyzer:
    """创业公司分析器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def extract_company_info(self, text: str) -> CompanyInfo:
        """提取公司基础信息"""
        prompt = f"""
请从以下文本中提取公司基础信息，以JSON格式返回：

{text}

请提取以下信息：
- name: 公司名称
- founded_date: 成立日期（格式：YYYY-MM-DD，如果只有年份则用YYYY-01-01）
- website: 官网/域名
- industry: 行业/赛道
- description: 公司简介（100字以内）
- value_proposition: 一句话价值主张（≤20字）
- product_description: 产品/服务简要描述（50字以内）
- story_line: 创业故事线（一句话概括：创始人出发点 + 痛点 + 独特解决方案，≤50字）

返回格式：
{{
    "name": "公司名称",
    "founded_date": "2020-01-01",
    "website": "example.com",
    "industry": "行业",
    "description": "公司简介",
    "value_proposition": "价值主张",
    "product_description": "产品描述",
    "story_line": "创业故事线"
}}
"""
        
        response = self.llm.call_llm(prompt)
        print("response", response)
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return CompanyInfo(**data)
            else:
                raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"解析公司信息失败: {str(e)}")
    
    def extract_founders(self, text: str) -> List[FounderInfo]:
        """提取创始人信息"""
        prompt = f"""
请从以下文本中提取创始人信息，以JSON格式返回：

{text}

请提取以下信息：
- name: 创始人姓名
- education: 教育背景
- key_experience: 关键经历（名企/创业/技术相关）
- personal_story: 个人故事或关键经历与创业目标的关联（≤30字）
- vision_quote: 创始人愿景或名言（≤20字，用引号包围）

返回格式：
{{
    "founders": [
        {{
            "name": "创始人姓名",
            "education": "教育背景",
            "key_experience": "关键经历",
            "personal_story": "个人故事",
            "vision_quote": "愿景名言"
        }}
    ]
}}
"""
        
        response = self.llm.call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return [FounderInfo(**founder) for founder in data.get("founders", [])]
            else:
                raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"解析创始人信息失败: {str(e)}")
    
    def extract_funding(self, text: str) -> FundingInfo:
        """提取融资信息"""
        prompt = f"""
请从以下文本中提取融资信息，以JSON格式返回：

{text}

请提取以下信息：
- latest_round: 最近轮次（如A轮、B轮、种子轮等）
- funding_date: 融资日期（格式：YYYY-MM-DD，如果只有年份则用YYYY-01-01）
- amount: 金额或区间
- investors: 投资方（领投/跟投）

返回格式：
{{
    "latest_round": "轮次",
    "funding_date": "2023-01-01",
    "amount": "金额",
    "investors": "投资方"
}}
"""
        
        response = self.llm.call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return FundingInfo(**data)
            else:
                raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"解析融资信息失败: {str(e)}")
    
    def extract_market_info(self, text: str) -> MarketInfo:
        """提取市场与竞争信息"""
        prompt = f"""
请从以下文本中提取市场与竞争信息，以JSON格式返回：

{text}

请提取以下信息：
- target_customers: 主要目标客户/使用场景
- competitors: 主要竞品或替代方案（1-2个）
- market_trend: 市场趋势和势能描述（为什么这个赛道现在机会最大，≤40字）
- growth_rate: 市场增长率（如"年增长30%"或"快速增长"）
- market_size: 潜在收入规模（如"千亿市场"或"百亿美元机会"）

返回格式：
{{
    "target_customers": "目标客户",
    "competitors": "竞品",
    "market_trend": "市场趋势",
    "growth_rate": "增长率",
    "market_size": "市场规模"
}}
"""
        
        response = self.llm.call_llm(prompt)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return MarketInfo(**data)
            else:
                raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"解析市场信息失败: {str(e)}")
    
    def generate_analysis(self, text: str, company_info: CompanyInfo) -> AnalysisInfo:
        """生成分析信号"""
        prompt = f"""
基于以下公司信息和文本，生成投资分析：

公司信息：
- 名称：{company_info.name}
- 行业：{company_info.industry}
- 价值主张：{company_info.value_proposition}
- 产品描述：{company_info.product_description}

文本内容：
{text}

请生成以下分析，以JSON格式返回：
- investment_view: 投资观点（Invest/Track/Pass 或文字描述）
- core_risks: 核心风险（1-3条）
- catalysts: 潜在催化因素（1-3条）
- investment_score: 投资评分（1-10分，5个维度）
- key_insight: 核心洞察（一句话表达投资价值或关注点，≤30字）

返回格式：
{{
    "investment_view": "投资观点",
    "core_risks": ["风险1", "风险2", "风险3"],
    "catalysts": ["催化因素1", "催化因素2", "催化因素3"],
    "investment_score": {{
        "team_strength": 8,
        "market_potential": 7,
        "product_innovation": 9,
        "competitive_advantage": 6,
        "execution_ability": 7
    }},
    "key_insight": "核心洞察"
}}
"""
        
        response = self.llm.call_llm(prompt, temperature=0.3)
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # 处理投资评分
                if 'investment_score' in data:
                    score_data = data['investment_score']
                    data['investment_score'] = InvestmentScore(**score_data)
                return AnalysisInfo(**data)
            else:
                raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise Exception(f"生成分析失败: {str(e)}")
    
    def analyze_startup(self, text: str) -> StartupAnalysis:
        """完整的创业公司分析流程"""
        print("🔍 开始分析创业公司...")
        
        # 提取公司基础信息
        print("📋 提取公司基础信息...")
        company_info = self.extract_company_info(text)
        
        # 提取创始人信息
        print("👥 提取创始人信息...")
        founders = self.extract_founders(text)
        
        # 提取融资信息
        print("💰 提取融资信息...")
        funding = self.extract_funding(text)
        
        # 提取市场信息
        print("📊 提取市场与竞争信息...")
        market = self.extract_market_info(text)
        
        # 生成分析
        print("🧠 生成投资分析...")
        analysis = self.generate_analysis(text, company_info)
        
        return StartupAnalysis(
            company=company_info,
            founders=founders,
            funding=funding,
            market=market,
            analysis=analysis,
            extracted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_text=text[:500] + "..." if len(text) > 500 else text
        )

class VisualElements:
    """可视化元素生成器"""
    
    @staticmethod
    def get_signal_light(score: int) -> str:
        """获取信号灯状态"""
        if score >= 8:
            return "🟢"  # 绿色
        elif score >= 6:
            return "🟡"  # 黄色
        else:
            return "🔴"  # 红色
    
    @staticmethod
    def get_risk_icon(risk_type: str) -> str:
        """获取风险图标"""
        risk_icons = {
            "监管": "📋",
            "技术": "⚙️",
            "市场": "📊",
            "竞争": "🏆",
            "团队": "👥",
            "资金": "💰",
            "执行": "🎯"
        }
        for key, icon in risk_icons.items():
            if key in risk_type:
                return icon
        return "⚠️"
    
    @staticmethod
    def get_catalyst_icon(catalyst_type: str) -> str:
        """获取催化因素图标"""
        catalyst_icons = {
            "技术": "🚀",
            "市场": "📈",
            "合作": "🤝",
            "融资": "💰",
            "政策": "📋",
            "人才": "👨‍💼"
        }
        for key, icon in catalyst_icons.items():
            if key in catalyst_type:
                return icon
        return "✨"
    
    @staticmethod
    def generate_radar_chart_markdown(score: InvestmentScore) -> str:
        """生成雷达图的 Markdown 表示"""
        chart = f"""
### 📊 投资评分雷达图

```
团队实力:     {'█' * score.team_strength}{'░' * (10 - score.team_strength)} {score.team_strength}/10 {VisualElements.get_signal_light(score.team_strength)}
市场潜力:     {'█' * score.market_potential}{'░' * (10 - score.market_potential)} {score.market_potential}/10 {VisualElements.get_signal_light(score.market_potential)}
产品创新:     {'█' * score.product_innovation}{'░' * (10 - score.product_innovation)} {score.product_innovation}/10 {VisualElements.get_signal_light(score.product_innovation)}
竞争优势:     {'█' * score.competitive_advantage}{'░' * (10 - score.competitive_advantage)} {score.competitive_advantage}/10 {VisualElements.get_signal_light(score.competitive_advantage)}
执行能力:     {'█' * score.execution_ability}{'░' * (10 - score.execution_ability)} {score.execution_ability}/10 {VisualElements.get_signal_light(score.execution_ability)}
```

**图例**: █ 得分 | ░ 满分 | 🟢 优秀 | 🟡 良好 | 🔴 需关注
"""
        return chart

class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_markdown(analysis: StartupAnalysis) -> str:
        """生成 Markdown 格式的一页纸报告"""
        
        # 计算平均投资评分
        avg_score = (
            analysis.analysis.investment_score.team_strength +
            analysis.analysis.investment_score.market_potential +
            analysis.analysis.investment_score.product_innovation +
            analysis.analysis.investment_score.competitive_advantage +
            analysis.analysis.investment_score.execution_ability
        ) / 5
        
        # 生成总体信号灯
        overall_signal = VisualElements.get_signal_light(int(avg_score))
        
        report = f"""# {analysis.company.name} - 创业公司分析报告

**生成时间**: {analysis.extracted_at} | **总体评分**: {overall_signal} {avg_score:.1f}/10

---

## 🎬 创业故事线

> **"{analysis.company.story_line}"**

---

## 📋 公司概览

| 项目 | 内容 |
|------|------|
| **公司名称** | {analysis.company.name} |
| **成立日期** | {analysis.company.founded_date} |
| **官网/域名** | {analysis.company.website} |
| **行业/赛道** | {analysis.company.industry} |
| **价值主张** | {analysis.company.value_proposition} |

**公司简介**: {analysis.company.description}

**产品/服务**: {analysis.company.product_description}

---

## 👥 创始团队

"""
        
        for i, founder in enumerate(analysis.founders, 1):
            report += f"""### 创始人 {i}: {founder.name}
- **教育背景**: {founder.education}
- **关键经历**: {founder.key_experience}
- **个人故事**: {founder.personal_story}
- **愿景名言**: {founder.vision_quote}

"""
        
        report += f"""---

## 💰 融资信息

| 项目 | 内容 |
|------|------|
| **最近轮次** | {analysis.funding.latest_round} |
| **融资日期** | {analysis.funding.funding_date} |
| **金额** | {analysis.funding.amount} |
| **投资方** | {analysis.funding.investors} |

---

## 📊 市场与竞争

**主要目标客户**: {analysis.market.target_customers}

**主要竞品**: {analysis.market.competitors}

### 📈 市场趋势
**{analysis.market.market_trend}**

**市场增长率**: {analysis.market.growth_rate} | **市场规模**: {analysis.market.market_size}

---

## 🎯 投资分析

### 核心洞察
> **"{analysis.analysis.key_insight}"**

### 投资观点
**{analysis.analysis.investment_view}**

{VisualElements.generate_radar_chart_markdown(analysis.analysis.investment_score)}

### ⚠️ 核心风险
"""
        
        for i, risk in enumerate(analysis.analysis.core_risks, 1):
            icon = VisualElements.get_risk_icon(risk)
            report += f"{i}. {icon} {risk}\n"
        
        report += "\n### 🚀 潜在催化因素\n"
        for i, catalyst in enumerate(analysis.analysis.catalysts, 1):
            icon = VisualElements.get_catalyst_icon(catalyst)
            report += f"{i}. {icon} {catalyst}\n"
        
        report += f"""

---

## 📝 数据来源

- **分析时间**: {analysis.extracted_at}
- **数据来源**: 公开文本信息
- **分析方法**: AI 辅助分析

---

*本报告基于公开信息生成，仅供参考，不构成投资建议。*
"""
        
        return report
    
    @staticmethod
    def save_report(analysis: StartupAnalysis, output_path: str = "startup_analysis_report.md"):
        """保存报告到文件"""
        report = ReportGenerator.generate_markdown(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 报告已保存到: {output_path}")
        return output_path

def main():
    """主函数 - 示例用法"""
    print("🚀 创业公司分析器启动")
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请设置 OPENAI_API_KEY 环境变量")
        print("   在 .env 文件中添加: OPENAI_API_KEY=your_api_key_here")
        return
    
    # 示例文本
    with open("data.txt", "r") as f:
        sample_text = f.read()
        
    
    try:
        # 初始化 LLM 客户端
        llm_client = LLMClient(api_key=api_key)
        
        # 初始化分析器
        analyzer = StartupAnalyzer(llm_client)
        
        # 执行分析
        analysis = analyzer.analyze_startup(sample_text)
        
        # 生成报告
        report_path = ReportGenerator.save_report(analysis)
        
        print("✅ 分析完成！")
        print(f"📊 分析结果摘要:")
        print(f"   公司: {analysis.company.name}")
        print(f"   行业: {analysis.company.industry}")
        print(f"   投资观点: {analysis.analysis.investment_view}")
        print(f"   报告文件: {report_path}")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main() 