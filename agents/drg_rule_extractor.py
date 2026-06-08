from __future__ import annotations

from kg.drg_loader import load_drg_graph
from kg.query import get_subgraph
from tools.trace import append_trace


def drg_rule_extractor_agent(state):
    """
    从 DRG 知识图谱中提取分组规则。
    纯计算步骤，不依赖 LLM。
    输出结构化的 DRG 分组规则，供 tc_composer 使用。
    """
    # 加载完整的 DRG 知识图谱边
    all_edges = load_drg_graph()

    # 按关系类型分类
    rules_by_relation: dict[str, list[dict]] = {}
    for edge in all_edges:
        rel = edge.get("relation", "unknown")
        if rel not in rules_by_relation:
            rules_by_relation[rel] = []
        rules_by_relation[rel].append(edge)

    # 构建 DRG 入组规则的结构化描述
    drg_rules = {
        "total_edges": len(all_edges),
        "relations": list(rules_by_relation.keys()),
        "rules_by_relation": rules_by_relation,
        "graph_schema": {
            "entity_types": ["symptom", "disease", "drg_group", "treatment", "risk_factor", "test"],
            "relation_types": [
                {"name": "suggests", "from": "symptom", "to": "disease",
                 "description": "症状提示可能疾病"},
                {"name": "mapped_to", "from": "disease", "to": "drg_group",
                 "description": "疾病映射到 DRG 分组，是入组核心关系"},
                {"name": "treated_by", "from": "disease", "to": "treatment",
                 "description": "疾病对应治疗方式，影响外科/内科 DRG 判定"},
                {"name": "increases_risk_of", "from": "risk_factor", "to": "disease",
                 "description": "风险因素增加疾病概率，影响合并症/并发症判定"},
                {"name": "confirms_or_rules_out", "from": "test", "to": "disease",
                 "description": "检查项目确定或排除疾病"},
            ],
        },
        "drg_grouping_logic": {
            "steps": [
                "1. 根据主要诊断 (Principal Diagnosis) 确定 MDC (Major Diagnostic Category)",
                "2. 检查是否存在手术/操作 (Procedure)，决定外科 vs 内科 DRG",
                "3. 评估合并症/并发症 (CC/MCC) 是否存在，影响 DRG 严重程度分级",
                "4. 考虑年龄、性别等人口学因素对 DRG 分组的影响",
                "5. 结合出院方式最终确定 DRG 分组编号",
            ],
            "key_factors": [
                "主要诊断 ICD 编码",
                "手术/操作 ICD-9-CM-3 编码",
                "次要诊断（合并症/并发症）",
                "患者年龄",
                "患者性别",
                "出院方式",
            ],
        },
    }

    state["drg_rules"] = drg_rules
    append_trace(state, "drg_rule_extractor",
                 f"Extracted DRG rules: {len(all_edges)} edges, "
                 f"{len(rules_by_relation)} relation types")
    return state
