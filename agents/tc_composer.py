import json
from tools.llm import call_llm
from tools.trace import append_trace


def tc_composer_agent(state):
    """
    根据测试类型、DRG 规则和病历样本，组稿生成测试用例初稿。
    严格遵循 docs/tc_spec.md 定义的章节结构和内容要求。
    """
    language = state.get("language", "zh")
    tc_type = state.get("tc_type", "normal")
    project_name = state.get("project_name", "MedReasonerAgent")
    drg_rules = state.get("drg_rules", {})
    medical_records = state.get("medical_records", {})

    # 根据测试类型选择不同的 prompt 模板
    if tc_type == "normal":
        prompt = _normal_prompt(project_name, language, drg_rules, medical_records)
    elif tc_type == "boundary":
        prompt = _boundary_prompt(project_name, language, drg_rules, medical_records)
    else:
        prompt = _abnormal_prompt(project_name, language, drg_rules, medical_records)

    draft = call_llm(prompt, metadata={"agent_system": "tcgen", "tc_type": tc_type})
    state["tc_draft"] = draft
    append_trace(state, "tc_composer", f"Composed {tc_type} test cases draft ({len(draft)} chars)")
    return state


def _format_drg_rules(drg_rules: dict) -> str:
    """将 DRG 规则格式化为 prompt 可用的文本（含实际 CN-DRG 查表数据）。"""
    lines = []

    # ── MDC 查表摘要 ──
    mdc_table = drg_rules.get("mdc_table", {})
    lines.append("## CN-DRG 2018 MDC 查表（ICD-10 诊断 → MDC）")
    lines.append("| MDC 编码 | MDC 名称 | ICD-10 前缀 | 编码示例 |")
    lines.append("|----------|----------|-------------|----------|")
    by_mdc = mdc_table.get("by_mdc", {})
    examples = mdc_table.get("examples", {})
    for mdc_code in sorted(by_mdc):
        info = by_mdc[mdc_code]
        prefixes = ", ".join(info["icd_prefixes"][:4])
        if len(info["icd_prefixes"]) > 4:
            prefixes += f" ...共{len(info['icd_prefixes'])}个"
        ex = examples.get(mdc_code, [])
        ex_str = "; ".join(ex[:2])
        lines.append(f"| {mdc_code} | {info['name']} | {prefixes} | {ex_str} |")
    lines.append(f"\n> 匹配规则: {mdc_table.get('lookup_rule', '')}")

    # ── ADRG 查表摘要 ──
    adrg_table = drg_rules.get("adrg_table", {})
    lines.append("\n## CN-DRG ADRG 查表（MDC + 手术编码 → ADRG）")
    lines.append("| MDC | 手术前缀 | ADRG | ADRG 名称 |")
    lines.append("|-----|----------|------|-----------|")
    for entry in adrg_table.get("surgical_entries", [])[:25]:
        lines.append(f"| {entry['mdc']} | {entry['proc_prefix']} | {entry['adrg']} | {entry['adrg_name']} |")
    if len(adrg_table.get("surgical_entries", [])) > 25:
        lines.append(f"| ... | ... | ... | （共{len(adrg_table['surgical_entries'])}条外科ADRG） |")
    lines.append(f"\n> 匹配规则: {adrg_table.get('lookup_rule', '')}")

    # 内科兜底
    medical = adrg_table.get("medical_fallback", [])
    lines.append("\n### 内科 ADRG 兜底（无手术匹配时使用）")
    lines.append("| MDC | ADRG | ADRG 名称 |")
    lines.append("|-----|------|-----------|")
    for entry in medical:
        lines.append(f"| {entry['mdc']} | {entry['adrg']} | {entry['adrg_name']} |")

    # ── CC/MCC 并发症编码 ──
    cc_mcc = drg_rules.get("cc_mcc_sets", {})
    lines.append("\n## 合并症/并发症编码（CC / MCC）")
    mcc_codes = cc_mcc.get("mcc_codes", [])
    cc_codes = cc_mcc.get("cc_codes", [])
    lines.append(f"\n### MCC 严重合并症（{len(mcc_codes)} 个）")
    lines.append("| 编码 | 说明 |")
    lines.append("|------|------|")
    _mcc_descriptions = {
        "A41.0": "败血症", "A41.1": "败血症", "A41.2": "败血症", "A41.5": "败血症",
        "A41.8": "败血症", "A41.9": "败血症",
        "C77.0": "淋巴结继发恶性肿瘤", "C77.1": "淋巴结继发恶性肿瘤",
        "C77.2": "淋巴结继发恶性肿瘤", "C77.3": "淋巴结继发恶性肿瘤",
        "C77.4": "淋巴结继发恶性肿瘤", "C77.5": "淋巴结继发恶性肿瘤",
        "C77.8": "淋巴结继发恶性肿瘤", "C77.9": "淋巴结继发恶性肿瘤",
        "D65": "弥散性血管内凝血",
        "G93.1": "缺氧性脑损伤",
        "I21.0": "急性心肌梗死", "I21.1": "急性心肌梗死", "I21.2": "急性心肌梗死",
        "I21.3": "急性心肌梗死", "I21.4": "急性心肌梗死", "I21.9": "急性心肌梗死",
        "I22.0": "再发心梗", "I22.1": "再发心梗", "I22.8": "再发心梗", "I22.9": "再发心梗",
        "I26.0": "肺栓塞", "I26.9": "肺栓塞",
        "I50.1": "重度心力衰竭", "I50.2": "重度心力衰竭", "I50.9": "重度心力衰竭",
        "J96.0": "呼吸衰竭", "J96.00": "呼吸衰竭", "J96.9": "呼吸衰竭",
        "K72.0": "肝功能衰竭", "K72.9": "肝功能衰竭",
        "N17.0": "急性肾衰竭", "N17.1": "急性肾衰竭", "N17.2": "急性肾衰竭",
        "N17.8": "急性肾衰竭", "N17.9": "急性肾衰竭",
        "R57.0": "休克", "R57.1": "休克", "R57.8": "休克", "R57.9": "休克",
        "R65.0": "全身炎症反应综合征", "R65.1": "全身炎症反应综合征",
        "R65.2": "全身炎症反应综合征", "R65.9": "全身炎症反应综合征",
    }
    for code in mcc_codes[:10]:
        desc = _mcc_descriptions.get(code, "")
        lines.append(f"| {code} | {desc} |")
    lines.append(f"| ... | （共 {len(mcc_codes)} 个 MCC 编码） |")

    lines.append(f"\n### CC 一般合并症（{len(cc_codes)} 个）")
    lines.append("| 编码 | 说明 |")
    lines.append("|------|------|")
    _cc_descriptions = {
        "B18.2": "慢性丙型肝炎", "D64.9": "贫血",
        "E10.0": "1型糖尿病", "E10.9": "1型糖尿病",
        "E11.0": "2型糖尿病", "E11.1": "2型糖尿病", "E11.9": "2型糖尿病",
        "E78.0": "高脂血症", "E78.1": "高脂血症", "E78.2": "高脂血症", "E78.5": "高脂血症",
        "E87.1": "低钠血症", "E87.6": "低钾血症",
        "F32.9": "抑郁症", "G47.3": "睡眠呼吸暂停",
        "I10": "原发性高血压", "I11.9": "高血压性心脏病",
        "I48.0": "房颤", "I48.1": "房颤", "I48.9": "房颤",
        "I49.9": "心律失常",
        "I63.8": "脑梗死", "I63.801": "腔隙性脑梗死", "I63.9": "脑梗死",
        "I64": "卒中",
        "J15.9": "肺炎", "J44.0": "COPD", "J44.1": "COPD", "J44.9": "COPD",
        "K66.0": "肠粘连", "K66.002": "肠粘连",
        "K76.8": "肝囊肿", "K76.807": "肝囊肿",
        "N18.3": "慢性肾脏病", "N18.4": "慢性肾脏病", "N18.5": "慢性肾脏病", "N18.9": "慢性肾脏病",
        "N39.0": "泌尿道感染",
        "Z98.8": "术后状态", "Z98.800": "术后状态",
    }
    for code in cc_codes[:12]:
        desc = _cc_descriptions.get(code, "")
        lines.append(f"| {code} | {desc} |")
    lines.append(f"| ... | （共 {len(cc_codes)} 个 CC 编码） |")

    lines.append(f"\n> 匹配规则: {cc_mcc.get('lookup_rule', '')}")

    # ── DRG 后缀规则 ──
    suffix = drg_rules.get("drg_suffix_rules", {})
    lines.append("\n## DRG 后缀规则（并发症等级 → 最终 DRG 编码）")
    lines.append("| 并发症等级 | 后缀 | 说明 |")
    lines.append("|-----------|------|------|")
    for level, desc in sorted(suffix.items()):
        lines.append(f"| {level} | {desc} |")

    # ── 入组判定逻辑 ──
    logic = drg_rules.get("drg_grouping_logic", {})
    lines.append("\n## DRG 入组判定逻辑（完整步骤）")
    for step in logic.get("steps", []):
        lines.append(f"- {step}")

    return "\n".join(lines)


