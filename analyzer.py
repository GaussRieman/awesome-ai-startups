#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创业公司分析器核心逻辑
使用新的提示词模板进行一次性分析，并解析为结构化数据
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from models import StartupAnalysis
from llm_client import LLMClient


class StartupAnalyzer:
    """创业公司分析器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def _extract_key_elements(self, text: str, llm_response: str) -> Dict[str, Any]:
        """从LLM响应中提取关键要素"""
        elements = {}
        
        # 提取公司名称
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text[:200])
        if name_match:
            elements['company_name'] = name_match.group(1)
        
        # 提取成立时间
        founded_match = re.search(r'([0-9]{4}[-/年][0-9]{1,2}[-/月][0-9]{1,2}[日]?)', llm_response)
        if founded_match:
            elements['founded'] = founded_match.group(1)
        
        # 提取行业/领域
        sector_match = re.search(r'行业[：:]\s*([^\n]+)', llm_response)
        if sector_match:
            elements['sector'] = sector_match.group(1).strip()
        
        # 提取价值主张
        value_match = re.search(r'价值主张[：:]\s*([^\n]+)', llm_response)
        if value_match:
            elements['one_liner'] = value_match.group(1).strip()
        
        return elements
    
    def _extract_keywords(self, text: str, llm_response: str) -> List[Tuple[str, float]]:
        """提取关键词和权重"""
        all_text = text + " " + llm_response
        
        # 中文关键词
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', all_text)
        # 英文关键词
        english_words = re.findall(r'\b[A-Za-z]{3,}\b', all_text)
        
        # 停用词
        stop_words = {'公司', '我们', '以及', '一个', '的', '和', '是', '在', '对', '与', '及', '等'}
        
        # 统计词频
        word_freq = {}
        for word in chinese_words + english_words:
            if word not in stop_words and len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 转换为权重
        if word_freq:
            max_freq = max(word_freq.values())
            keywords = [(word, freq / max_freq) for word, freq in word_freq.items()]
            keywords.sort(key=lambda x: x[1], reverse=True)
            return keywords[:20]
        
        return []
    
    def _build_graph(self, text: str, llm_response: str) -> Dict[str, Any]:
        """构建简单的知识图谱"""
        graph = {"nodes": [], "edges": []}
        
        # 提取公司名称
        company_name = None
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text[:200])
        if name_match:
            company_name = name_match.group(1)
        
        if company_name:
            # 添加公司节点
            graph["nodes"].append({
                "id": f"company:{company_name.lower()}",
                "label": company_name,
                "type": "Company"
            })
            
            # 尝试提取创始人
            founder_match = re.search(r'创始人[：:]\s*([^\n]+)', llm_response)
            if founder_match:
                founder_name = founder_match.group(1).strip()
                graph["nodes"].append({
                    "id": f"person:{founder_name.lower()}",
                    "label": founder_name,
                    "type": "Person"
                })
                graph["edges"].append({
                    "source": f"company:{company_name.lower()}",
                    "target": f"person:{founder_name.lower()}",
                    "rel": "FOUNDED_BY"
                })
        
        return graph
    
    def analyze_startup(self, text: str, stream: bool = True) -> StartupAnalysis:
        """完整的创业公司分析流程"""
        print("🔍 开始分析创业公司...")
        
        try:
            # 使用新的提示词模板进行一次性分析，支持流式输出
            response = self.llm.call_llm(text, stream=stream)
            
            # 解析响应，构建结构化数据
            key_elements = self._extract_key_elements(text, response)
            keywords = self._extract_keywords(text, response)
            graph = self._build_graph(text, response)
            
            # 创建分析结果
            analysis = StartupAnalysis(
                extracted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source_text=text[:500] + "..." if len(text) > 500 else text,
                raw_response=response,
                key_elements=key_elements,
                graph=graph,
                keywords=keywords,
                sources=[{
                    "title": "原始文本分析",
                    "url": "N/A",
                    "level": "L1",
                    "captured_at": datetime.now().strftime("%Y-%m-%d")
                }]
            )
            
            return analysis
            
        except Exception as e:
            raise Exception(f"分析失败: {str(e)}") 