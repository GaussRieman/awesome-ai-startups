#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReportGenerator Pro (LLM + Graph + BI)
- 将 LLM 的结构化分析结果渲染为 Markdown / HTML 报告
- 内置可视化：投资评分雷达图、关系图谱（networkx）、轻量词云/关键词权重图
- 可选导出：PDF（需要 weasyprint / wkhtmltopdf）、PPTX（python-pptx）
- 设计为“即插即用”：没有某些依赖时自动降级，不影响主流程
"""

import os
import io
import base64
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

# 可选依赖
try:
    import matplotlib.pyplot as plt
    import numpy as np
except Exception:
    plt = None
    np = None

try:
    import networkx as nx
except Exception:
    nx = None

try:
    from jinja2 import Template
except Exception:
    Template = None

# ------------------------------
# 数据模型（与你现有的结构兼容即可）
# ------------------------------
@dataclass
class StartupAnalysis:
    extracted_at: str
    raw_response: str  # LLM 原文（可为 JSON/Markdown）
    key_elements: Dict[str, Any] = field(default_factory=dict)
    # graph: { "nodes":[{"id":"company:xxx","label":"Blue","type":"Company"},...],
    #          "edges":[{"source":"company:xxx","target":"person:yyy","rel":"FOUNDED_BY"}] }
    graph: Dict[str, Any] = field(default_factory=lambda: {"nodes": [], "edges": []})
    # scoring: 五维评分，若无则自动跳过雷达图
    scoring: Dict[str, float] = field(default_factory=dict)
    # sources: [{"title":"...","url":"...","level":"L1-L5","captured_at":"YYYY-MM-DD"}]
    sources: List[Dict[str, str]] = field(default_factory=list)
    # keywords: [(词,权重)] ；若不给则从 raw_response 简单统计（英文/数字/中文混合粗糙版）
    keywords: List[Tuple[str, float]] = field(default_factory=list)

# ------------------------------
# 工具函数：image->base64
# ------------------------------
def _fig_to_base64(figure) -> str:
    buf = io.BytesIO()
    figure.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    plt.close(figure)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ------------------------------
# 可视化：雷达图（五维评分）
# ------------------------------
def render_radar_base64(scoring: Dict[str, float]) -> Optional[str]:
    if not scoring or not plt or not np:
        return None

    # 只取 5 个关键维度（无则跳过）
    dims_order = [
        ("people", "团队"),
        ("market", "市场"),
        ("traction", "牵引力"),
        ("moat", "护城河"),
        ("financing", "融资"),
    ]
    values = []
    labels = []
    for k, label in dims_order:
        if k in scoring:
            labels.append(label)
            values.append(float(scoring[k]))
    if not values:
        return None

    # 闭合雷达
    values = np.array(values, dtype=float)
    theta = np.linspace(0, 2 * np.pi, len(values), endpoint=False)
    values = np.concatenate([values, values[:1]])
    theta = np.concatenate([theta, theta[:1]])

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(theta, values)  # 不指定颜色
    ax.fill(theta, values, alpha=0.1)
    ax.set_thetagrids(theta[:-1] * 180 / np.pi, labels)  # 角度标签
    ax.set_title("投资评分雷达图", pad=12)
    ax.grid(True)
    return _fig_to_base64(fig)

# ------------------------------
# 可视化：关系图谱（networkx），失败则用 Mermaid
# ------------------------------
def render_graph_base64(graph: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    返回: (base64_png, mermaid_fallback)
    """
    if not graph or (not graph.get("nodes") and not graph.get("edges")):
        return None, None

    # Mermaid fallback（总能返回）
    mermaid = _graph_to_mermaid(graph)

    if not nx or not plt:
        return None, mermaid

    try:
        G = nx.DiGraph()
        labels = {}
        for n in graph.get("nodes", []):
            nid = n.get("id", "")
            nlabel = n.get("label", nid)
            ntype = n.get("type", "Node")
            G.add_node(nid, label=nlabel, ntype=ntype)
            labels[nid] = f"{nlabel}\n({ntype})"

        for e in graph.get("edges", []):
            s = e.get("source")
            t = e.get("target")
            rel = e.get("rel", "")
            if s and t:
                G.add_edge(s, t, rel=rel)

        pos = nx.spring_layout(G, seed=42, k=0.8)
        fig = plt.figure(figsize=(6, 4.5))
        ax = fig.add_subplot(111)
        nx.draw_networkx_nodes(G, pos, node_size=800)  # 不指定颜色
        nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=12)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9)

        # 在边中标注 rel
        edge_labels = {(u, v): d.get("rel", "") for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        ax.set_axis_off()
        return _fig_to_base64(fig), mermaid
    except Exception:
        return None, mermaid

def _graph_to_mermaid(graph: Dict[str, Any]) -> str:
    # 生成简单的 Mermaid graph TD
    node_ids = {}
    lines = ["graph TD"]
    for i, n in enumerate(graph.get("nodes", [])):
        nid = n.get("id", f"n{i}")
        node_ids[nid] = nid.replace(":", "_").replace("-", "_")
        label = n.get("label", nid)
        ntype = n.get("type", "Node")
        lines.append(f'    {node_ids[nid]}["{label} ({ntype})"]')
    for e in graph.get("edges", []):
        s = node_ids.get(e.get("source", ""), None)
        t = node_ids.get(e.get("target", ""), None)
        rel = e.get("rel", "")
        if s and t:
            if rel:
                lines.append(f"    {s} -->|{rel}| {t}")
            else:
                lines.append(f"    {s} --> {t}")
    return "\n".join(lines)

# ------------------------------
# 可视化：轻量“词云/关键词权重图”
# 说明：不依赖 wordcloud；用柱状+变字号文本混合实现简版可视化
# ------------------------------
def render_keyword_cloud_base64(keywords: List[Tuple[str, float]], topk: int = 30) -> Optional[str]:
    if not plt or not keywords:
        return None
    # 取 topk，归一化
    kws = sorted(keywords, key=lambda x: x[1], reverse=True)[:topk]
    if not kws:
        return None
    weights = [w for _, w in kws]
    wmin, wmax = min(weights), max(weights)
    norm = [(w - wmin) / (wmax - wmin + 1e-9) for w in weights]

    fig = plt.figure(figsize=(6, 4.5))
    ax = fig.add_subplot(111)
    ax.bar(range(len(kws)), weights)  # 不指定颜色
    ax.set_xticks(range(len(kws)))
    ax.set_xticklabels([k for k, _ in kws], rotation=45, ha="right", fontsize=8)
    ax.set_title("关键词权重")
    fig.tight_layout()
    bar_b64 = _fig_to_base64(fig)

    # 变字号文本排布（简单实现）
    fig2 = plt.figure(figsize=(6, 4.5))
    ax2 = fig2.add_subplot(111)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 100)
    ax2.axis("off")
    x, y = 5, 90
    for i, ((word, w), v) in enumerate(zip(kws, norm)):
        fs = 8 + int(18 * v)
        ax2.text(x, y, word, fontsize=fs)
        x += max(10, len(word) * 5)
        if x > 90:
            x = 5
            y -= 10
            if y < 5:
                break
    cloud_b64 = _fig_to_base64(fig2)
    # 返回文本云（可嵌入报告）
    return cloud_b64 or bar_b64