def _format_medical_records(medical_records: dict) -> str:
    """将病历参考数据格式化为 prompt 可用的文本。"""
    lines = []

    # 病历模板
    template = medical_records.get("sample_template", {})
    lines.append("## 病历 JSON 模板")
    lines.append("```json")
    lines.append(json.dumps(template, ensure_ascii=False, indent=2))
    lines.append("```")

    # ICD-10 诊断编码
    icd10 = medical_records.get("icd10_diagnosis_ref", [])
    lines.append("\n## 可用 ICD-10 诊断编码参考")
    lines.append("| 编码 | 名称 | 类别 |")
    lines.append("|------|------|------|")
    for item in icd10[:20]:
        lines.append(f"| {item['code']} | {item['name']} | {item['category']} |")

    # ICD-9-CM-3 手术编码
    icd9 = medical_records.get("icd9_procedure_ref", [])
    lines.append("\n## 可用 ICD-9-CM-3 手术/操作编码参考")
    lines.append("| 编码 | 名称 | 类别 |")
    lines.append("|------|------|------|")
    for item in icd9:
        lines.append(f"| {item['code']} | {item['name']} | {item['category']} |")

    # DRG 分组示例
    drg_examples = medical_records.get("drg_group_examples", [])
    lines.append("\n## DRG 分组示例参考")
    lines.append("| DRG 编码 | 名称 | MDC | 类型 | 关键因素 |")
    lines.append("|----------|------|-----|------|----------|")
    for item in drg_examples:
        lines.append(f"| {item['drg_code']} | {item['drg_name']} | {item['mdc']} | {item['type']} | {item['factors']} |")

    return "\n".join(lines)


