#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 客户端
负责与各种LLM服务的通信
"""

import os
import json
import re
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from prompts import TOP_ANALYST_SYSTEM_PROMPT, TOP_ANALYST_USER_PROMPT

class LLMClient:
    """LLM 客户端，支持 OpenAI 兼容接口"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "deepseek-chat")
        
        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")
        
        # 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def call_llm(self, prompt: str, temperature: float = 0.1, max_tokens: int = 8000, stream: bool = False) -> str:
        """调用 LLM 接口"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TOP_ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": TOP_ANALYST_USER_PROMPT.format(text=prompt)},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # 流式输出
                full_response = ""
                print("🤖 AI 分析中...")
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        full_response += content
                print()  # 换行
                return full_response
            else:
                # 非流式输出
                return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def extract_json_from_response(self, response: str) -> dict:
        """从LLM响应中提取JSON数据"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError("无法解析JSON响应")
            else:
                raise ValueError("响应中未找到JSON格式数据")
    
    def call_with_json_extraction(self, prompt: str, temperature: float = 0.1) -> dict:
        """调用LLM并自动提取JSON响应"""
        response = self.call_llm(prompt, temperature)
        return self.extract_json_from_response(response) 