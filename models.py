#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
包含创业公司分析所需的所有数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


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
    """完整的创业公司分析 - 兼容新的报告生成器"""
    extracted_at: str = ""
    source_text: str = ""
    raw_response: str = ""  # LLM 原文（可为 JSON/Markdown）
    key_elements: Dict[str, Any] = field(default_factory=dict)  # 关键要素
    graph: Dict[str, Any] = field(default_factory=lambda: {"nodes": [], "edges": []})  # 知识图谱
    scoring: Dict[str, float] = field(default_factory=dict)  # 五维评分
    sources: List[Dict[str, str]] = field(default_factory=list)  # 数据来源
    keywords: List[Tuple[str, float]] = field(default_factory=list)  # 关键词权重
    
    # 兼容旧版本的字段
    company: Optional[CompanyInfo] = None
    founders: List[FounderInfo] = field(default_factory=list)
    funding: Optional[FundingInfo] = None
    market: Optional[MarketInfo] = None
    analysis: Optional[AnalysisInfo] = None 