def _normal_prompt(project_name: str, language: str, drg_rules: dict, medical_records: dict) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/tc_spec.md 中「正常场景测试用例格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/tc_spec.md section 'Normal Scenario Test Cases Format'."
    )

    return f"""
You are a medical DRG test case designer generating NORMAL scenario test cases.
Normal scenarios test valid diagnosis + procedure combinations that correctly map to DRG groups.

Project: {project_name}
Description: MedReasonerAgent is a multi-agent biomedical knowledge graph reasoning system for CN-DRG 2018 grouping.

{_format_drg_rules(drg_rules)}

{_format_medical_records(medical_records)}

{spec_ref}

Generate a complete normal scenario test case document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering):

## 1. 测试概述
## 2. DRG 分组规则摘要
## 3. 测试场景设计
## 4. 测试用例
## 5. 测试数据

Content per section:
- ## 1. 测试概述: 测试目标、测试范围（覆盖哪些诊断类别和手术类型）、参考资料
- ## 2. DRG 分组规则摘要: 知识图谱关系表格、入组判定逻辑步骤
- ## 3. 测试场景设计: 场景分类说明、场景覆盖矩阵表格（场景编号 | 诊断 | 手术 | MDC | ADRG | 并发症 | 最终DRG | 覆盖说明）
- ## 4. 测试用例: 至少8个 TC-N-XX 编号的测试用例，每个用例使用标准表格格式（用例编号|用例名称|测试场景|前置条件|输入数据|预期DRG分组|预期置信度|测试步骤|预期结果），用例中的"输入数据"必须包含完整的病历 JSON
- ## 5. 测试数据: 病历样本汇总、预期 DRG 分组映射表

Input Data JSON Format (CRITICAL — every test case's 输入数据 must follow this EXACT structure):
```json
{{
  "性别": "男/女",
  "年龄": 整数,
  "主要诊断": {{ "疾病名称": "中文名称", "疾病编码": "ICD-10编码" }},
  "次要诊断列表": [{{ "疾病名称": "...", "疾病编码": "ICD-10编码" }}],
  "主要手术": {{ "手术名称": "中文名称", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }},
  "其他手术列表": [{{ "手术名称": "...", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }}]
}}
```

Expected DRG Format:
- Final DRG code uses CN-DRG 2018 format: ADRG编码 + 后缀数字
- 后缀: 5=无合并症(NONE), 9=一般合并症(CC), 1=严重合并症(MCC)
- Examples: GB29 (胃手术+CC), HC15 (胆道手术+无CC), EC29 (胸壁手术+CC), IC35 (关节置换+无CC)
- DRG codes should NEVER use letter suffixes like A/B (that's AR-DRG, not CN-DRG)

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型="正常场景测试用例", 文档版本, 生成日期, 生成方式, 状态, DRG版本
- Use Markdown tables where appropriate
- Each test case must have a unique TC-N-XX number (TC-N-01, TC-N-02, ... at least TC-N-08)
- Cover at least 3 different MDC (MDCF循环系统, MDCE呼吸系统, MDCG消化道, MDCH肝胆胰, MDCI骨骼肌肉)
- Cover at least 3 different procedure types (心血管手术, 消化系统手术, 骨科手术, 胸外科手术)
- Cover at least 2 DRG group types (内科 and 外科)
- Every test case MUST include a complete medical record JSON in the "输入数据" field using the CN-DRG field format (性别, 年龄, 主要诊断, 次要诊断列表, 主要手术, 其他手术列表)
- Use ONLY ICD-10 and ICD-9-CM-3 codes from the reference data and lookup tables provided above
- Expected DRG groups MUST use CN-DRG 2018 numeric suffix format (5/9/1), NEVER use A/B letter suffixes
- When predicting expected DRG, follow the 4-step grouping logic: MDC→ADRG→CC/MCC→Final DRG
- Document MUST end with: "*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- ABSOLUTELY NO "TODO", "TBD", "待定", "待补充" or any placeholder text anywhere in the entire document

Document title: # {project_name} 正常场景测试用例
"""


