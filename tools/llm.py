from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def call_llm(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return offline_response(prompt, metadata)

    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    request: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if model != "deepseek-reasoner":
        request["temperature"] = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    resp = client.chat.completions.create(**request)
    return resp.choices[0].message.content or ""


def offline_response(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    text = " ".join(prompt.strip().split())

    # ── 文档生成 supervisor 分类（必须放在 docgen 完整文档生成之前）──
    # supervisor 只应返回分类字符串，不能走 _offline_docgen_dispatch 返回完整文档
    if "document generation supervisor" in text.lower() or "classify the user's request into one of three document types" in text.lower():
        import re
        # 从 prompt 中提取 Pre-set doc_type 作为最可靠的分类依据
        hint_match = re.search(r'Pre-set doc_type:\s*(\S+)', prompt)
        if hint_match:
            hint = hint_match.group(1).strip().lower()
            if hint in ("requirements", "architecture", "testing"):
                return hint
        return "requirements"

    # ── 优先：文档生成 fallback（必须放在最前面，避免被 DRG 关键词误匹配）──
    if metadata and metadata.get("agent_system") == "docgen":
        return _offline_docgen_dispatch(prompt, metadata)
    # 兜底：通过 prompt 特征识别文档生成
    if _is_docgen_prompt(text):
        return _offline_docgen_dispatch(prompt, metadata)

    # ── 测试用例生成 fallback（必须在 DRG 推理 fallback 之前拦截）──
    if metadata and metadata.get("agent_system") == "tcgen":
        return _offline_tcgen_dispatch(prompt, metadata)
    if _is_tcgen_prompt(text):
        return _offline_tcgen_dispatch(prompt, metadata)

    # ── DRG 医疗推理 fallback ──
    if "Extract biomedical entities" in text:
        terms = [
            word.strip(".,:;()[]").lower()
            for word in text.split()
            if len(word.strip(".,:;()[]")) > 4
        ]
        return ", ".join(dict.fromkeys(terms[:6])) or "symptom, disease"
    if "Decide workflow" in text:
        return "deep-reasoning"
    if "structured medical understanding" in text:
        return (
            '{"possible_disease":"requires clinical confirmation",'
            '"symptoms":["extracted from query"],'
            '"risk_factors":["unknown"],'
            '"clinical_interpretation":"Preliminary AI-assisted case summary.",'
            '"severity_estimation":"undetermined"}'
        )
    if "Explain the biomedical reasoning" in text:
        return (
            "The system extracted query entities, retrieved the closest DRG graph context, "
            "ranked plausible medical reasoning paths, and generated a guarded treatment summary."
        )
    # DRG treatment — only match if NOT a docgen prompt
    if "treatment" in text.lower() and "DocGen" not in text:
        return (
            '{"options":["confirm diagnosis with licensed clinician",'
            '"symptom-directed management"],'
            '"drug_candidates":[],"confidence":"low",'
            '"warnings":["Educational output only; not medical advice."]}'
        )
    if "reasoning" in text.lower() and "DocGen" not in text:
        return "Query entities -> DRG concepts -> plausible mechanism -> clinical hypothesis."

    return "Preliminary medical reasoning generated from available query and graph context."


def _is_docgen_prompt(text: str) -> bool:
    """检测是否为文档生成类 prompt。"""
    docgen_markers = [
        "generating a requirements analysis document",
        "generating an architecture design document",
        "generating a test plan document",
        "docs/doc_spec.md",
        "DocGen Agent",
        "requirements analysis document",
        "architecture design document",
        "test plan document",
        "Document Generation Agent",
    ]
    return any(marker.lower() in text.lower() for marker in docgen_markers)


def _offline_docgen_dispatch(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    """根据 prompt 内容分发到正确的文档生成 fallback。

    优先使用 metadata 中的 doc_type（最可靠，由前端/调用方显式指定）；
    回退到 prompt 关键词匹配（兼容无 metadata 的调用路径）。
    """
    # 优先：使用 metadata 中显式指定的 doc_type
    if metadata and metadata.get("doc_type"):
        doc_type = metadata["doc_type"]
        if doc_type == "architecture":
            return _offline_architecture_doc(prompt)
        if doc_type == "testing":
            return _offline_testing_doc(prompt)
        if doc_type == "requirements":
            return _offline_requirements_doc(prompt)

    # 回退：prompt 关键词匹配
    text = prompt.lower()
    if "requirements" in text or "需求分析" in text:
        return _offline_requirements_doc(prompt)
    if "architecture" in text or "架构" in text:
        return _offline_architecture_doc(prompt)
    if "testing" in text or "test plan" in text or "测试" in text:
        return _offline_testing_doc(prompt)
    # 默认返回需求分析文档
    return _offline_requirements_doc(prompt)


def _is_tcgen_prompt(text: str) -> bool:
    """检测是否为测试用例生成类 prompt。"""
    markers = [
        "tcgen", "tc_spec.md",
        "tc_normal", "tc_boundary", "tc_abnormal",
        "normal scenario test case", "boundary scenario test case",
        "abnormal scenario test case",
        "test case generation supervisor",
        "tc_composer",
    ]
    text_lower = text.lower()
    return any(m.lower() in text_lower for m in markers)


def _offline_tcgen_dispatch(prompt: str, metadata: dict[str, Any] | None = None) -> str:
    """根据 tc_type 分发到正确的测试用例生成 fallback。"""
    if metadata and metadata.get("tc_type"):
        tc_type = metadata["tc_type"]
        if tc_type == "boundary":
            return _offline_tcgen_boundary(prompt)
        if tc_type == "abnormal":
            return _offline_tcgen_abnormal(prompt)
        return _offline_tcgen_normal(prompt)

    text_lower = prompt.lower()
    if "boundary" in text_lower:
        return _offline_tcgen_boundary(prompt)
    if "abnormal" in text_lower:
        return _offline_tcgen_abnormal(prompt)
    return _offline_tcgen_normal(prompt)


def _offline_tcgen_normal(prompt: str) -> str:
    """生成离线正常场景测试用例文档模板。"""
    import re
    from datetime import date
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    today = date.today().isoformat()

    # JSON template for medical records
    emr_json = (
        '{{"性别":"男","年龄":整数,"主要诊断":{{"疾病名称":"中文名称","疾病编码":"ICD-10编码"}},'
        '"次要诊断列表":[{{"疾病名称":"...","疾病编码":"ICD-10编码"}}],'
        '"主要手术":{{"手术名称":"中文名称","手术编码":"ICD-9-CM-3编码","手术级别":1-4}},'
        '"其他手术列表":[{{"手术名称":"...","手术编码":"ICD-9-CM-3编码","手术级别":1-4}}]}}'
    )

    # TC-N-01 JSON
    tcn01_json = (
        '{{"性别":"男","年龄":65,"主要诊断":{{"疾病名称":"急性透壁性心肌梗死","疾病编码":"I21.3"}},'
        '"次要诊断列表":[{{"疾病名称":"原发性高血压","疾病编码":"I10"}}],'
        '"主要手术":{{"手术名称":"冠状动脉支架植入术","手术编码":"36.06001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcn02_json = (
        '{{"性别":"女","年龄":48,"主要诊断":{{"疾病名称":"细菌性肺炎","疾病编码":"J15.9"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"手术名称":"胸腔穿刺术","手术编码":"34.9103","手术级别":1}},'
        '"其他手术列表":[]}}'
    )
    tcn03_json = (
        '{{"性别":"男","年龄":72,"主要诊断":{{"疾病名称":"胃窦恶性肿瘤","疾病编码":"C16.301"}},'
        '"次要诊断列表":[{{"疾病名称":"肠粘连","疾病编码":"K66.002"}}],'
        '"主要手术":{{"手术名称":"腹腔镜胃大部切除伴胃空肠吻合术","手术编码":"43.7x03","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcn04_json = (
        '{{"性别":"女","年龄":55,"主要诊断":{{"疾病名称":"胆管狭窄","疾病编码":"K83.105"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"手术名称":"胆总管切除术","手术编码":"51.6303","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcn05_json = (
        '{{"性别":"女","年龄":68,"主要诊断":{{"疾病名称":"膝关节骨性关节炎","疾病编码":"M17.9"}},'
        '"次要诊断列表":[{{"疾病名称":"慢性肾脏病","疾病编码":"N18.9"}}],'
        '"主要手术":{{"手术名称":"全膝关节置换术","手术编码":"81.54001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcn06_json = (
        '{{"性别":"男","年龄":58,"主要诊断":{{"疾病名称":"原发性高血压","疾病编码":"I10"}},'
        '"次要诊断列表":[{{"疾病名称":"2型糖尿病","疾病编码":"E11.9"}}],'
        '"主要手术":{{"手术名称":"常规检查","手术编码":"89.0","手术级别":1}},'
        '"其他手术列表":[]}}'
    )
    tcn07_json = (
        '{{"性别":"女","年龄":45,"主要诊断":{{"疾病名称":"胆囊结石伴急性胆囊炎","疾病编码":"K80.0"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"手术名称":"腹腔镜胆囊切除术","手术编码":"51.22001","手术级别":2}},'
        '"其他手术列表":[]}}'
    )
    tcn08_json = (
        '{{"性别":"男","年龄":78,"主要诊断":{{"疾病名称":"股骨颈骨折","疾病编码":"S72.0"}},'
        '"次要诊断列表":[{{"疾病名称":"腔隙性脑梗死","疾病编码":"I63.801"}}],'
        '"主要手术":{{"手术名称":"股骨骨折切开复位内固定术","手术编码":"79.35001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )

    body = _NORMAL_TC_TEMPLATE % {
        'project_name': project_name,
        'today': today,
        'emr_json': emr_json,
        'tcn01_json': tcn01_json,
        'tcn02_json': tcn02_json,
        'tcn03_json': tcn03_json,
        'tcn04_json': tcn04_json,
        'tcn05_json': tcn05_json,
        'tcn06_json': tcn06_json,
        'tcn07_json': tcn07_json,
        'tcn08_json': tcn08_json,
    }
    return body


def _offline_tcgen_boundary(prompt: str) -> str:
    """生成离线边界场景测试用例文档模板。"""
    import re
    from datetime import date
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    today = date.today().isoformat()

    tcb01_json = (
        '{{"性别":"女","年龄":55,"主要诊断":{{"疾病名称":"胆管狭窄","疾病编码":"K83.105"}},'
        '"次要诊断列表":[{{"疾病名称":"肠粘连","疾病编码":"K66.002"}}],'
        '"主要手术":{{"手术名称":"胆总管切除术","手术编码":"51.6303","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcb02_json = (
        '{{"性别":"女","年龄":55,"主要诊断":{{"疾病名称":"胆管狭窄","疾病编码":"K83.105"}},'
        '"次要诊断列表":[{{"疾病名称":"急性透壁性心肌梗死","疾病编码":"I21.3"}}],'
        '"主要手术":{{"手术名称":"胆总管切除术","手术编码":"51.6303","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcb03_json = (
        '{{"性别":"男","年龄":72,"主要诊断":{{"疾病名称":"胃窦恶性肿瘤","疾病编码":"C16.301"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"手术名称":"腹腔镜胃大部切除伴胃空肠吻合术","手术编码":"43.7x03","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcb04_json = (
        '{{"性别":"男","年龄":17,"主要诊断":{{"疾病名称":"急性透壁性心肌梗死","疾病编码":"I21.3"}},'
        '"次要诊断列表":[{{"疾病名称":"原发性高血压","疾病编码":"I10"}}],'
        '"主要手术":{{"手术名称":"冠状动脉支架植入术","手术编码":"36.06001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcb05_json = (
        '{{"性别":"男","年龄":79,"主要诊断":{{"疾病名称":"股骨颈骨折","疾病编码":"S72.0"}},'
        '"次要诊断列表":[{{"疾病名称":"腔隙性脑梗死","疾病编码":"I63.801"}}],'
        '"主要手术":{{"手术名称":"股骨骨折切开复位内固定术","手术编码":"79.35001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tcb06_json = (
        '{{"性别":"男","年龄":72,"主要诊断":{{"疾病名称":"胃窦恶性肿瘤","疾病编码":"C16.301"}},'
        '"次要诊断列表":[{{"疾病名称":"肠粘连","疾病编码":"K66.002"}}],'
        '"主要手术":{{"手术名称":"腹腔镜胃大部切除伴胃空肠吻合术","手术编码":"43.7x03","手术级别":3}},'
        '"其他手术列表":[{{"手术名称":"超声引导下胸腔穿刺术","手术编码":"34.9103","手术级别":1}},'
        '{{"手术名称":"肠粘连松解术","手术编码":"54.5903","手术级别":2}}]}}'
    )
    tcb07_json = (
        '{{"性别":"男","年龄":65,"主要诊断":{{"疾病名称":"膝关节骨性关节炎","疾病编码":"M17.9"}},'
        '"次要诊断列表":[{{"疾病名称":"慢性肾脏病","疾病编码":"N18.9"}}],'
        '"主要手术":{{"手术名称":"全膝关节置换术","手术编码":"81.54001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )

    body = _BOUNDARY_TC_TEMPLATE % {
        'project_name': project_name,
        'today': today,
        'tcb01_json': tcb01_json,
        'tcb02_json': tcb02_json,
        'tcb03_json': tcb03_json,
        'tcb04_json': tcb04_json,
        'tcb05_json': tcb05_json,
        'tcb06_json': tcb06_json,
        'tcb07_json': tcb07_json,
    }
    return body


def _offline_tcgen_abnormal(prompt: str) -> str:
    """生成离线异常场景测试用例文档模板。"""
    import re
    from datetime import date
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    today = date.today().isoformat()

    tca01_json = (
        '{{"性别":"男","年龄":60,"主要诊断":{{"疾病名称":"未知疾病","疾病编码":"XXXX.9"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"手术名称":"常规手术","手术编码":"99.99","手术级别":1}},'
        '"其他手术列表":[]}}'
    )
    tca02_json = (
        '{{"性别":"男","年龄":55,"主要诊断":{{"疾病名称":"胆管狭窄","疾病编码":"K83.105"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"疾病名称":"未知手术","手术编码":"999.99","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tca03_json = (
        '{{"性别":"男","年龄":60,"次要诊断列表":[{{"疾病名称":"高血压","疾病编码":"I10"}}],'
        '"主要手术":{{"疾病名称":"支架植入","手术编码":"36.06001","手术级别":3}}}}'
    )
    tca04_json = (
        '{{"性别":"女","主要诊断":{{"疾病名称":"胆囊结石","疾病编码":"K80.0"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"疾病名称":"腹腔镜胆囊切除术","手术编码":"51.22001","手术级别":2}},'
        '"其他手术列表":[]}}'
    )
    tca05_json = (
        '{{"性别":"女","年龄":28,"主要诊断":{{"疾病名称":"头位顺产","疾病编码":"O80.0"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"疾病名称":"全膝关节置换术","手术编码":"81.54001","手术级别":3}},'
        '"其他手术列表":[]}}'
    )
    tca06_json = (
        '{{"性别":"男","年龄":60,"主要诊断":{{"疾病名称":"心肌梗死","疾病编码":"I21.3"}}}'
    )
    tca07_json = (
        '{{"性别":"男","年龄":"六十八","主要诊断":{{"疾病名称":"胆管狭窄","疾病编码":"K83.105"}},'
        '"次要诊断列表":[],'
        '"主要手术":{{"疾病名称":"胆总管切除术","手术编码":"51.6303","手术级别":3}},'
        '"其他手术列表":[]}}'
    )

    body = _ABNORMAL_TC_TEMPLATE % {
        'project_name': project_name,
        'today': today,
        'tca01_json': tca01_json,
        'tca02_json': tca02_json,
        'tca03_json': tca03_json,
        'tca04_json': tca04_json,
        'tca05_json': tca05_json,
        'tca06_json': tca06_json,
        'tca07_json': tca07_json,
    }
    return body


_NORMAL_TC_TEMPLATE = """| 属性 | 内容 |
|------|------|
| **项目名称** | %(project_name)s |
| **文档类型** | 正常场景测试用例 |
| **文档版本** | V1.0 |
| **生成日期** | %(today)s |
| **生成方式** | AI 自动生成（TCGen Agent） |
| **状态** | 草稿 |
| **DRG 版本** | CN-DRG 2018（基于项目内置 MDC/ADRG/CC 查表） |

# %(project_name)s 正常场景测试用例

## 1. 测试概述

### 1.1 测试目标

验证 MedReasonerAgent 的 DRG 入组推理模块对常见诊断 + 手术组合的正确处理能力。测试系统能否根据 ICD-10 诊断编码正确匹配 MDC，根据 ICD-9-CM-3 手术编码匹配外科 ADRG，并根据 CC/MCC 次要诊断正确判定并发症等级，最终输出符合 CN-DRG 2018 规范的 DRG 编码。

### 1.2 测试范围

- 覆盖 MDC：MDCF（循环系统）、MDCE（呼吸系统）、MDCG（消化道）、MDCH（肝胆胰）、MDCI（骨骼肌肉）
- 覆盖手术类型：心血管手术，消化系统手术，肝胆胰手术，骨科手术，呼吸系统手术
- 覆盖 DRG 类型：内科 ADRG（FR3、GR1 等）、外科 ADRG（GB2、HC1、IC3、FM2 等）
- 覆盖并发症等级：无合并症（NONE 后缀5）、一般合并症（CC 后缀9）

### 1.3 参考资料

- CN-DRG 2018 分组规则（kg/drg_loader.py）
- 测试用例格式规范（docs/tc_spec.md）

## 2. DRG 分组规则摘要

### 2.1 知识图谱关系

| 源节点 | 关系 | 目标节点 | 说明 |
|--------|------|----------|------|
| symptom | suggests | disease | 症状提示可能疾病 |
| disease | mapped_to | drg_group | 疾病映射到 DRG 分组 |
| disease | treated_by | treatment | 疾病对应治疗方式 |
| risk_factor | increases_risk_of | disease | 风险因素增加疾病概率 |
| test | confirms_or_rules_out | disease | 检查项目确定或排除疾病 |

### 2.2 入组判定逻辑

1. **Step 1 — 确定 MDC**：取主要诊断 ICD-10 编码的前缀，在 MDC_TABLE 中按前缀长度降序匹配，取最长匹配。
2. **Step 2 — 确定 ADRG**：在匹配到的 MDC 下，将手术 ICD-9-CM-3 编码前缀与 ADRG_TABLE 逐级比对（5→4→3→2位）。命中外科条目则为外科 ADRG；无匹配则回退到该 MDC 的内科 ADRG。
3. **Step 3 — 判定 CC/MCC**：遍历所有次要诊断编码，先在 MCC_SET 精确查找，再在 CC_SET 精确查找。MCC 优先于 CC。
4. **Step 4 — 组装最终 DRG**：ADRG 编码 + 并发症后缀（NONE→5, CC→9, MCC→1）→ 最终 DRG。

## 3. 测试场景设计

### 3.1 场景分类

本测试套件覆盖以下场景类型：

- **内科场景**：有主要诊断，无主要手术或手术不匹配，回退到内科 ADRG
- **外科场景**：主要诊断 + 主要手术均匹配到外科 ADRG
- **CC 场景**：主要诊断 + 手术 + 次要诊断含 CC 编码
- **MCC 场景**：主要诊断 + 手术 + 次要诊断含 MCC 编码
- **复合手术场景**：主要诊断 + 主要手术 + 其他手术列表

### 3.2 场景覆盖矩阵

| 场景编号 | 诊断 | 手术 | MDC | ADRG | 并发症 | 最终DRG | 覆盖说明 |
|----------|------|------|------|------|--------|---------|----------|
| TC-N-01 | I21.3 急性透壁性心肌梗死 | 36.06001 冠脉支架植入 | MDCF | FM2 | CC（I10） | FM29 | 心血管+CC |
| TC-N-02 | J15.9 细菌性肺炎 | 无（回退内科） | MDCE | ER3 | NONE | ER35 | 呼吸系统内科 |
| TC-N-03 | C16.301 胃窦恶性肿瘤 | 43.7x03 腹腔镜胃大部切除 | MDCG | GB2 | CC（K66.002） | GB29 | 消化道外科+CC |
| TC-N-04 | K83.105 胆管狭窄 | 51.6303 胆总管切除术 | MDCH | HC1 | NONE | HC15 | 肝胆胰外科+无CC |
| TC-N-05 | M17.9 膝关节骨性关节炎 | 81.54001 全膝关节置换 | MDCI | IC3 | CC（N18.9 CKD） | IC39 | 骨科外科+CC |
| TC-N-06 | I10 原发性高血压 | 无（回退内科） | MDCF | FR3 | CC（E11.9 糖尿病） | FR39 | 心血管内科+CC |
| TC-N-07 | K80.0 胆囊结石伴急性胆囊炎 | 51.22001 腹腔镜胆囊切除 | MDCH | HC2 | NONE | HC25 | 肝胆胰外科+无CC |
| TC-N-08 | S72.0 股骨颈骨折 | 79.35001 股骨骨折切开复位 | MDCI | ID1 | CC（I63.801 腔隙性脑梗死） | ID19 | 骨折外科+CC |

## 4. 测试用例

### TC-N-01：心血管支架植入伴高血压

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-01 |
| **用例名称** | 心血管支架植入伴高血压 |
| **测试场景** | 急性心肌梗死患者行冠脉支架植入术，伴原发性高血压（CC） |
| **前置条件** | 系统已加载 kg/drg_loader.py 中的 MDCF/ADRG/CC 查表 |
| **输入数据** | ```json\n%(tcn01_json)s\n``` |
| **预期 DRG 分组** | MDCF → FM2（经皮心血管介入治疗）→ CC → FM29 |
| **预期置信度** | 高 |
| **测试步骤** | 1. 提交 EMR JSON，系统调用 entity._parse_emr() 解析<br>2. get_mdc("I21.3") → MDCF<br>3. get_adrg(MDCF, ["36.06001"]) → FM2<br>4. check_complications(["I10"]) → CC<br>5. resolve_drg("FM2", "CC") → FM29 |
| **预期结果** | drg_result: {"mdc":"MDCF","adrg":"FM2","drg":"FM29","complication":"CC"} |

### TC-N-02：细菌性肺炎内科治疗

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-02 |
| **用例名称** | 细菌性肺炎内科治疗 |
| **测试场景** | 细菌性肺炎患者，无匹配手术，回退到呼吸系统内科 ADRG |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn02_json)s\n``` |
| **预期 DRG 分组** | MDCE → ER3（呼吸系统内科疾病）→ NONE → ER35 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("J15.9") → MDCE<br>2. 手术 34.9103 不在 ADRG_TABLE 中，回退到 MEDICAL_ADRG → ER3<br>3. check_complications([]) → NONE<br>4. resolve_drg("ER3", "NONE") → ER35 |
| **预期结果** | drg_result: {"mdc":"MDCE","adrg":"ER3","drg":"ER35","complication":"NONE"} |

### TC-N-03：胃癌手术伴肠粘连

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-03 |
| **用例名称** | 胃癌手术伴肠粘连 |
| **测试场景** | 胃窦恶性肿瘤行腹腔镜胃大部切除术，伴肠粘连（CC） |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn03_json)s\n``` |
| **预期 DRG 分组** | MDCG → GB2 → CC（K66.002）→ GB29 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("C16.301") → MDCG（C16 前缀优先于 K）<br>2. get_adrg(MDCG, ["43.7x03"]) → GB2<br>3. check_complications(["K66.002"]) → CC<br>4. resolve_drg("GB2", "CC") → GB29 |
| **预期结果** | drg_result: {"mdc":"MDCG","adrg":"GB2","drg":"GB29","complication":"CC"} |

### TC-N-04：胆管狭窄手术无合并症

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-04 |
| **用例名称** | 胆管狭窄手术无合并症 |
| **测试场景** | 胆管狭窄患者行胆总管切除术，无次要诊断 |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn04_json)s\n``` |
| **预期 DRG 分组** | MDCH → HC1 → NONE → HC15 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("K83.105") → MDCH（K83 前缀优先于 K）<br>2. get_adrg(MDCH, ["51.6303"]) → HC1<br>3. check_complications([]) → NONE<br>4. resolve_drg("HC1", "NONE") → HC15 |
| **预期结果** | drg_result: {"mdc":"MDCH","adrg":"HC1","drg":"HC15","complication":"NONE"} |

### TC-N-05：膝关节置换伴慢性肾脏病

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-05 |
| **用例名称** | 膝关节置换伴慢性肾脏病 |
| **测试场景** | 膝关节骨性关节炎行全膝关节置换术，伴慢性肾脏病（CC） |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn05_json)s\n``` |
| **预期 DRG 分组** | MDCI → IC3 → CC（N18.9）→ IC39 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("M17.9") → MDCI<br>2. get_adrg(MDCI, ["81.54001"]) → IC3<br>3. check_complications(["N18.9"]) → CC<br>4. resolve_drg("IC3", "CC") → IC39 |
| **预期结果** | drg_result: {"mdc":"MDCI","adrg":"IC3","drg":"IC39","complication":"CC"} |

### TC-N-06：高血压伴糖尿病（内科）

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-06 |
| **用例名称** | 高血压伴糖尿病（内科） |
| **测试场景** | 原发性高血压伴 2 型糖尿病患者，内科治疗，无手术匹配 |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn06_json)s\n``` |
| **预期 DRG 分组** | MDCF → FR3（心血管内科）→ CC → FR39 |
| **预期置信度** | 中 |
| **测试步骤** | 1. get_mdc("I10") → MDCF<br>2. 手术 89.0 不在 ADRG_TABLE，回退 MEDICAL_ADRG → FR3<br>3. check_complications(["E11.9"]) → CC<br>4. resolve_drg("FR3", "CC") → FR39 |
| **预期结果** | drg_result: {"mdc":"MDCF","adrg":"FR3","drg":"FR39","complication":"CC"} |

### TC-N-07：急性胆囊炎腹腔镜切除

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-07 |
| **用例名称** | 急性胆囊炎腹腔镜切除 |
| **测试场景** | 胆囊结石伴急性胆囊炎，行腹腔镜胆囊切除术，无次要诊断 |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn07_json)s\n``` |
| **预期 DRG 分组** | MDCH → HC2 → NONE → HC25 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("K80.0") → MDCH<br>2. get_adrg(MDCH, ["51.22001"]) → HC2（MDCH|51.2 匹配）<br>3. check_complications([]) → NONE<br>4. resolve_drg("HC2", "NONE") → HC25 |
| **预期结果** | drg_result: {"mdc":"MDCH","adrg":"HC2","drg":"HC25","complication":"NONE"} |

### TC-N-08：股骨骨折手术伴脑梗死

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-N-08 |
| **用例名称** | 股骨骨折手术伴脑梗死 |
| **测试场景** | 股骨颈骨折患者行切开复位内固定术，伴腔隙性脑梗死（CC） |
| **前置条件** | 系统已加载 kg/drg_loader.py |
| **输入数据** | ```json\n%(tcn08_json)s\n``` |
| **预期 DRG 分组** | MDCI → ID1 → CC（I63.801）→ ID19 |
| **预期置信度** | 高 |
| **测试步骤** | 1. get_mdc("S72.0") → MDCI<br>2. get_adrg(MDCI, ["79.35001"]) → ID1<br>3. check_complications(["I63.801"]) → CC<br>4. resolve_drg("ID1", "CC") → ID19 |
| **预期结果** | drg_result: {"mdc":"MDCI","adrg":"ID1","drg":"ID19","complication":"CC"} |

## 5. 测试数据

### 5.1 病历样本汇总

| 用例编号 | 患者特征 | 主要诊断 | 手术 | 次要诊断 | 预期 DRG |
|----------|----------|----------|------|----------|----------|
| TC-N-01 | 男 65岁 | I21.3 急性心梗 | 36.06001 支架 | I10 高血压 | FM29 |
| TC-N-02 | 女 48岁 | J15.9 肺炎 | 无（回退内科） | 无 | ER35 |
| TC-N-03 | 男 72岁 | C16.301 胃癌 | 43.7x03 胃切除 | K66.002 肠粘连 | GB29 |
| TC-N-04 | 女 55岁 | K83.105 胆管狭窄 | 51.6303 胆总管切除 | 无 | HC15 |
| TC-N-05 | 女 68岁 | M17.9 膝关节炎 | 81.54001 膝置换 | N18.9 CKD | IC39 |
| TC-N-06 | 男 58岁 | I10 高血压 | 无（回退内科） | E11.9 糖尿病 | FR39 |
| TC-N-07 | 女 45岁 | K80.0 胆囊炎 | 51.22001 腹腔镜胆囊切除 | 无 | HC25 |
| TC-N-08 | 男 78岁 | S72.0 股骨骨折 | 79.35001 骨折复位 | I63.801 脑梗死 | ID19 |

### 5.2 预期 DRG 分组映射表

| 预期 DRG | ADRG | 并发症后缀 | 说明 |
|----------|------|------------|------|
| FM29 | FM2（经皮心血管介入） | 9（CC） | 心血管外科 + CC |
| ER35 | ER3（呼吸内科） | 5（NONE） | 呼吸内科 + 无CC |
| GB29 | GB2（胃、十二指肠大手术） | 9（CC） | 消化道外科 + CC |
| HC15 | HC1（胆总管手术） | 5（NONE） | 肝胆外科 + 无CC |
| IC39 | IC3（髋/膝关节置换） | 9（CC） | 骨科外科 + CC |
| FR39 | FR3（心血管内科） | 9（CC） | 心血管内科 + CC |
| HC25 | HC2（胆囊切除术） | 5（NONE） | 肝胆外科 + 无CC |
| ID19 | ID1（骨折切开复位） | 9（CC） | 骨折外科 + CC |

---

*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


_BOUNDARY_TC_TEMPLATE = """| 属性 | 内容 |
|------|------|
| **项目名称** | %(project_name)s |
| **文档类型** | 边界场景测试用例 |
| **文档版本** | V1.0 |
| **生成日期** | %(today)s |
| **生成方式** | AI 自动生成（TCGen Agent） |
| **状态** | 草稿 |
| **DRG 版本** | CN-DRG 2018（基于项目内置 MDC/ADRG/CC 查表） |

# %(project_name)s 边界场景测试用例

## 1. 测试概述

### 1.1 测试目标

验证 MedReasonerAgent DRG 入组推理模块在关键变量处于边界条件时的行为。边界条件包括：合并症/并发症的有无（CC/MCC 临界状态）、年龄边界值、多手术组合优先级、性别特异性分组。

### 1.2 边界定义

| 边界类型 | 边界条件 | 预期影响 |
|----------|----------|----------|
| 合并症有无 | 添加/移除 CC 编码 → DRG 后缀 5↔9；添加 MCC 编码 → 后缀 9↔1 | DRG 编码发生变化 |
| 年龄边界 | 17岁 vs 18岁（成年阈值）、新生儿 vs 成人 | 部分 ADRG 按年龄分层 |
| 多手术组合 | 主要手术 vs 其他手术列表的优先级 | 主要手术决定 ADRG |
| 性别差异 | MDCM（男性生殖）、MDCN（女性生殖）| 同诊断不同性别可能入不同 MDC |

## 2. 边界条件分析

### 2.1 合并症影响分析

CN-DRG 2018 中，次要诊断决定最终 DRG 的后缀数字：
- **无合并症（NONE）** → 后缀 5（入组如 GB25、HC15）
- **一般合并症（CC）** → 后缀 9（入组如 GB29、HC19）
- **严重合并症（MCC）** → 后缀 1（入组如 GB21、HC11）

边界条件：当次要诊断列表从空变为含 CC 编码，或从含 CC 变为含 MCC 编码时，后缀数字发生变化，对应 DRG 分组改变，进而影响医保支付权重。

### 2.2 年龄边界分析

部分 MDC/ADRG 按患者年龄分层：
- 新生儿（年龄 < 1 岁）：进入 MDCP（新生儿及其他围产期疾病）
- 成人阈值（18 岁）：部分 DRG 按成年/未成年区分
- 老年阈值（60/65 岁）：部分 ADRG 可能涉及年龄加权

当前系统 kg/drg_loader.py 暂未实现年龄分层规则（预留字段），边界测试验证系统能否正确传递年龄信息。

### 2.3 多手术组合影响

当患者其他手术列表包含多个手术时，系统应优先根据主要手术编码匹配 ADRG。当前实现中 get_adrg() 按手术列表顺序（主要手术优先）匹配，取第一个命中结果。

## 3. 测试场景设计

### 3.1 边界场景矩阵

| 场景编号 | 边界类型 | 变化因素 | 基线正常场景 | 预期影响 |
|----------|----------|----------|--------------|----------|
| TC-B-01 | 合并症有无 | 添加 CC（K66.002 肠粘连） | TC-N-04（HC15）→ HC19 | DRG 后缀 5→9 |
| TC-B-02 | 合并症有无 | 添加 MCC（I21.3 急性心梗） | TC-N-04（HC15）→ HC11 | DRG 后缀 5→1 |
| TC-B-03 | 合并症有无 | 移除 CC（TC-N-03 的 K66.002） | TC-N-03（GB29）→ GB25 | DRG 后缀 9→5 |
| TC-B-04 | 年龄边界 | 17岁 vs 18岁 | TC-N-01 65岁 → TC-B-04 17岁 | 验证年龄传递 |
| TC-B-05 | 年龄边界 | 78岁 vs 79岁高龄 | TC-N-08 78岁 → TC-B-05 79岁 | 验证年龄传递 |
| TC-B-06 | 多手术组合 | 其他手术列表含多个手术 | TC-N-03（仅主要手术）→ 增加其他手术 | 主要手术决定 ADRG |
| TC-B-07 | 性别差异 | 男性患者（TC-N-05 变体） | TC-N-05 女性 → TC-B-07 男性 | 验证性别传递 |

## 4. 测试用例

### TC-B-01：胆管手术添加 CC（5→9 边界）

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-01 |
| **用例名称** | 胆管手术添加 CC（5→9 边界） |
| **边界类型** | 合并症有无 |
| **变化因素** | 次要诊断列表从空变为含 K66.002 肠粘连（CC） |
| **基线场景** | TC-N-04（HC15：无合并症） |
| **变化描述** | 在 TC-N-04 基础上添加肠粘连（CC）作为次要诊断 |
| **输入数据** | ```json\n%(tcb01_json)s\n``` |
| **预期 DRG 变化** | HC15（无CC）→ HC19（CC），后缀 5→9 |
| **测试步骤** | 1. get_mdc("K83.105") → MDCH<br>2. get_adrg(MDCH, ["51.6303"]) → HC1<br>3. check_complications(["K66.002"]) → CC<br>4. resolve_drg("HC1", "CC") → HC19 |
| **预期结果** | drg_result: {"mdc":"MDCH","adrg":"HC1","drg":"HC19","complication":"CC"} |

### TC-B-02：胆管手术添加 MCC（5→1 边界）

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-02 |
| **用例名称** | 胆管手术添加 MCC（5→1 边界） |
| **边界类型** | 合并症有无 |
| **变化因素** | 次要诊断从无变为含 I21.3 急性心梗（MCC） |
| **基线场景** | TC-N-04（HC15：无合并症） |
| **变化描述** | 在 TC-N-04 基础上添加急性心肌梗死（MCC）作为次要诊断 |
| **输入数据** | ```json\n%(tcb02_json)s\n``` |
| **预期 DRG 变化** | HC15（无CC）→ HC11（MCC），后缀 5→1 |
| **测试步骤** | 1. get_mdc("K83.105") → MDCH<br>2. get_adrg(MDCH, ["51.6303"]) → HC1<br>3. check_complications(["I21.3"]) → MCC（I21.3 在 MCC_SET）<br>4. resolve_drg("HC1", "MCC") → HC11 |
| **预期结果** | drg_result: {"mdc":"MDCH","adrg":"HC1","drg":"HC11","complication":"MCC"} |

### TC-B-03：胃癌手术移除 CC（9→5 边界）

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-03 |
| **用例名称** | 胃癌手术移除 CC（9→5 边界） |
| **边界类型** | 合并症有无 |
| **变化因素** | TC-N-03 的次要诊断列表中移除 K66.002 |
| **基线场景** | TC-N-03（GB29：有 CC） |
| **变化描述** | TC-N-03 的次要诊断列表清空，验证无合并症场景 |
| **输入数据** | ```json\n%(tcb03_json)s\n``` |
| **预期 DRG 变化** | GB29（CC）→ GB25（无CC），后缀 9→5 |
| **测试步骤** | 1. get_mdc("C16.301") → MDCG<br>2. get_adrg(MDCG, ["43.7x03"]) → GB2<br>3. check_complications([]) → NONE<br>4. resolve_drg("GB2", "NONE") → GB25 |
| **预期结果** | drg_result: {"mdc":"MDCG","adrg":"GB2","drg":"GB25","complication":"NONE"} |

### TC-B-04：年龄边界 17岁 vs 18岁

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-04 |
| **用例名称** | 年龄边界 17岁 vs 18岁 |
| **边界类型** | 年龄边界 |
| **变化因素** | 将 TC-N-01 的患者年龄从 65岁改为 17岁 |
| **基线场景** | TC-N-01（65岁男性） |
| **变化描述** | 验证系统能否正确传递和处理年龄字段（当前系统暂未按年龄分层 ADRG） |
| **输入数据** | ```json\n%(tcb04_json)s\n``` |
| **预期 DRG 变化** | 年龄字段正确传递，MDC/ADRG/DRG 与 TC-N-01 一致（系统当前无年龄分层规则） |
| **测试步骤** | 1. entity._parse_emr() 正确解析年龄字段<br>2. 验证 state["emr_data"]["age"] == 17<br>3. DRG 分组逻辑与 TC-N-01 一致 |
| **预期结果** | emr_data 中 age 字段正确记录为 17，drg_result 同 TC-N-01 |

### TC-B-05：年龄边界 78岁 vs 79岁高龄

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-05 |
| **用例名称** | 年龄边界 78岁 vs 79岁高龄 |
| **边界类型** | 年龄边界 |
| **变化因素** | 将 TC-N-08 的患者年龄从 78岁改为 79岁 |
| **基线场景** | TC-N-08（78岁男性） |
| **变化描述** | 验证高龄患者年龄字段处理正确性 |
| **输入数据** | ```json\n%(tcb05_json)s\n``` |
| **预期 DRG 变化** | 年龄字段正确传递，MDC/ADRG/DRG 与 TC-N-08 一致 |
| **测试步骤** | 1. entity._parse_emr() 正确解析年龄字段<br>2. 验证 state["emr_data"]["age"] == 79<br>3. DRG 分组结果同 TC-N-08 |
| **预期结果** | emr_data 中 age 字段正确记录为 79，drg_result 同 TC-N-08 |

### TC-B-06：多手术组合优先级

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-06 |
| **用例名称** | 多手术组合优先级 |
| **边界类型** | 多手术组合 |
| **变化因素** | 在 TC-N-03 基础上，其他手术列表增加胸腔穿刺和肠粘连松解 |
| **基线场景** | TC-N-03（仅主要手术） |
| **变化描述** | 增加其他手术列表，验证主要手术决定 ADRG 的优先级规则 |
| **输入数据** | ```json\n%(tcb06_json)s\n``` |
| **预期 DRG 变化** | 主要手术 43.7x03 仍决定 ADRG=GB2，与 TC-N-03 一致（不受其他手术影响） |
| **测试步骤** | 1. get_adrg() 按主要手术 43.7x03 匹配 → GB2<br>2. 其他手术 34.9103 和 54.5903 不影响 ADRG 判定<br>3. check_complications(["K66.002"]) → CC → GB29 |
| **预期结果** | drg_result: {"mdc":"MDCG","adrg":"GB2","drg":"GB29","complication":"CC"}，与 TC-N-03 一致 |

### TC-B-07：性别差异验证

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-B-07 |
| **用例名称** | 性别差异验证 |
| **边界类型** | 性别差异 |
| **变化因素** | 将 TC-N-05 的患者性别从女改为男，年龄从 68岁改为 65岁 |
| **基线场景** | TC-N-05（65岁女性） |
| **变化描述** | 验证系统正确传递和处理性别字段 |
| **输入数据** | ```json\n%(tcb07_json)s\n``` |
| **预期 DRG 变化** | 性别字段正确传递，M17.9 → MDCI（骨骼肌肉），与 TC-N-05 DRG 分组一致 |
| **测试步骤** | 1. entity._parse_emr() 正确解析性别字段<br>2. 验证 state["emr_data"]["gender"] == "男"<br>3. DRG 分组结果同 TC-N-05 |
| **预期结果** | emr_data 中 gender 字段正确记录为"男"，drg_result 同 TC-N-05 |

## 5. 测试数据

### 5.1 边界病历样本

| 用例编号 | 基线 | 变化因素 | 变化后次要诊断 | 预期 DRG 变化 |
|----------|------|----------|----------------|--------------|
| TC-B-01 | TC-N-04（HC15） | 添加 K66.002 | K66.002 | HC15→HC19 |
| TC-B-02 | TC-N-04（HC15） | 添加 I21.3 | I21.3 | HC15→HC11 |
| TC-B-03 | TC-N-03（GB29） | 移除 K66.002 | 空 | GB29→GB25 |
| TC-B-04 | TC-N-01 | 年龄 65→17 | 同 TC-N-01 | 年龄字段=17 |
| TC-B-05 | TC-N-08 | 年龄 78→79 | 同 TC-N-08 | 年龄字段=79 |
| TC-B-06 | TC-N-03 | 增加其他手术 | 同 TC-N-03 + 额外手术 | 与 TC-N-03 一致 |
| TC-B-07 | TC-N-05 | 性别 女→男 | 同 TC-N-05 | 性别字段="男" |

### 5.2 对比分析表

| 对比项 | TC-B-01 vs TC-N-04 | TC-B-02 vs TC-N-04 | TC-B-03 vs TC-N-03 | TC-B-06 vs TC-N-03 |
|--------|---------------------|---------------------|---------------------|---------------------|
| 变化变量 | 次要诊断 +1 | 次要诊断 +1（换 MCC） | 次要诊断 -1 | 其他手术列表 +2 |
| MDC 变化 | 无 | 无 | 无 | 无 |
| ADRG 变化 | 无 | 无 | 无 | 无 |
| DRG 变化 | HC15→HC19 | HC15→HC11 | GB29→GB25 | 无 |
| 后缀变化 | 5→9 | 5→1 | 9→5 | 无 |

---

*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


_ABNORMAL_TC_TEMPLATE = """| 属性 | 内容 |
|------|------|
| **项目名称** | %(project_name)s |
| **文档类型** | 异常场景测试用例 |
| **文档版本** | V1.0 |
| **生成日期** | %(today)s |
| **生成方式** | AI 自动生成（TCGen Agent） |
| **状态** | 草稿 |
| **DRG 版本** | CN-DRG 2018（基于项目内置 MDC/ADRG/CC 查表） |

# %(project_name)s 异常场景测试用例

## 1. 测试概述

### 1.1 测试目标

验证 MedReasonerAgent 的 DRG 入组推理模块在接收无效、不完整或矛盾输入时的降级处理能力。异常场景测试确保系统在遇到各类输入错误时能够给出合理的错误提示或降级响应，而不是崩溃或返回无意义结果。

### 1.2 异常分类

| 异常类型 | 触发条件 | 预期系统行为 |
|----------|----------|--------------|
| 编码错误 | ICD 编码不在 MDC_TABLE/ADRG_TABLE/CC/MCC 集合中 | get_mdc() 返回 None，降级到 NLP 模式或返回 N/A |
| 信息缺失 | 缺少主要诊断、年龄或性别等必填字段 | entity._parse_emr() 返回 None，降级到 NLP 模式 |
| 逻辑冲突 | 诊断与手术逻辑不匹配（如产科诊断 + 骨科手术） | 可能回退到内科 ADRG 或返回冲突警告 |
| 格式错误 | JSON 格式错误、字段类型错误 | json.loads() 抛出异常，降级到 NLP 模式 |

## 2. 异常条件分析

### 2.1 编码错误类型

无效 ICD 编码是指不在系统内置查表中的编码：
- **ICD-10 无效诊断编码**：前缀不匹配 MDC_TABLE 中的任何条目（如 "XXXX.9"、"999.99"）
- **ICD-9-CM-3 无效手术编码**：前缀不匹配 ADRG_TABLE 中的任何条目，且不在 MEDICAL_ADRG 兜底范围

当 get_mdc() 返回 None 时，entity agent 应降级到 NLP 模式，从自然语言 query 中抽取实体。

### 2.2 信息缺失类型

系统要求以下字段必须存在：
- 主要诊断.疾病编码：必填，用于 MDC 判定
- 年龄：系统虽不直接用于 DRG 分组，但需记录到 emr_data
- 性别：系统虽不直接用于 DRG 分组，但需记录到 emr_data

当 entity._parse_emr() 返回 None 时，entity agent 降级到 NLP 模式，尝试从原始 query 中通过 LLM 抽取实体。

### 2.3 逻辑冲突类型

逻辑冲突指输入在格式上合法，但在医学逻辑上存在不匹配：
- 产科诊断（MDCO）患者接受骨科手术（MDCI）
- 消化系统诊断（MDCG）患者接受心血管手术（MDCF）
- 男性患者的主要诊断为女性生殖系统疾病（MDCN）

当前系统 get_adrg() 按主要手术匹配 ADRG，可能会命中内科兜底或返回外科 ADRG 但与 MDC 不一致。

## 3. 测试场景设计

### 3.1 异常场景矩阵

| 场景编号 | 异常类型 | 触发条件 | 输入示例 | 预期系统行为 |
|----------|----------|----------|----------|--------------|
| TC-A-01 | 编码错误 | 无效 ICD-10 诊断编码 "XXXX.9" | JSON 含 "疾病编码": "XXXX.9" | get_mdc() 返回 None，NLP 降级 |
| TC-A-02 | 编码错误 | 无效 ICD-9-CM-3 手术编码 "999.99" | JSON 含 "手术编码": "999.99" | 回退到内科 ADRG |
| TC-A-03 | 信息缺失 | 缺少"主要诊断"字段 | JSON 不含"主要诊断"键 | entity._parse_emr() 返回 None，NLP 降级 |
| TC-A-04 | 信息缺失 | 缺少"年龄"字段 | JSON 含主要诊断但无年龄 | emr_data 中 age=0 或缺失，NLP 降级 |
| TC-A-05 | 逻辑冲突 | 产科诊断（O80.0）+ 骨科手术（81.54001） | MDCO 诊断 + MDCI 手术 | get_adrg 可能返回不一致结果 |
| TC-A-06 | 格式错误 | JSON 截断（缺少闭合括号） | 不完整 JSON 字符串 | json.loads() 抛出异常，NLP 降级 |
| TC-A-07 | 格式错误 | 字段类型错误（年龄="六十八"） | JSON 中年龄为字符串 | json.loads() 可能解析为 str，entity 处理异常 |

## 4. 测试用例

### TC-A-01：无效 ICD-10 诊断编码

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-01 |
| **用例名称** | 无效 ICD-10 诊断编码 |
| **异常类型** | 编码错误 |
| **触发条件** | 主要诊断的疾病编码为 "XXXX.9"，不在 MDC_TABLE 中 |
| **输入数据** | ```json\n%(tca01_json)s\n``` |
| **预期错误码** | DRG-N/A |
| **预期错误信息** | 主要诊断 ICD-10 编码不在系统支持范围内 |
| **预期系统行为** | get_mdc("XXXX.9") → None，降级到 NLP 模式或返回 confidence=0 |
| **测试步骤** | 1. entity._parse_emr() 解析 JSON → 提取到 icd_codes=["XXXX.9"]<br>2. retrieval agent 调用 get_mdc("XXXX.9") → None<br>3. 系统降级到 NLP 模式，从 query 自然语言抽取实体 |
| **预期结果** | drg_result: {"mdc":"N/A","adrg":"N/A","drg":"N/A","complication":"N/A","confidence":0.0} |

### TC-A-02：无效 ICD-9-CM-3 手术编码

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-02 |
| **用例名称** | 无效 ICD-9-CM-3 手术编码 |
| **异常类型** | 编码错误 |
| **触发条件** | 主要手术编码为 "999.99"，不在 ADRG_TABLE 中，且无内科兜底 |
| **输入数据** | ```json\n%(tca02_json)s\n``` |
| **预期错误码** | ADRG-FALLBACK |
| **预期错误信息** | 主要手术编码不在系统支持范围内，回退到内科 ADRG |
| **预期系统行为** | get_mdc("K83.105") → MDCH；get_adrg(MDCH, ["999.99"]) → 手术 999.99 不匹配，回退 MEDICAL_ADRG → HR1 |
| **测试步骤** | 1. get_mdc("K83.105") → MDCH<br>2. 手术 999.99 不匹配 ADRG_TABLE，回退到 MEDICAL_ADRG["MDCH"] → HR1<br>3. check_complications([]) → NONE → HR15 |
| **预期结果** | drg_result: {"mdc":"MDCH","adrg":"HR1","drg":"HR15","complication":"NONE","reason":["ICD编码999.99不在ADRG_TABLE，回退内科ADRG"]} |

### TC-A-03：缺少主要诊断字段

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-03 |
| **用例名称** | 缺少主要诊断字段 |
| **异常类型** | 信息缺失 |
| **触发条件** | JSON 中不包含"主要诊断"键 |
| **输入数据** | ```json\n%(tca03_json)s\n``` |
| **预期错误码** | EMR-PARSE-FAIL |
| **预期错误信息** | 缺少必填字段"主要诊断"，无法进行 DRG 分组 |
| **预期系统行为** | entity._parse_emr() 检测到缺少主要诊断，返回 None，降级到 NLP 模式 |
| **测试步骤** | 1. entity._parse_emr() 检测到无"主要诊断"字段 → 返回 None<br>2. entity agent 降级到 NLP 模式<br>3. 从 query 自然语言中抽取实体 |
| **预期结果** | emr_data 为空字典，entities 由 LLM 从 query 抽取，mode 降级为 NLP |

### TC-A-04：缺少年龄字段

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-04 |
| **用例名称** | 缺少年龄字段 |
| **异常类型** | 信息缺失 |
| **触发条件** | JSON 中不包含"年龄"字段 |
| **输入数据** | ```json\n%(tca04_json)s\n``` |
| **预期错误码** | EMR-MISSING-AGE |
| **预期错误信息** | 缺少"年龄"字段，年龄信息设为 0 或默认值 |
| **预期系统行为** | entity._parse_emr() 解析年龄为 0 或默认值，emr_data["age"]=0，DRG 分组仍正常执行（年龄当前不参与分组逻辑） |
| **测试步骤** | 1. entity._parse_emr() 解析 JSON，"年龄"字段缺失 → age=0（默认值）<br>2. get_mdc("K80.0") → MDCH<br>3. DRG 分组正常执行 |
| **预期结果** | emr_data 中 age=0，但 drg_result 正常（HC25），reason 包含"年龄字段缺失，已设为默认值" |

### TC-A-05：产科诊断 + 骨科手术逻辑冲突

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-05 |
| **用例名称** | 产科诊断 + 骨科手术逻辑冲突 |
| **异常类型** | 逻辑冲突 |
| **触发条件** | 主要诊断为产科（MDCO），主要手术为骨科（MDCI），MDC 与 ADRG 不匹配 |
| **输入数据** | ```json\n%(tca05_json)s\n``` |
| **预期错误码** | MDC-ADRG-MISMATCH |
| **预期错误信息** | 诊断 MDCO（妊娠分娩）与手术 ADRG（MDCI 骨科）不匹配 |
| **预期系统行为** | get_mdc("O80.0") → MDCO；get_adrg(MDCO, ["81.54001"]) → 81.54001 不在 MDCO 下，MEDICAL_ADRG["MDCO"] → OR1 |
| **测试步骤** | 1. get_mdc("O80.0") → MDCO<br>2. get_adrg(MDCO, ["81.54001"]) → 81.54001 不在 MDCO 下，MEDICAL_ADRG["MDCO"] → OR1<br>3. check_complications([]) → NONE → OR15 |
| **预期结果** | drg_result: {"mdc":"MDCO","adrg":"OR1","drg":"OR15","complication":"NONE","reason":["MDCO诊断与MDCI手术不匹配，回退产科内科ADRG"]} |

### TC-A-06：JSON 格式截断

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-06 |
| **用例名称** | JSON 格式截断 |
| **异常类型** | 格式错误 |
| **触发条件** | JSON 字符串缺少闭合括号，无法被 json.loads() 解析 |
| **输入数据** | ```json\n%(tca06_json)s\n``` |
| **预期错误码** | JSON-DECODE-ERROR |
| **预期错误信息** | JSON 格式错误，无法解析电子病历 |
| **预期系统行为** | json.loads() 抛出 JSONDecodeError，entity agent 降级到 NLP 模式 |
| **测试步骤** | 1. entity._parse_emr() 调用 json.loads() → JSONDecodeError<br>2. 捕获异常，返回 None<br>3. entity agent 降级到 NLP 模式 |
| **预期结果** | emr_data 为空字典，mode 降级为 NLP，answer 包含 NLP 分析结果 |

### TC-A-07：字段类型错误（年龄为字符串）

| 属性 | 内容 |
|------|------|
| **用例编号** | TC-A-07 |
| **用例名称** | 字段类型错误（年龄为字符串） |
| **异常类型** | 格式错误 |
| **触发条件** | "年龄"字段值为中文字符串"六十八"而非整数 |
| **输入数据** | ```json\n%(tca07_json)s\n``` |
| **预期错误码** | EMR-TYPE-ERROR |
| **预期错误信息** | "年龄"字段类型错误，期望整数 |
| **预期系统行为** | json.loads() 解析成功（"六十八"作为字符串合法），entity._parse_emr() 处理年龄时类型不匹配，age 被设为 0 或默认值 |
| **测试步骤** | 1. json.loads() 解析 JSON 成功（年龄为字符串）<br>2. entity._parse_emr() 检查年龄类型 → int(age) 失败 → age=0（默认值）<br>3. DRG 分组正常执行（年龄不参与分组逻辑） |
| **预期结果** | emr_data 中 age=0，drg_result 正常，reason 包含"年龄字段类型错误，已设为默认值" |

## 5. 测试数据

### 5.1 异常病历样本

| 用例编号 | 异常类型 | 错误字段 | 错误值 | 预期处理结果 |
|----------|----------|----------|--------|--------------|
| TC-A-01 | 编码错误 | 主要诊断.疾病编码 | XXXX.9 | get_mdc() → None，NLP 降级 |
| TC-A-02 | 编码错误 | 主要手术.手术编码 | 999.99 | 回退到内科 ADRG（HR1） |
| TC-A-03 | 信息缺失 | 无"主要诊断"键 | - | _parse_emr() → None，NLP 降级 |
| TC-A-04 | 信息缺失 | 无"年龄"字段 | - | age=0，DRG 正常执行 |
| TC-A-05 | 逻辑冲突 | MDCO + MDCI 不匹配 | O80.0 + 81.54001 | 回退到 MDCO 内科 OR1 |
| TC-A-06 | 格式错误 | JSON 截断 | 不完整 JSON | JSONDecodeError，NLP 降级 |
| TC-A-07 | 格式错误 | 年龄类型错误 | "六十八" | age=0，DRG 正常执行 |

### 5.2 错误处理验证表

| 异常场景 | 检测点 | 检测函数 | 预期返回值 | 备选路径 |
|----------|--------|----------|------------|----------|
| 无效 ICD-10 | MDC 匹配 | kg/drg_loader.get_mdc() | None | entity agent → NLP 模式 |
| 无效 ICD-9-CM-3 | ADRG 匹配 | kg/drg_loader.get_adrg() | MEDICAL_ADRG 兜底 | 正常返回内科 ADRG |
| 缺少主要诊断 | EMR 解析 | entity._parse_emr() | None | entity agent → NLP 模式 |
| 缺少年龄 | EMR 解析 | entity._parse_emr() | age=0 | 继续 DRG 分组（年龄不参与） |
| MDC/ADRG 不匹配 | ADRG 回退 | kg/drg_loader.get_adrg() | MEDICAL_ADRG[mdc] | 回退到内科 ADRG |
| JSON 格式错误 | JSON 解析 | json.loads() | JSONDecodeError | entity agent → NLP 模式 |
| 字段类型错误 | 年龄处理 | entity._parse_emr() | age=0（默认值） | 继续 DRG 分组 |

---

*本文档由 TCGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


def _offline_requirements_doc(prompt: str) -> str:
    """生成离线需求分析文档模板。

    描述 MedReasonerAgent —— 基于 LangGraph 的多 Agent 生物医学知识图谱推理系统，
    核心能力为 DRG（疾病诊断相关分组）医保入组推理与临床决策支持演示。
    """
    import re
    from datetime import date
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    today = date.today().isoformat()
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 需求分析文档 |
| **文档版本** | V1.0 |
| **生成日期** | {today} |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 引言

### 1.1 编写目的

本文档旨在对 {project_name} —— 多 Agent 医疗知识推理与可视化系统进行完整的需求分析。系统基于 LangGraph 编排多 Agent 工作流，结合 DRG 知识图谱检索和 LLM/SGLang 模型推理能力，实现可解释、可追踪、可视化的临床决策支持演示。

### 1.2 适用范围

本文档覆盖 {project_name} 的全部功能模块，包括：后端多 Agent 推理服务（FastAPI + LangGraph）、DRG 知识图谱检索、LLM/SGLang 模型推理与路由、WebSocket 事件流、前端 Agent 通信界面（Next.js + React Flow）和运行决策树可视化。

本文档不覆盖：真实医院 HIS/EMR 集成、医疗器械级诊断功能、药品处方合法性审核、用户账号体系与权限管理。

### 1.3 术语与缩写

| 术语/缩写 | 全称 | 说明 |
|-----------|------|------|
| DRG | Diagnosis Related Groups | 疾病诊断相关分组，用于医疗费用管理与临床路径分组 |
| KG | Knowledge Graph | 知识图谱，存储症状-疾病-DRG分组-治疗方案等关系 |
| LLM | Large Language Model | 大语言模型，用于医学实体抽取、推理、解释生成 |
| SGLang | SGLang | 高效 LLM 推理服务框架 |
| LangGraph | LangGraph | 基于有向图（DAG）的 LLM Agent 工作流编排框架 |
| React Flow | @xyflow/react | 前端节点图可视化库 |
| WebSocket | WebSocket | 双向实时通信协议，用于推送 Agent 执行事件 |
| Agent | Agent | 系统中承担单一推理步骤的独立处理单元 |
| DRGState | DRGState | 跨 Agent 传递的全局共享数据字典（TypedDict） |
| EventBus | EventBus | 发布/订阅模式的事件总线 |

## 2. 系统概述

### 2.1 项目背景

在医疗 AI 领域，多 Agent 系统正成为临床决策支持的重要技术方向。传统单模型推理存在过程不透明、推理链不可追溯等问题。{project_name} 旨在构建一个可解释、可追踪、可视化的多 Agent 医疗推理原型系统，聚焦于 **DRG（疾病诊断相关分组）医保入组推理**场景——根据患者症状和诊断信息，通过知识图谱检索和 LLM 推理，给出可能的 DRG 分组和治疗方案参考。

### 2.2 系统定位

本系统定位为**医疗推理原型与临床决策支持演示系统**：

- 是**医疗推理原型**，不是医疗诊断系统
- 是**临床决策支持演示**，不是临床决策执行系统
- 是**多 Agent 可解释推理教学系统**，不是医学教育考核系统
- 是**研究性原型**，不是生产级医疗器械软件

### 2.3 建设目标

1. **多 Agent 流水线**：从用户输入自然语言医疗问题开始，依次完成实体抽取、病例理解、DRG 检索、医学推理、路径排序、治疗方案草案生成和最终解释输出的完整链路。
2. **可解释推理**：每一步 Agent 的决策过程可被用户审查，Agent 间传递的上下文可追溯。
3. **实时可视化**：通过 WebSocket 事件流驱动前端运行决策树，实时展示执行进度。
4. **模型可替换**：支持 DeepSeek、OpenAI 兼容 API、SGLang 等多种模型服务，通过环境变量配置即可切换。
5. **医疗安全**：所有输出包含 AI 生成声明、临床确认建议和风险提示。
6. **离线可运行**：未配置 API Key 时，系统通过确定性 fallback 机制仍可完整演示全链路。

### 2.4 系统边界

**系统范围包含：**
- 后端多 Agent 推理服务（FastAPI + LangGraph）
- DRG 知识图谱检索（kg/ 模块）
- LLM / SGLang 模型推理与模型路由（runtime/router.py）
- WebSocket 事件流推送（runtime/event_bus.py）
- 前端 Agent 通信界面（Next.js + React Flow）
- 运行决策树可视化（AgentGraph 组件）
- 文档自动生成子系统（DocGen Agent + VDoc Agent）

**系统范围不包含：**
- 真实医院 HIS/EMR 系统集成
- 医疗器械级诊断功能
- 药品处方合法性审核
- 用户账号和权限管理系统
- 多租户隔离与数据持久化

## 3. 用户需求分析

### 3.1 目标用户角色

| 角色 | 描述 | 关注点 |
|------|------|--------|
| 普通用户 | 希望体验医疗 AI 推理过程的用户 | 输出是否易懂、推理过程是否可信 |
| 医保审核员 | 模拟 DRG 入组审核场景 | DRG 分组逻辑是否合理、路径是否可追溯 |
| 研发人员 | 医疗 AI 原型研发或系统集成工程师 | Agent 间数据传递、链路完整性、模型切换 |
| 教学人员 | 医疗 AI 课程或科研项目的演示人员 | 运行树是否清晰展示决策过程 |

### 3.2 用户场景分析

**场景一：医疗推理演示**：用户输入医疗问题（如"患者胸痛、发热，有糖尿病风险和炎症指标异常"），系统返回完整推理过程和结果，包含 Agent 分步执行说明、医疗报告摘要、治疗方案草案和风险提示。

**场景二：DRG 入组审核模拟**：医保审核员输入患者诊断信息，系统通过知识图谱检索症状→疾病→DRG 分组的映射关系，展示多跳推理路径和入组依据。

**场景三：多 Agent 通讯调试**：研发人员检查 Agent 间的数据传递，展开内部上下文查看原始输出和状态字段值，通过运行决策树查看执行路径。

**场景四：模型切换验证**：研发人员通过修改环境变量切换推理引擎（LLM/SGLang），验证不同模型服务下的执行行为和推理结果差异。

### 3.3 用户故事

| 编号 | 角色 | 需求描述 | 优先级 | 验收条件 |
|------|------|----------|--------|----------|
| US-01 | 普通用户 | 输入医疗问题后看到自然语言解释，而非内部变量 | 高 | 默认消息为自然语言 Markdown |
| US-02 | 普通用户 | 看到运行树展示系统每一步的决策过程 | 高 | 运行树随执行实时更新 |
| US-03 | 普通用户 | 医疗建议包含风险提示和免责声明 | 高 | 每条医疗输出含 warning |
| US-04 | 医保审核员 | 查看 DRG 分组的推理依据和关联路径 | 高 | 推理路径展示症状→疾病→DRG 完整链路 |
| US-05 | 研发人员 | 展开内部详情查看 Agent 间传递的数据 | 中 | 内部上下文默认折叠，可手动展开 |
| US-06 | 研发人员 | 模型服务通过配置切换，无需修改业务代码 | 中 | 修改 .env 即可切换模型服务 |
| US-07 | 研发人员 | 无 API Key 时全链路可运行 | 高 | offline fallback 返回确定性文本 |
| US-08 | 教学人员 | 运行树纵向排列，同层候选水平排列 | 中 | 运行树布局符合要求 |

### 3.4 用例分析

| 编号 | 名称 | 参与者 | 前置条件 | 基本流程 |
|------|------|--------|----------|----------|
| UC-01 | 执行医疗推理 | 普通用户 | 后端服务已启动 | 输入 query → 选择语言 → 发送 → 系统执行多 Agent 推理链路 → 前端实时展示 Agent 消息和运行树 → 显示最终答案 |
| UC-02 | DRG 入组推理 | 医保审核员 | 后端服务已启动 | 输入诊断信息 → Entity Agent 抽取实体 → Retrieval Agent 检索 DRG 子图 → Reasoning Agent 推演入组路径 → 输出 DRG 分组和治疗方案 |
| UC-03 | 查看内部上下文 | 研发人员 | 已完成至少一次推理 | 在对话区找到 Agent 消息 → 点击"查看 Agent 内部传递内容" → 展开原始输出和上下文摘要 |
| UC-04 | 切换推理引擎 | 研发人员 | 有对应 API Key | 修改 .env 中 REASONING_ENGINE → 重启服务 → 运行推理 → 运行树显示对应引擎选项 |

## 4. 功能需求

### 4.1 多 Agent 推理链路

系统采用 LangGraph 编排固定的线性多 Agent 流水线，各 Agent 通过共享 DRGState 字典传递信息：

```
supervisor → entity → medical_report → retrieval → reasoning → ranking → treatment_plan → explain
```

| 编号 | Agent | 功能 | 输入 | 输出 |
|------|-------|------|------|------|
| FR-01 | Supervisor | 意图分类，判断推理模式（simple/multi-hop/deep-reasoning） | query, language | plan.mode |
| FR-02 | Entity | 从用户 query 中抽取生物医学实体 | query, language | entities[] |
| FR-03 | Medical Report | 将 query 分析为结构化病例理解 | query, language | medical_report{{possible_disease, symptoms, risk_factors, severity}} |
| FR-04 | Retrieval | 基于抽取的实体检索 DRG 知识图谱子图 | entities[] | subgraph{{nodes, edges, hops}} |
| FR-05 | Reasoning | 基于实体和图谱上下文生成医学推理路径 | entities, subgraph | reasoning_paths[] |
| FR-06 | Ranking | 对候选推理路径进行排序 | reasoning_paths | ranked_paths[] |
| FR-07 | Treatment Plan | 生成治疗方案草案，包含风险提示 | medical_report, ranked_paths | treatment_plan{{options, drug_candidates, warnings}} |
| FR-08 | Explain | 汇总所有前置步骤，生成面向用户的最终自然语言解释 | ranked_paths, medical_report, treatment_plan | answer |

### 4.2 DRG 入组核心功能

系统围绕 DRG（疾病诊断相关分组）构建知识图谱和推理能力：

**FR-09：DRG 知识图谱** — 系统内置轻量级 DRG 知识图谱（`kg/drg_loader.py`），定义五类基本关系：

| 源节点类型 | 关系 | 目标节点类型 | 说明 |
|-----------|------|-------------|------|
| symptom | suggests | disease | 症状提示可能疾病 |
| disease | mapped_to | drg_group | 疾病映射到 DRG 分组 |
| disease | treated_by | treatment | 疾病对应治疗方式 |
| risk_factor | increases_risk_of | disease | 风险因素增加疾病概率 |
| test | confirms_or_rules_out | disease | 检查项目确定或排除疾病 |

**FR-10：DRG 子图检索** — `kg/query.py` 的 `get_subgraph(entities, hops)` 基于实体匹配图谱边，支持 1-3 跳扩展，返回子图 `{{nodes, edges, hops}}`。

**FR-11：DRG 入组推理流程** — 完整推理链路：Entity Agent 抽取医学实体 → Retrieval Agent 查找 symptom→disease→drg_group 映射 → Reasoning Agent 推演 DRG 入组路径 → Ranking Agent 排序候选路径 → Treatment Plan Agent 基于入组结果生成治疗方案。

### 4.3 可视化与交互

**FR-12：运行决策树** — 前端右侧使用 React Flow 渲染运行时决策树，每个 Agent 节点展示候选决策选项，实际选中路径以绿色标识。布局规则：纵向排列（每层 y+=184px）、水平候选（间距 96px）、延迟显示（未执行层级不提前渲染）。

**FR-13：对话式通信界面** — 前端左侧展示对话式 Agent 消息流，每条消息包含 Agent 名称、自然语言说明，内部上下文默认折叠，点击"查看 Agent 内部传递内容"可展开原始输出。

**FR-14：内部信息分层展示** — 用户可见层（始终显示）：Agent 名称、自然语言说明、执行摘要；内部详情层（默认折叠）：选中工具名、原始输出文本、上下文字段值。

### 4.4 模型服务与离线能力

**FR-15：模型服务配置化切换** — 通过环境变量支持 DeepSeek（`OPENAI_BASE_URL=https://api.deepseek.com`）、OpenAI 兼容 API、SGLang（`SGLANG_BASE_URL`）。`REASONING_ENGINE=llm|sglang` 环境变量控制推理引擎选择。

**FR-16：离线确定性 Fallback** — 未配置任何 API Key 时，所有 Agent 返回确定性 fallback 文本，保证全链路可运行和 UI 可测试。

**FR-17：Trace 回放** — `GET /trace/replay` 返回当前进程内 EventBus 已记录的全部事件，支持执行过程回溯审查。

## 5. 非功能需求

### 5.1 性能需求
- WebSocket 事件延迟：Agent 执行完成后 100ms 内到达前端
- 前端渲染帧率：运行树更新时不低于 30fps
- API 超时：同步 `/run` 接口超时上限 120s

### 5.2 可用性需求
- 支持中文和英文界面/输出语言切换
- 用户可见消息支持 Markdown 渲染（标题、列表、加粗、代码块）
- 首次使用显示空状态引导文案

### 5.3 可靠性需求
- 离线可运行：无 API Key 时全链路可跑通
- WebSocket 断连：前端显示错误状态，可重新连接
- 模型调用失败：不阻断整体链路，记录错误并继续

### 5.4 可维护性需求
- 严格分层：API / Graph / Runtime / Agent / KG / Tools / Frontend
- 模块化：每个 Agent 为独立函数，只承担单一推理步骤
- 配置外部化：所有模型配置通过 `.env` 管理

### 5.5 安全需求
- `.env`（含 API Key）不提交到 Git
- 所有医疗输出必须包含 warning 和免责声明
- 系统定位声明：不是医疗器械，不是诊断系统，不提供医疗建议
- API Key 不走前端，所有模型调用在后端执行

### 5.6 医疗安全与伦理约束
- 禁止声称给出最终诊断
- 禁止直接开具处方（drug_candidates 标明仅供参考）
- 所有输出提示"需经持证专业人员确认"
- 系统始终明确标识 AI 生成内容

## 6. 数据需求

### 6.1 DRGState 全局状态

| 字段名 | 类型 | 写入者 | 说明 |
|--------|------|--------|------|
| query | str | API 初始化 | 用户输入的自然语言医疗问题 |
| language | str | API 初始化 | 输出语言（zh/en） |
| entities | List[str] | Entity Agent | 抽取的医学实体列表 |
| subgraph | dict | Retrieval Agent | DRG 子图 |
| reasoning_paths | List | Reasoning Agent | 医学推理路径 |
| ranked_paths | List | Ranking Agent | 排序后推理路径 |
| medical_report | dict | Medical Report Agent | 结构化病例理解 |
| treatment_plan | dict | Treatment Plan Agent | 治疗方案草案 |
| answer | str | Explain Agent | 最终自然语言解释 |
| plan | dict | Supervisor Agent | 执行计划 |
| trace | List[dict] | 各 Agent | 执行轨迹日志 |

### 6.2 事件数据模型

EventBus 推送的事件对象：`event`（node_start/node_end/complete/error）、`node`（Agent 名称）、`decision_id`、`parent_decision_id`、`decision_options`（候选选项列表）、`selected_option`（实际选中）、`output`（Agent 输出）、`state`（当前状态快照）。

### 6.3 知识图谱数据模型

DRG 图谱边结构：`{{source: str, relation: str, target: str}}`。关系类型：suggests、mapped_to、treated_by、increases_risk_of、confirms_or_rules_out。子图结构：`{{nodes: List[str], edges: List[dict], hops: int}}`。

## 7. 外部接口需求

### 7.1 HTTP API 接口

| 方法 | 路径 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| GET | /health | - | {{"status": "ok"}} | 健康检查 |
| POST | /run | {{"query":"...", "language":"zh", "mode":"drg"}} | {{"answer":"...", "trace":[...], "medical_report":{{...}}, "treatment_plan":{{...}}}} | 同步执行智能体工作流 |
| GET | /trace/replay | - | {{"events": [...]}} | 回放 EventBus 历史事件 |
| POST | /docgen/generate | {{"query":"...", "doc_type":"requirements"}} | {{"doc_final":"...", "storage_path":"...", "review_report":{{...}}}} | 文档生成并存储 |

### 7.2 WebSocket 接口

| 路径 | 客户端发送 | 服务端事件流 |
|------|-----------|-------------|
| /ws/run | {{"query":"...", "language":"zh", "mode":"drg"}} | node_start → node_end → ... → complete |

WebSocket 连接建立后，后端每执行完一个 Agent 即推送 node_start/node_end 事件，前端实时更新对话消息和运行决策树。

### 7.3 环境变量契约

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OPENAI_API_KEY | OpenAI 或兼容 API 密钥 | — |
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | — |
| OPENAI_BASE_URL | API 服务地址 | — |
| OPENAI_MODEL | 默认模型名称 | gpt-4o-mini |
| REASONING_ENGINE | 推理引擎（llm/sglang） | sglang |
| SGLANG_BASE_URL | SGLang 推理服务地址 | — |
| NEXT_PUBLIC_API_BASE | 前端连接的后端地址 | http://localhost:8000 |

## 8. 约束与假设

### 8.1 技术约束
- LangGraph 工作流当前为固定线性拓扑（无条件分支）
- EventBus 为进程内实现（不支持分布式）
- DRG 图谱为内存加载（不支持大规模知识持久化）
- 无会话隔离（单用户原型阶段）

### 8.2 业务约束
- 系统不得用于真实临床诊断
- 系统为原型级别，不保证生产级可靠性
- 不保存真实患者隐私数据

### 8.3 假设条件
- 用户理解系统为原型，不会将输出作为医疗决策依据
- 使用外部模型时需要网络连接
- 当前阶段假设单用户操作模式

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


def _offline_architecture_doc(prompt: str) -> str:
    """生成离线架构设计文档模板。"""
    import re
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 架构设计文档 |
| **文档版本** | V1.0 |
| **生成日期** | 2026-06-08 |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 总体架构
### 1.1 架构风格
{project_name} 采用分层架构（Layered Architecture），分后端服务层、运行时层、智能体层和前端展示层。

### 1.2 系统架构图
```
┌─────────────────────────────────────┐
│         用户浏览器 (Frontend)         │
│    Next.js + React Flow + Zustand   │
├─────────────────────────────────────┤
│       HTTP / WebSocket (JSON)       │
├─────────────────────────────────────┤
│         FastAPI 后端服务             │
│  ┌───────────────────────────────┐  │
│  │     Graph Layer (graph/)      │  │
│  ├───────────────────────────────┤  │
│  │    Runtime Layer (runtime/)   │  │
│  │  ┌────────┬────────┬───────┐  │  │
│  │  │Executor│EventBus│Router │  │  │
│  │  └────────┴────────┴───────┘  │  │
│  ├───────────────────────────────┤  │
│  │     Agent Layer (agents/)     │  │
│  │  (DRG / DocGen / VDoc agents) │  │
│  ├───────────────────────────────┤  │
│  │   KG Layer + Tools Layer      │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│        LLM API / SGLang            │
└─────────────────────────────────────┘
```

### 1.3 技术栈总览
| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js, TypeScript, React Flow | 页面渲染与可视化 |
| 前端状态 | Zustand | 全局状态管理 |
| 后端框架 | FastAPI | REST/WebSocket 服务 |
| 工作流编排 | LangGraph | 多智能体流水线 |
| 模型调用 | OpenAI SDK | LLM API 调用 |
| 知识图谱 | 内存图谱 (kg/) | DRG 关系数据 |

## 2. 模块划分
### 2.1 模块总览
| 模块 | 路径 | 职责 | 依赖 |
|------|------|------|------|
| API 层 | app.py | HTTP 路由、WebSocket | graph, runtime |
| Graph 层 | graph/ | 状态定义、工作流编译 | agents, runtime |
| Runtime 层 | runtime/ | 执行器、事件总线、策略 | 无 |
| Agent 层 | agents/ | 各智能体实现 | tools, kg, runtime |
| KG 层 | kg/ | 知识图谱加载与查询 | 无 |
| Tools 层 | tools/ | LLM 客户端、trace 工具 | 无 |
| Frontend 层 | frontend/ | UI 组件、状态管理 | 后端 API |

### 2.2 各模块详细设计
#### Agent 层
- **DRG 入组智能体**：8 个子智能体线性流水线，处理医疗推理
- **文档生成智能体**：6 个子智能体，代码扫描→组稿→格式化→审核
- **虚拟文档系统智能体**：5 个子智能体，接收→验证→标记→存储→通知

## 3. 数据流设计
### 3.1 核心数据流
用户输入 → API 层（mode 路由）→ Graph 层（工作流选择）→ Agent 层（流水线执行）→ 事件总线 → 前端展示

### 3.2 状态管理
- 后端：TypedDict 状态在各 Agent 间传递
- 前端：Zustand Store 管理 UI 状态

### 3.3 事件机制
EventBus（发布/订阅模式）在 Agent 执行时发送 node_start/node_end 事件，前端通过 WebSocket 订阅。

## 4. 组件/服务通信
### 4.1 同步通信
| 方法 | 路径 | 请求 | 响应 | 说明 |
|------|------|------|------|------|
| POST | /run | query, language, mode | answer, trace, state | 执行智能体 |
| POST | /docgen/generate | query, doc_type | doc_final, storage_path | 生成并保存文档 |
| GET | /docgen/docs | - | documents[] | 文档列表 |
| GET | /health | - | status | 健康检查 |

### 4.2 异步通信
WebSocket /ws/run 支持实时事件流。

## 5. 技术选型
### 5.4 选型理由
| 技术项 | 选型 | 理由 | 替代方案 |
|--------|------|------|----------|
| 后端框架 | FastAPI | 异步支持、WebSocket 原生支持 | Flask, Django |
| 工作流 | LangGraph | 有向图编排、状态管理 | 自定义 DAG |
| 前端 | Next.js | SSR、React 生态 | Vite + React |
| 可视化 | React Flow | 节点图渲染 | D3.js, Cytoscape |
| 模型调用 | OpenAI SDK | 多模型兼容 | httpx 直接调用 |

## 6. 部署架构
### 6.1 部署拓扑
- 后端：单进程 FastAPI（uvicorn）
- 前端：Next.js dev server 或静态导出
- 依赖：外部 LLM API（DeepSeek / OpenAI / SGLang）

## 7. 安全设计
### 7.1 安全边界
- API Key 通过环境变量管理，不写入代码
- 生成的文档自动标记"草稿"状态和 AI 生成声明
- 前端不暴露后端 API Key

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""


def _offline_testing_doc(prompt: str) -> str:
    """生成离线测试文档模板。"""
    import re
    project_match = re.search(r'Project:\s*(\S+)', prompt)
    project_name = project_match.group(1) if project_match else "MedReasonerAgent"
    return f"""| 属性 | 内容 |
|------|------|
| **项目名称** | {project_name} |
| **文档类型** | 测试文档 |
| **文档版本** | V1.0 |
| **生成日期** | 2026-06-08 |
| **生成方式** | AI 自动生成（DocGen Agent） |
| **状态** | 草稿 |

## 1. 测试策略
### 1.1 测试层次
```
验收测试（E2E 场景验证）
    ^
集成测试（前后端联调、API 测试）
    ^
单元测试（模块级函数测试）
    ^
静态检查（构建、lint、安全审计）
```

### 1.2 测试方法
- 黑盒测试：API 接口功能测试
- 白盒测试：Agent 函数单元测试
- 手动测试：UI 交互验证
- 自动化测试：API 回归测试

## 2. 单元测试方案
### 2.1 测试范围
- Agent 层：每个 Agent 函数的输入/输出验证
- Graph 层：工作流编译正确性
- Runtime 层：EventBus 发布/订阅、Executor 生命周期
- Tools 层：LLM 调用封装、trace 工具

### 2.2 测试用例
| 编号 | 模块 | 测试项 | 输入 | 预期输出 |
|------|------|--------|------|----------|
| TC-01 | doc_supervisor | 文档类型分类 | query="生成需求分析" | doc_type="requirements" |
| TC-02 | doc_supervisor | 架构文档分类 | query="生成架构设计" | doc_type="architecture" |
| TC-03 | code_scanner | 代码扫描 | 项目根路径 | 返回模块清单 |
| TC-04 | context_collector | 上下文收集 | state with code_analysis | 返回上下文数据 |
| TC-05 | doc_composer | 文档组稿 | state with context | 返回 Markdown 字符串 |
| TC-06 | doc_formatter | 格式规范化 | 初稿文档 | 含元信息表的格式化文档 |
| TC-07 | doc_reviewer | 文档审核 | 格式化文档 | 审核报告含通过/失败 |
| TC-08 | doc_storer | 文件存储 | 文档内容 | 返回存储路径 |

### 2.3 覆盖率目标
- 代码行覆盖率 >= 80%
- Agent 函数覆盖率 100%

## 3. 集成测试方案
### 3.1 集成策略
自底向上：先测试单个 Agent，再测试 Agent 流水线，最后测试端到端 API。

### 3.2 接口测试用例
| 编号 | 接口 | 测试场景 | 请求 | 预期响应 |
|------|------|----------|------|----------|
| TC-I01 | POST /run (drg) | DRG 推理 | {{"query":"chest pain","mode":"drg"}} | 200, 含 answer 和 trace |
| TC-I02 | POST /run (docgen) | 文档生成 | {{"query":"需求分析","mode":"docgen","doc_type":"requirements"}} | 200, 含 doc_final |
| TC-I03 | POST /docgen/generate | 生成+存储 | {{"query":"架构设计","doc_type":"architecture"}} | 200, 含 storage_path |
| TC-I04 | GET /docgen/docs | 文档列表 | - | 200, 含 documents[] |

## 4. 系统测试方案
### 4.1 功能测试
- DRG 入组全链路测试
- 文档生成全链路测试
- 虚拟文档存储测试
- 前端三选项卡切换测试

### 4.2 性能测试
- 文档生成响应时间 < 120s
- WebSocket 事件延迟 < 100ms

### 4.3 安全测试
- 空 query 不可提交
- API Key 不泄露
- 生成文档包含 AI 声明

### 4.4 兼容性测试
- Chrome / Safari / Firefox 浏览器
- Python 3.10+
- Node.js 18+

## 5. 验收测试方案
### 5.1 验收标准
- [ ] DRG 选项卡可正常执行医疗推理
- [ ] 文档生成选项卡可生成三种文档
- [ ] 虚拟文档选项卡正常显示
- [ ] 生成的文档保存到 generated_docs/ 目录
- [ ] 文档格式符合 doc_spec.md 规范
- [ ] `npm run build` 前端构建成功
- [ ] 离线 fallback 模式下全链路可运行

### 5.2 验收流程
1. 环境准备：安装依赖，配置（或不配置）API Key
2. 功能验证：逐项测试三个智能体系统
3. 文档审核：检查生成文档的格式和质量
4. 签署验收

## 6. 测试环境
### 6.1 硬件环境
- CPU: >= 4 cores
- RAM: >= 8GB
- Disk: >= 2GB 可用空间

### 6.2 软件环境
- OS: macOS / Linux / Windows WSL
- Python: >= 3.10
- Node.js: >= 18
- 浏览器: Chrome 100+

### 6.3 测试数据
- 测试 query 使用脱敏医疗描述或文档生成指令

## 7. 缺陷管理
### 7.1 缺陷等级定义
| 等级 | 名称 | 说明 | 响应时间 |
|------|------|------|----------|
| P0 | 阻断 | 系统不可用，核心功能崩溃 | 2小时 |
| P1 | 严重 | 主要功能异常，影响使用 | 24小时 |
| P2 | 一般 | 次要功能异常，有替代方案 | 72小时 |
| P3 | 轻微 | UI 显示问题、建议性改进 | 下一迭代 |

### 7.2 缺陷跟踪流程
发现缺陷 → 记录（等级、复现步骤）→ 分配 → 修复 → 验证 → 关闭

---

*本文档由 DocGen Agent 自动生成，状态为草稿，需人工审核确认。*
"""
