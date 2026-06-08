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
    """将 DRG 规则格式化为 prompt 可用的文本。"""
    schema = drg_rules.get("graph_schema", {})
    logic = drg_rules.get("drg_grouping_logic", {})

    lines = ["## DRG 知识图谱关系类型"]
    for rel in schema.get("relation_types", []):
        lines.append(f"- {rel['from']} --[{rel['name']}]--> {rel['to']}: {rel['description']}")

    lines.append("\n## DRG 入组判定逻辑")
    for step in logic.get("steps", []):
        lines.append(f"  {step}")

    lines.append("\n## 关键影响因素")
    for factor in logic.get("key_factors", []):
        lines.append(f"  - {factor}")

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
Description: MedReasonerAgent is a multi-agent biomedical knowledge graph reasoning system for DRG grouping.

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
- ## 3. 测试场景设计: 场景分类说明、场景覆盖矩阵表格（场景编号 | 诊断 | 手术 | DRG 分组 | 覆盖说明）
- ## 4. 测试用例: 至少8个 TC-N-XX 编号的测试用例，每个用例使用标准表格格式（用例编号|用例名称|测试场景|前置条件|输入数据|预期DRG分组|预期置信度|测试步骤|预期结果），用例中的"输入数据"必须包含完整的病历 JSON
- ## 5. 测试数据: 病历样本汇总、预期 DRG 分组映射表

Format requirements:
- Include the meta information table at the top: | 属性 | 内容 | with 项目名称, 文档类型="正常场景测试用例", 文档版本, 生成日期, 生成方式, 状态, DRG版本
- Use Markdown tables where appropriate
- Each test case must have a unique TC-N-XX number (TC-N-01, TC-N-02, ... at least TC-N-08)
- Cover at least 3 different diagnosis categories (循环系统, 呼吸系统, 消化系统, 骨骼肌肉)
- Cover at least 3 different procedure types (心血管手术, 消化系统手术, 骨科手术)
- Cover at least 2 DRG group types (内科 and 外科)
- Every test case MUST include a complete medical record JSON in the "输入数据" field using the provided template format
- Use accurate ICD-10 and ICD-9-CM-3 codes from the reference data
- Expected DRG groups should reference the DRG group examples provided
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
- Presence/absence of comorbidities/complications (CC)
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
- ## 2. 边界条件分析: 合并症影响分析、年龄边界分析（如 17/18岁、60/61岁、新生儿/成人）、多手术组合影响、性别差异分析
- ## 3. 测试场景设计: 边界场景矩阵表格（场景编号 | 边界类型 | 变化因素 | 基线正常场景 | 预期影响）
- ## 4. 测试用例: 至少7个 TC-B-XX 编号的边界测试用例，每个用例使用标准表格格式（用例编号|用例名称|边界类型|变化因素|基线场景|变化描述|输入数据|预期DRG变化|测试步骤|预期结果），"基线场景"应引用 TC-N-XX 编号，"输入数据"必须包含完整病历 JSON
- ## 5. 测试数据: 边界病历样本汇总、对比分析表

Format requirements:
- Meta information table at top: | 属性 | 内容 | with 文档类型="边界场景测试用例"
- Each test case must have a unique TC-B-XX number (TC-B-01, TC-B-02, ... at least TC-B-07)
- Cover all 4 boundary types: 合并症有无(≥2 cases), 年龄边界(≥2 cases), 多手术组合(≥1 case), 性别差异(≥1 case)
- Each "基线场景" field should reference a normal scenario like "TC-N-01" to show the comparison
- Every test case MUST include a complete medical record JSON
- Use accurate ICD-10 and ICD-9-CM-3 codes
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
- Invalid or mismatched ICD codes
- Missing required fields (no principal diagnosis, etc.)
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
- ## 2. 异常条件分析: 编码错误类型分析（无效编码如 "XXXX.X"、编码名称不匹配）、信息缺失类型分析（缺主要诊断、缺年龄/性别）、逻辑冲突类型分析（诊断与手术不匹配）、格式错误分析（JSON格式错误、字段类型错误如 age="abc"）
- ## 3. 测试场景设计: 异常场景矩阵表格（场景编号 | 异常类型 | 触发条件 | 输入示例 | 预期系统行为）
- ## 4. 测试用例: 至少7个 TC-A-XX 编号的异常测试用例，每个用例使用标准表格格式（用例编号|用例名称|异常类型|触发条件|输入数据|预期错误码|预期错误信息|预期系统行为|测试步骤|预期结果），"输入数据"必须包含含错误的病历 JSON
- ## 5. 测试数据: 异常病历样本汇总、错误处理验证表

Format requirements:
- Meta information table at top: | 属性 | 内容 | with 文档类型="异常场景测试用例"
- Each test case must have a unique TC-A-XX number (TC-A-01, TC-A-02, ... at least TC-A-07)
- Cover all 4 abnormal types: 编码错误(≥2 cases), 信息缺失(≥2 cases), 逻辑冲突(≥1 case), 格式错误(≥1 case)
- For 编码错误 cases, use clearly invalid ICD codes like "XXXX.9", "999.99", or codes that don't match their names
- For 信息缺失 cases, omit principal_diagnosis or patient.age fields
- For 逻辑冲突 cases, use diagnosis-surgery combos that make no medical sense (e.g., O80.0 顺产 + 81.54 膝关节置换)
- For 格式错误 cases, provide truncated/malformed JSON
- Every test case MUST include a complete medical record JSON (even if it contains errors)
- Document MUST end with: "*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*"
- NO "TODO", "TBD", "待定" or any placeholder text

Document title: # {project_name} 异常场景测试用例
"""