def _boundary_prompt(project_name: str, language: str, drg_rules: dict, medical_records: dict) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/tc_spec.md 中「边界场景测试用例格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/tc_spec.md section 'Boundary Scenario Test Cases Format'."
    )

    return f"""
You are a medical DRG test case designer generating BOUNDARY scenario test cases.
Boundary scenarios test how DRG grouping changes when key variables are at boundary conditions:
- Presence/absence of comorbidities/complications (CC): adding/removing CC codes changes DRG suffix (5↔9↔1)
- Age boundaries (pediatric vs adult, elderly thresholds)
- Multiple simultaneous procedures and their priority
- Gender-specific DRG groups

Project: {project_name}

{_format_drg_rules(drg_rules)}

{_format_medical_records(medical_records)}

{spec_ref}

Generate a complete boundary scenario test case document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering):

## 1. 测试概述
## 2. 边界条件分析
## 3. 测试场景设计
## 4. 测试用例
## 5. 测试数据

Content per section:
- ## 1. 测试概述: 测试目标、边界定义（说明哪些参数在边界上变化）
- ## 2. 边界条件分析: 合并症影响分析（添加/移除CC编码 → DRG后缀变化 5↔9↔1）、年龄边界分析（如 17/18岁、60/61岁、新生儿/成人）、多手术组合影响（手术优先级选择）、性别差异分析
- ## 3. 测试场景设计: 边界场景矩阵表格（场景编号 | 边界类型 | 变化因素 | 基线正常场景 | 预期影响）
- ## 4. 测试用例: 至少7个 TC-B-XX 编号的边界测试用例，每个用例使用标准表格格式（用例编号|用例名称|边界类型|变化因素|基线场景|变化描述|输入数据|预期DRG变化|测试步骤|预期结果），"基线场景"应引用 TC-N-XX 编号，"输入数据"必须包含完整病历 JSON
- ## 5. 测试数据: 边界病历样本汇总、对比分析表

Input Data JSON Format (SAME as normal scenarios — use CN-DRG field names):
```json
{{
  "性别": "男/女",
  "年龄": 整数,
  "主要诊断": {{ "疾病名称": "中文名称", "疾病编码": "ICD-10编码" }},
  "次要诊断列表": [{{ "疾病名称": "...", "疾病编码": "ICD-10编码" }}],
  "主要手术": {{ "手术名称": "中文名称", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }},
  "其他手术列表": [{{ "手术名称": "...", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }}]
}}
```

Expected DRG changes MUST use CN-DRG 2018 numeric suffix format: 5(NONE), 9(CC), 1(MCC).
For CC boundary tests: show the same ADRG with different suffixes (e.g., HC15 → HC19 when adding CC codes).

Format requirements:
- Meta information table at top: | 属性 | 内容 | with 文档类型="边界场景测试用例"
- Each test case must have a unique TC-B-XX number (TC-B-01, TC-B-02, ... at least TC-B-07)
- Cover all 4 boundary types: 合并症有无(≥2 cases), 年龄边界(≥2 cases), 多手术组合(≥1 case), 性别差异(≥1 case)
- Each "基线场景" field should reference a normal scenario like "TC-N-01" to show the comparison
- Every test case MUST include a complete medical record JSON using CN-DRG field format (性别, 年龄, 主要诊断, 次要诊断列表, 主要手术, 其他手术列表)
- Use ONLY ICD codes from the reference data and lookup tables
- Expected DRG codes MUST use numeric suffix (5/9/1), NEVER use A/B letter suffixes
- Document MUST end with: "*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text

Document title: # {project_name} 边界场景测试用例
"""