# ------------------------------
# 渲染：Markdown（带 Mermaid 备选）
# ------------------------------
def render_markdown(ana: StartupAnalysis,
                    radar_b64: Optional[str],
                    graph_b64: Optional[str],
                    mermaid: Optional[str],
                    cloud_b64: Optional[str]) -> str:
    # 核心要素表
    ke = ana.key_elements or {}
    name = ke.get("company_name") or ke.get("name") or "N/A"
    founded = ke.get("founded") or ke.get("founded_date") or "N/A"
    sector = ke.get("sector") or ke.get("industry") or "N/A"
    one_liner = ke.get("one_liner") or ke.get("value_proposition") or ""
    desc = ke.get("description") or ke.get("product_description") or ""

    md = []
    md.append(f"# 🚀 创业公司分析报告 · {name}")
    md.append("")
    md.append(f"**生成时间**: {ana.extracted_at}")
    md.append("")
    md.append("## 🧩 核心要素")
    md.append("")
    md.append("| 要素 | 内容 |")
    md.append("|---|---|")
    md.append(f"| 公司名称 | {name} |")
    md.append(f"| 成立时间 | {founded} |")
    md.append(f"| 所属领域 | {sector} |")
    md.append(f"| 价值主张 | {one_liner or '—'} |")
    md.append(f"| 简介/产品 | {desc or '—'} |")
    md.append("")

    if radar_b64:
        md.append("## 📊 投资评分雷达图")
        md.append(f"![radar](data:image/png;base64,{radar_b64})")
        md.append("")

    md.append("## 🧠 LLM 分析摘要（原文）")
    md.append("")
    md.append(ana.raw_response.strip())
    md.append("")

    md.append("## 🔗 关系图谱")
    if graph_b64:
        md.append(f"![graph](data:image/png;base64,{graph_b64})")
    elif mermaid:
        md.append("```mermaid")
        md.append(mermaid)
        md.append("```")
    else:
        md.append("> 暂无图谱数据")
    md.append("")

    if cloud_b64:
        md.append("## ☁️ 关键词可视化")
        md.append(f"![keywords](data:image/png;base64,{cloud_b64})")
        md.append("")

    if ana.sources:
        md.append("## 🗂️ 证据与来源")
        md.append("")
        md.append("| 标题 | URL | 等级 | 抓取时间 |")
        md.append("|---|---|---|---|")
        for s in ana.sources:
            md.append(f"| {s.get('title','—')} | {s.get('url','—')} | {s.get('level','—')} | {s.get('captured_at','—')} |")
        md.append("")

    md.append("---")
    md.append("**数据与方法**：公开信息 + 知识图谱推理 + 大模型分析")
    md.append("")
    md.append("_本报告仅供参考，不构成投资建议。_")
    return "\n".join(md)

