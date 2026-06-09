import json
from tools.llm import call_llm
from tools.trace import append_trace


def entity_agent(state):
    """
    智能实体抽取 Agent：
    - 若 query 为合法 JSON 且含 "主要诊断" 等字段 → EMR 模式：直接解析结构化数据
    - 否则 → NLP 模式：调用 LLM 从自然语言中抽取医学实体
    """
    query = state.get("query", "").strip()
    language = state.get("language", "zh")

    # ── 尝试 EMR 模式 ──
    emr = _parse_emr(query)
    if emr:
        # 结构化输入：提取 ICD 编码作为 entities，保留完整 EMR 数据
        entities = list(emr.get("icd_codes", []))
        state["entities"] = entities
        state["emr_data"] = emr
        state["plan"] = {"mode": "drg-grouper", "input_type": "emr"}
        append_trace(state, "entity",
                     f"EMR mode: {emr['gender']} {emr['age']}y, "
                     f"dx={emr['principal_dx_code']}, "
                     f"proc={emr['principal_proc_code']}")
        return state

    # ── NLP 模式（向后兼容）──
    prompt = (
        f"Extract biomedical entities from this query. "
        f"Reply in {'Chinese' if language == 'zh' else 'English'}: {query}"
    )
    result = call_llm(prompt)
    entities = [item.strip() for item in result.split(",") if item.strip()]
    state["entities"] = entities
    state["emr_data"] = {}
    append_trace(state, "entity", f"NLP mode: {entities} (query was NOT valid JSON EMR)")
    return state


def _parse_emr(text: str) -> dict | None:
    """尝试将 query 解析为结构化电子病历 JSON。
    返回 None 表示非 EMR 输入。
    """
    # 清洗不可见字符（BOM、零宽空格、全角空格等）
    cleaned = text.strip()
    cleaned = cleaned.replace("﻿", "")   # BOM
    cleaned = cleaned.replace("​", "")   # 零宽空格
    cleaned = cleaned.replace("　", " ")  # 全角空格
    cleaned = cleaned.replace(" ", " ")  # 不间断空格

    # 自动修补：如果内容以 EMR 关键字段开头但没有外层 {}，自动包裹
    if not cleaned.startswith("{") and not cleaned.startswith("["):
        if '"性别"' in cleaned or '"年龄"' in cleaned or '"主要诊断"' in cleaned:
            cleaned = "{" + cleaned + "}"
            # 检查是否真的以 } 结尾，如果结尾缺 } 也补上
            # （上面已包裹，这里确保 JSON 合法）

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None

    # 必须包含 "主要诊断" 字段
    if not isinstance(data, dict) or "主要诊断" not in data:
        return None

    # 必须有有效 ICD 编码
    dx = data.get("主要诊断", {})
    if not isinstance(dx, dict) or not dx.get("疾病编码"):
        return None

    dx = data.get("主要诊断", {})
    if not isinstance(dx, dict) or "疾病编码" not in dx:
        return None

    # 提取所有 ICD 编码
    icd_codes = [dx.get("疾病编码", "")]
    sec_dx = data.get("次要诊断列表", [])
    if isinstance(sec_dx, list):
        for item in sec_dx:
            if isinstance(item, dict) and "疾病编码" in item:
                icd_codes.append(item["疾病编码"])

    # 提取手术编码
    main_proc = data.get("主要手术", {})
    other_procs = data.get("其他手术列表", [])

    all_proc_codes = []
    if isinstance(main_proc, dict) and "手术编码" in main_proc:
        all_proc_codes.append(main_proc["手术编码"])
    if isinstance(other_procs, list):
        for item in other_procs:
            if isinstance(item, dict) and "手术编码" in item:
                all_proc_codes.append(item["手术编码"])

    return {
        "gender": data.get("性别", ""),
        "age": data.get("年龄", 0),
        "principal_dx_code": dx.get("疾病编码", ""),
        "principal_dx_name": dx.get("疾病名称", ""),
        "secondary_dx_codes": [d.get("疾病编码", "") for d in sec_dx if isinstance(d, dict)],
        "secondary_dx_names": [d.get("疾病名称", "") for d in sec_dx if isinstance(d, dict)],
        "principal_proc_code": main_proc.get("手术编码", "") if isinstance(main_proc, dict) else "",
        "principal_proc_name": main_proc.get("手术名称", "") if isinstance(main_proc, dict) else "",
        "all_proc_codes": all_proc_codes,
        "icd_codes": list(set(icd_codes)),
    }