def _abnormal_prompt(project_name: str, language: str, drg_rules: dict, medical_records: dict) -> str:
    is_zh = language == "zh"
    spec_ref = (
        "请严格参照 docs/tc_spec.md 中「异常场景测试用例格式」章节规定的结构生成。"
        if is_zh else
        "Follow the structure defined in docs/tc_spec.md section 'Abnormal Scenario Test Cases Format'."
    )

    return f"""
You are a medical DRG test case designer generating ABNORMAL scenario test cases.
Abnormal scenarios test system behavior when given invalid, incomplete, or contradictory input:
- Invalid or mismatched ICD codes (codes not in MDC_TABLE, ADRG_TABLE, CC/MCC sets)
- Missing required fields (no 主要诊断, missing 年龄 or 性别)
- Logic conflicts (e.g., obstetric diagnosis with orthopedic procedure)
- Format errors (malformed JSON, wrong data types)

Project: {project_name}

{_format_drg_rules(drg_rules)}

{_format_medical_records(medical_records)}

{spec_ref}

Generate a complete abnormal scenario test case document in {'Chinese' if is_zh else 'English'}.

CRITICAL — You MUST use these EXACT markdown section headings (copy them verbatim, including the "##" prefix and numbering):

## 1. 测试概述
## 2. 异常条件分析
## 3. 测试场景设计
## 4. 测试用例
## 5. 测试数据

Content per section:
- ## 1. 测试概述: 测试目标、异常分类（编码错误/信息缺失/逻辑冲突/格式错误）
- ## 2. 异常条件分析: 编码错误类型分析（无效编码如 "XXXX.X" 不在MDC_TABLE、编码名称不匹配）、信息缺失类型分析（缺"主要诊断"字段、缺"年龄"/"性别"字段）、逻辑冲突类型分析（诊断与手术不匹配，如产科诊断+骨科手术）、格式错误分析（JSON格式错误、字段类型错误如 年龄="abc"）
- ## 3. 测试场景设计: 异常场景矩阵表格（场景编号 | 异常类型 | 触发条件 | 输入示例 | 预期系统行为）
- ## 4. 测试用例: 至少7个 TC-A-XX 编号的异常测试用例，每个用例使用标准表格格式（用例编号|用例名称|异常类型|触发条件|输入数据|预期错误码|预期错误信息|预期系统行为|测试步骤|预期结果），"输入数据"必须包含含错误的病历 JSON
- ## 5. 测试数据: 异常病历样本汇总、错误处理验证表

Input Data JSON Format for abnormal cases:
- 编码错误 cases: use CN-DRG field format but with codes like "XXXX.9" as 疾病编码 or "999.99" as 手术编码
- 信息缺失 cases: use CN-DRG field format but omit "主要诊断" or "年龄" fields
- 逻辑冲突 cases: use CN-DRG field format with mismatched diagnosis/procedure (e.g., 主要诊断.疾病编码="O80.0" + 主要手术.手术编码="81.54001")
- 格式错误 cases: use CN-DRG field format but with wrong types (e.g., 年龄="六十八", truncated JSON)

Valid CN-DRG JSON structure for reference:
```json
{{
  "性别": "男",
  "年龄": 整数,
  "主要诊断": {{ "疾病名称": "中文名称", "疾病编码": "ICD-10编码" }},
  "次要诊断列表": [{{ "疾病名称": "...", "疾病编码": "ICD-10编码" }}],
  "主要手术": {{ "手术名称": "中文名称", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }},
  "其他手术列表": [{{ "手术名称": "...", "手术编码": "ICD-9-CM-3编码", "手术级别": 1-4 }}]
}}
```

Expected system behavior for abnormal cases:
- 编码错误 → get_mdc() 返回 None, DRG result: N/A with confidence 0.0
- 信息缺失 → entity._parse_emr() 返回 None, 降级到 NLP 模式
- 逻辑冲突 → MDC 与 ADRG 不匹配, get_adrg() 可能返回内科兜底
- 格式错误 → json.loads() 抛出异常, 降级到 NLP 模式

Format requirements:
- Meta information table at top: | 属性 | 内容 | with 文档类型="异常场景测试用例"
- Each test case must have a unique TC-A-XX number (TC-A-01, TC-A-02, ... at least TC-A-07)
- Cover all 4 abnormal types: 编码错误(≥2 cases), 信息缺失(≥2 cases), 逻辑冲突(≥1 case), 格式错误(≥1 case)
- For 编码错误 cases, use clearly invalid ICD codes like "XXXX.9", "999.99", or codes that don't match their names
- For 信息缺失 cases, omit "主要诊断" or "年龄" fields from the CN-DRG JSON format
- For 逻辑冲突 cases, use diagnosis-surgery combos that make no medical sense (e.g., O80.0 顺产 + 81.54001 膝关节置换)
- For 格式错误 cases, provide truncated/malformed JSON or wrong field types
- Every test case MUST include a JSON block (even if it contains errors)
- Document MUST end with: "*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text

Document title: # {project_name} 异常场景测试用例
"""