# ------------------------------
# 渲染：HTML（内嵌 base64 图片，含 Mermaid 备用）
# ------------------------------
_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{{ title }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB","Microsoft YaHei", Arial, sans-serif; margin: 24px; line-height: 1.55;}
  h1,h2 { margin: 16px 0 8px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
  .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }
  .muted { color: #6b7280; }
  .img { border:1px solid #e5e7eb; border-radius: 12px; padding: 8px; }
  pre { background: #0b1021; color:#e5e7eb; padding:12px; border-radius:8px; overflow:auto;}
</style>
</head>
<body>
  <h1>🚀 创业公司分析报告 · {{ company_name }}</h1>
  <div class="muted">生成时间：{{ extracted_at }}</div>

  <div class="grid" style="margin-top:16px;">
    <div class="card">
      <h2>🧩 核心要素</h2>
      <table>
        <tr><th>公司名称</th><td>{{ company_name }}</td></tr>
        <tr><th>成立时间</th><td>{{ founded }}</td></tr>
        <tr><th>所属领域</th><td>{{ sector }}</td></tr>
        <tr><th>价值主张</th><td>{{ one_liner }}</td></tr>
        <tr><th>简介/产品</th><td>{{ desc }}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>📊 投资评分雷达图</h2>
      {% if radar_b64 %}
        <img class="img" src="data:image/png;base64,{{ radar_b64 }}" alt="radar"/>
      {% else %}
        <div class="muted">暂无评分或依赖缺失</div>
      {% endif %}
    </div>
  </div>

  <div class="card" style="margin-top:16px;">
    <h2>🧠 LLM 分析摘要（原文）</h2>
    <pre>{{ raw_response }}</pre>
  </div>

  <div class="grid" style="margin-top:16px;">
    <div class="card">
      <h2>🔗 关系图谱</h2>
      {% if graph_b64 %}
        <img class="img" src="data:image/png;base64,{{ graph_b64 }}" alt="graph"/>
      {% elif mermaid %}
        <pre class="mermaid">{{ mermaid }}</pre>
        <div class="muted">（在支持 Mermaid 的环境中可直接渲染）</div>
      {% else %}
        <div class="muted">暂无图谱数据</div>
      {% endif %}
    </div>

    <div class="card">
      <h2>☁️ 关键词可视化</h2>
      {% if cloud_b64 %}
        <img class="img" src="data:image/png;base64,{{ cloud_b64 }}" alt="keywords"/>
      {% else %}
        <div class="muted">暂无关键词或依赖缺失</div>
      {% endif %}
    </div>
  </div>

  <div class="card" style="margin-top:16px;">
    <h2>🗂️ 证据与来源</h2>
    {% if sources %}
      <table>
        <thead><tr><th>标题</th><th>URL</th><th>等级</th><th>抓取时间</th></tr></thead>
        <tbody>
        {% for s in sources %}
          <tr>
            <td>{{ s.title or '—' }}</td>
            <td>{{ s.url or '—' }}</td>
            <td>{{ s.level or '—' }}</td>
            <td>{{ s.captured_at or '—' }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <div class="muted">暂无来源</div>
    {% endif %}
  </div>

  <div class="muted" style="margin-top:16px;">
    数据与方法：公开信息 + 知识图谱推理 + 大模型分析。<br/>
    本报告仅供参考，不构成投资建议。
  </div>
</body>
</html>
"""

def render_html(ana: StartupAnalysis,
                radar_b64: Optional[str],
                graph_b64: Optional[str],
                mermaid: Optional[str],
                cloud_b64: Optional[str]) -> str:
    ke = ana.key_elements or {}
    name = ke.get("company_name") or ke.get("name") or "N/A"
    founded = ke.get("founded") or ke.get("founded_date") or "N/A"
    sector = ke.get("sector") or ke.get("industry") or "N/A"
    one_liner = ke.get("one_liner") or ke.get("value_proposition") or "—"
    desc = ke.get("description") or ke.get("product_description") or "—"

    context = {
        "title": f"创业公司分析报告 · {name}",
        "company_name": name,
        "founded": founded,
        "sector": sector,
        "one_liner": one_liner,
        "desc": desc,
        "extracted_at": ana.extracted_at,
        "radar_b64": radar_b64,
        "graph_b64": graph_b64,
        "mermaid": mermaid,
        "cloud_b64": cloud_b64,
        "raw_response": ana.raw_response,
        "sources": ana.sources,
    }
    if Template:
        return Template(_HTML_TEMPLATE).render(**context)
    else:
        # 简易字符串替换（若 jinja2 不可用）
        html = _HTML_TEMPLATE
        for k, v in context.items():
            html = html.replace("{{ "+k+" }}", str(v if v is not None else ""))
        # 简单处理未用到的 Jinja 控制块：去掉
        import re
        html = re.sub(r"\{%.*?%\}", "", html, flags=re.S)
        html = re.sub(r"\{\{.*?\}\}", "", html)  # 清理残留
        return html

# ------------------------------
# 报告生成器（统一入口）
# ------------------------------
class ReportGeneratorPro:

    @staticmethod
    def _prepare_visuals(ana: StartupAnalysis) -> Dict[str, Optional[str]]:
        radar_b64 = render_radar_base64(ana.scoring) if ana.scoring else None
        graph_b64, mermaid = render_graph_base64(ana.graph)
        kws = ana.keywords or ReportGeneratorPro._auto_keywords(ana)
        cloud_b64 = render_keyword_cloud_base64(kws) if kws else None
        return {
            "radar_b64": radar_b64,
            "graph_b64": graph_b64,
            "mermaid": mermaid,
            "cloud_b64": cloud_b64
        }

    @staticmethod
    def to_markdown(ana: StartupAnalysis) -> str:
        vis = ReportGeneratorPro._prepare_visuals(ana)
        return render_markdown(ana, **vis)

    @staticmethod
    def to_html(ana: StartupAnalysis) -> str:
        vis = ReportGeneratorPro._prepare_visuals(ana)
        return render_html(ana, **vis)


    @staticmethod
    def save_all(ana: StartupAnalysis,
                 md_path: str = "startup_report.md",
                 html_path: str = "startup_report.html",
                 ) -> Dict[str, Optional[str]]:
        md = ReportGeneratorPro.to_markdown(ana)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)

        html = ReportGeneratorPro.to_html(ana)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)



        print("✅ 报告已生成：")
        print(f"- Markdown: {os.path.abspath(md_path)}")
        print(f"- HTML:     {os.path.abspath(html_path)}")


        return {
            "markdown": md_path,
            "html": html_path,
        }

# ------------------------------
# 使用示例（可删除）
# ------------------------------
if __name__ == "__main__":
    # Demo: 你可以把 LLM 输出的 structured JSON 解析后填入下面字段
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    demo = StartupAnalysis(
        extracted_at=now,
        raw_response="（这里填 LLM 的 One-Pager 文本或 JSON 节选）",
        key_elements={
            "company_name": "Blue",
            "founded": "2024-01-01",
            "sector": "AI, hardware, speech-recognition",
            "one_liner": "True voice control for your phone.",
            "description": "Voice assistant enabling hands-free operation across apps."
        },
        graph={
            "nodes": [
                {"id": "company:blue", "label": "Blue", "type": "Company"},
                {"id": "person:omar", "label": "Omar", "type": "Person"},
                {"id": "investor:yc", "label": "Y Combinator", "type": "Investor"},
            ],
            "edges": [
                {"source": "company:blue", "target": "person:omar", "rel": "FOUNDED_BY"},
                {"source": "investor:yc", "target": "company:blue", "rel": "INVESTED_IN"}
            ]
        },
        scoring={"people": 26, "market": 18, "traction": 12, "moat": 10, "financing": 6, "total": 72, "confidence": 0.65},
        sources=[{"title":"Company Website","url":"https://heyblue.com","level":"L2","captured_at":"2025-08-13"}],
        keywords=[("语音助手", 0.9), ("无障碍", 0.6), ("移动端", 0.5), ("场景", 0.4)]
    )
    ReportGeneratorPro.save_all(demo)
