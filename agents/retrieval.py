from kg.drg_loader import get_mdc, get_adrg, check_complications, resolve_drg
from tools.trace import append_trace


def retrieval_agent(state):
    """
    DRG 入组核心检索 Agent：
    - EMR 模式：执行 MDC→ADRG→CC 三步确定性查表
    - NLP 模式：回退到旧 KG 子图检索
    """
    emr = state.get("emr_data", {})

    if emr.get("principal_dx_code"):
        # ── EMR 模式：确定性入组 ──
        result = _do_drg_grouping(emr)
        state["drg_result"] = result
        state["subgraph"] = {
            "nodes": [result.get("mdc", ""), result.get("adrg", ""), result.get("drg", "")],
            "edges": result.get("reasoning_steps", []),
            "hops": 3,
            "mode": "cn-drg-lookup",
        }
        append_trace(state, "retrieval",
                     f"CN-DRG: {result.get('mdc', '?')}→{result.get('adrg', '?')}"
                     f"→{result.get('complication', '?')}→{result.get('drg', '?')}")
        return state

    # ── NLP 模式：旧 KG 检索 ──
    from kg.query import get_subgraph
    subgraph = get_subgraph(state["entities"], hops=2)
    state["subgraph"] = subgraph
    state["drg_result"] = {}
    append_trace(state, "retrieval", f"{len(subgraph.get('edges', []))} edges")
    return state


def _do_drg_grouping(emr: dict) -> dict:
    """执行完整的 CN-DRG 入组逻辑。"""
    reasoning = []
    confidence_factors = []

    # Step 1: MDC
    mdc_result = get_mdc(emr["principal_dx_code"])
    if not mdc_result:
        return {
            "drg": "N/A", "drg_name": "无法分组",
            "mdc": "N/A", "adrg": "N/A", "complication": "N/A",
            "confidence": 0.0, "reasoning_steps": ["主诊断编码无法匹配任何 MDC"],
            "warning": "AI-generated grouping; for clinical decision support only.",
        }
    mdc = mdc_result["mdc"]
    mdc_name = mdc_result["mdc_name"]
    reasoning.append(f"主诊断 {emr['principal_dx_code']} ({emr['principal_dx_name']}) → {mdc}（{mdc_name}）")
    confidence_factors.append(1.0)

    # Step 2: ADRG
    proc_codes = emr.get("all_proc_codes", [])
    adrg_result = get_adrg(mdc, proc_codes)
    if adrg_result:
        adrg = adrg_result["adrg"]
        adrg_name = adrg_result["adrg_name"]
        match_proc = adrg_result.get("matched_proc", "")
        group_type = adrg_result.get("type", "surgical")
        proc_info = f"（手术 {match_proc}）" if match_proc else "（内科）"
        reasoning.append(f"手术 {proc_codes} → ADRG {adrg}（{adrg_name}）{proc_info}")
        confidence_factors.append(1.0 if match_proc else 0.7)
    else:
        adrg = "N/A"
        adrg_name = "未知 ADRG"
        reasoning.append(f"手术 {proc_codes} → 无匹配 ADRG")
        confidence_factors.append(0.3)

    # Step 3: CC/MCC
    complication = check_complications(emr.get("secondary_dx_codes", []))
    comp_level = complication["level"]
    if comp_level == "MCC":
        reasoning.append(f"次要诊断含严重合并症: {complication['matched_mcc']}")
        confidence_factors.append(0.9)
    elif comp_level == "CC":
        reasoning.append(f"次要诊断含一般合并症: {complication['matched_cc']}")
        confidence_factors.append(0.95)
    else:
        reasoning.append("次要诊断无合并症/并发症 → 无 CC")
        confidence_factors.append(1.0)

    # Step 4: 最终 DRG
    drg = resolve_drg(adrg, comp_level) if adrg != "N/A" else "N/A"
    reasoning.append(f"最终 DRG: {adrg} + {comp_level} → {drg}")

    # 置信度：各步骤置信度的加权平均
    confidence = round(sum(confidence_factors) / len(confidence_factors), 2) if confidence_factors else 0.0

    return {
        "drg": drg,
        "drg_name": adrg_name if adrg != "N/A" else "无法分组",
        "mdc": mdc,
        "mdc_name": mdc_name,
        "adrg": adrg,
        "adrg_name": adrg_name,
        "complication": comp_level,
        "complication_detail": complication,
        "confidence": confidence,
        "reasoning_steps": reasoning,
        "warning": "AI-assisted DRG grouping result; for clinical decision support only. Confirm with licensed coding professionals.",
    }
