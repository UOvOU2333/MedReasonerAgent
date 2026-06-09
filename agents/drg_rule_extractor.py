from __future__ import annotations

from kg.drg_loader import (
    load_drg_graph, MDC_TABLE, ADRG_TABLE, MEDICAL_ADRG,
    CC_SET, MCC_SET, COMPLICATION_SUFFIX,
)
from tools.trace import append_trace


def drg_rule_extractor_agent(state):
    """
    从 DRG 知识图谱和 CN-DRG 查表中提取完整分组规则。
    纯计算步骤，不依赖 LLM。
    输出结构化的 DRG 分组规则（含实际 MDC/ADRG/CC 查表数据），供 tc_composer 使用。
    """
    # ── 1. 基础关系图（向后兼容）──
    all_edges = load_drg_graph()
    rules_by_relation: dict[str, list[dict]] = {}
    for edge in all_edges:
        rel = edge.get("relation", "unknown")
        if rel not in rules_by_relation:
            rules_by_relation[rel] = []
        rules_by_relation[rel].append(edge)

    # ── 2. MDC 查表摘要 ──
    # 按 MDC 分组，列出每个 MDC 覆盖的 ICD 前缀
    mdc_summary: dict[str, dict] = {}
    for icd_prefix, (mdc_code, mdc_name) in sorted(MDC_TABLE.items(),
                                                     key=lambda x: len(x[0]), reverse=True):
        if mdc_code not in mdc_summary:
            mdc_summary[mdc_code] = {"name": mdc_name, "icd_prefixes": [], "example_codes": []}
        mdc_summary[mdc_code]["icd_prefixes"].append(icd_prefix)
    # 每个 MDC 取 1-2 个代表性 ICD 编码作为示例
    _mdc_examples = {
        "MDCF": ["I21.3 (急性心梗)", "I10 (高血压)"],
        "MDCE": ["J15.9 (肺炎)", "J44.9 (COPD)"],
        "MDCG": ["C16.301 (胃窦恶性肿瘤)", "K66.002 (肠粘连)"],
        "MDCH": ["K83.105 (胆管狭窄)", "K80.0 (胆囊结石伴胆囊炎)"],
        "MDCI": ["M17.9 (膝关节骨性关节炎)", "S72.0 (股骨颈骨折)"],
        "MDCA": ["G93.1 (缺氧性脑损伤)"],
        "MDCK": ["E11.9 (2型糖尿病)"],
        "MDCL": ["N18.9 (慢性肾脏病)", "N39.0 (泌尿道感染)"],
        "MDCO": ["O80.0 (头位顺产)"],
        "MDCS": ["A41.9 (败血症)"],
    }

    # ── 3. ADRG 查表摘要 ──
    adrg_summary: list[dict] = []
    for key, (adrg_code, adrg_name) in sorted(ADRG_TABLE.items()):
        mdc, proc_prefix = key.split("|", 1)
        adrg_summary.append({
            "mdc": mdc, "proc_prefix": proc_prefix,
            "adrg": adrg_code, "adrg_name": adrg_name,
        })
    # 内科 ADRG 兜底
    medical_adrg_list: list[dict] = [
        {"mdc": mdc, "adrg": code, "adrg_name": name, "type": "medical_fallback"}
        for mdc, (code, name) in sorted(MEDICAL_ADRG.items())
    ]

    # ── 4. CC/MCC 并发症编码 ──
    cc_list = sorted(CC_SET)
    mcc_list = sorted(MCC_SET)

    # ── 5. DRG 后缀规则 ──
    suffix_rules = {
        "NONE": "5 (无合并症/并发症)",
        "CC": "9 (伴一般合并症/并发症)",
        "MCC": "1 (伴严重合并症/并发症)",
    }
    suffix_rules.update({k: v for k, v in COMPLICATION_SUFFIX.items()})

    # ── 6. 入组判定逻辑（精炼版）──
    grouping_steps = [
        "Step 1 — 确定 MDC: 取主要诊断 ICD-10 编码的前缀，在 MDC_TABLE 中按前缀长度降序匹配，"
        "取最长匹配。如 K83.105 → 前缀 K83 → MDCH（肝胆胰），而非 K → MDCG（消化道）。",
        "Step 2 — 确定 ADRG: 在匹配到的 MDC 下，将主要手术/操作 ICD-9-CM-3 编码前缀与 "
        "ADRG_TABLE 逐级比对（依次截取前5/4/3/2位）。若匹配到手术条目，则为外科 ADRG；"
        "若无匹配，回退到该 MDC 的内科 ADRG（MEDICAL_ADRG）。",
        "Step 3 — 判定 CC/MCC: 遍历所有次要诊断 ICD-10 编码，先在 MCC_SET 中精确查找，"
        "再在 CC_SET 中精确查找。命中 MCC 则计为严重合并症，命中 CC 则计为一般合并症，"
        "均不命中则为无合并症（NONE）。",
        "Step 4 — 组装最终 DRG: ADRG 编码 + 并发症后缀数字（NONE→5, CC→9, MCC→1）"
        " → 最终 DRG 编码。如 HC1 + NONE → HC15, GB2 + CC → GB29。",
    ]

    drg_rules = {
        "total_edges": len(all_edges),
        "relations": list(rules_by_relation.keys()),
        "rules_by_relation": rules_by_relation,

        # 新增：实际 CN-DRG 查表数据
        "mdc_table": {
            "total_entries": len(MDC_TABLE),
            "by_mdc": mdc_summary,
            "examples": _mdc_examples,
            "lookup_rule": "按 ICD 前缀长度降序匹配，最长匹配优先",
        },
        "adrg_table": {
            "total_surgical": len(adrg_summary),
            "surgical_entries": adrg_summary,
            "medical_fallback": medical_adrg_list,
            "lookup_rule": "手术编码前缀逐级匹配（5→4→3→2位），无匹配回退内科",
        },
        "cc_mcc_sets": {
            "mcc_count": len(mcc_list),
            "mcc_codes": mcc_list,
            "cc_count": len(cc_list),
            "cc_codes": cc_list,
            "lookup_rule": "精确匹配（大小写不敏感），MCC 优先于 CC",
        },
        "drg_suffix_rules": suffix_rules,

        # 入组逻辑（精炼版）
        "drg_grouping_logic": {
            "steps": grouping_steps,
            "key_factors": [
                "主要诊断 ICD-10 编码（决定 MDC）",
                "主要手术/操作 ICD-9-CM-3 编码（决定外科/内科 ADRG）",
                "次要诊断 ICD-10 编码（决定 CC/MCC/NONE 并发症等级）",
                "患者年龄（部分 ADRG 按年龄分层）",
                "患者性别（部分 MDC 按性别区分，如 MDCM/MDCN）",
            ],
        },

        # 向后兼容
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
    }

    state["drg_rules"] = drg_rules
    append_trace(state, "drg_rule_extractor",
                 f"Extracted CN-DRG rules: {len(MDC_TABLE)} MDC entries, "
                 f"{len(ADRG_TABLE)} ADRG entries, "
                 f"{len(MCC_SET)} MCC + {len(CC_SET)} CC codes")
    return state
