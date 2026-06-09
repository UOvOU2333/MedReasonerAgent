import json
from tools.trace import append_trace


def medical_record_context_agent(state):
    """
    收集并提供标准化的病历样本模板和 DRG 编码参考数据。
    纯计算步骤，不依赖 LLM。

    重要：所有模板和参考数据严格对齐 `entity._parse_emr()` 的预期格式
    和 `kg/drg_loader` 中 CN-DRG 2018 的查表编码体系。
    """
    language = state.get("language", "zh")

    # ── 标准病历 JSON 模板（对齐 entity._parse_emr() 的 EMR 格式）──
    sample_record_template = {
        "性别": "",            # str: "男" 或 "女"
        "年龄": 0,             # int: 患者年龄
        "主要诊断": {
            "疾病名称": "",    # str: 诊断中文名称
            "疾病编码": "",    # str: ICD-10 编码（如 C16.301, J15.9）
        },
        "次要诊断列表": [
            {"疾病名称": "", "疾病编码": ""},
        ],
        "主要手术": {
            "手术名称": "",    # str: 手术中文名称
            "手术编码": "",    # str: ICD-9-CM-3 编码（如 36.06, 47.0）
            "手术级别": 0,     # int: 1-4 级手术
        },
        "其他手术列表": [
            {"手术名称": "", "手术编码": "", "手术级别": 0},
        ],
    }

    # ── DRG 常用 ICD-10 诊断编码参考 ──
    # 选自 CC_SET / MCC_SET / MDC_TABLE 中实际存在的编码
    icd10_diagnosis_ref = [
        # 循环系统 — MDCF
        {"code": "I21.3", "name": "急性透壁性心肌梗死", "category": "循环系统", "cc_level": "MCC"},
        {"code": "I21.4", "name": "急性非透壁性心肌梗死", "category": "循环系统", "cc_level": "MCC"},
        {"code": "I50.9", "name": "心力衰竭", "category": "循环系统", "cc_level": "MCC"},
        {"code": "I63.801", "name": "腔隙性脑梗死", "category": "循环系统", "cc_level": "CC"},
        {"code": "I63.9", "name": "脑梗死", "category": "循环系统", "cc_level": "CC"},
        {"code": "I10", "name": "原发性高血压", "category": "循环系统", "cc_level": "CC"},
        {"code": "I48.9", "name": "心房颤动", "category": "循环系统", "cc_level": "CC"},
        # 呼吸系统 — MDCE
        {"code": "J15.9", "name": "细菌性肺炎", "category": "呼吸系统", "cc_level": "CC"},
        {"code": "J44.9", "name": "慢性阻塞性肺疾病", "category": "呼吸系统", "cc_level": "CC"},
        {"code": "J86.000x013", "name": "支气管胆管瘘", "category": "呼吸系统", "cc_level": "NONE"},
        # 消化系统 — MDCG
        {"code": "C16.301", "name": "胃窦恶性肿瘤", "category": "消化系统", "cc_level": "NONE"},
        {"code": "K66.002", "name": "肠粘连", "category": "消化系统", "cc_level": "CC"},
        {"code": "Z98.800", "name": "术后状态", "category": "消化系统", "cc_level": "CC"},
        # 肝、胆、胰 — MDCH
        {"code": "K83.105", "name": "胆管狭窄", "category": "肝胆胰", "cc_level": "NONE"},
        {"code": "K80.0", "name": "胆囊结石伴急性胆囊炎", "category": "肝胆胰", "cc_level": "NONE"},
        {"code": "K76.807", "name": "肝囊肿", "category": "肝胆胰", "cc_level": "CC"},
        # 内分泌 — MDCK
        {"code": "E11.9", "name": "2型糖尿病", "category": "内分泌", "cc_level": "CC"},
        {"code": "E78.5", "name": "高脂血症", "category": "内分泌", "cc_level": "CC"},
        # 泌尿系统 — MDCL
        {"code": "N18.9", "name": "慢性肾脏病", "category": "泌尿系统", "cc_level": "CC"},
        {"code": "N39.0", "name": "泌尿道感染", "category": "泌尿系统", "cc_level": "CC"},
        # 其他系统补充
        {"code": "D64.9", "name": "贫血", "category": "血液系统", "cc_level": "CC"},
        {"code": "F32.9", "name": "抑郁症", "category": "精神", "cc_level": "CC"},
    ]

    # ── DRG 常用 ICD-9-CM-3 手术/操作编码参考 ──
    # 选自 ADRG_TABLE 中实际可匹配的编码前缀
    icd9_procedure_ref = [
        # 循环系统手术 — ADRG under MDCF
        {"code": "36.06001", "name": "冠状动脉支架植入术", "category": "心血管手术", "adrg": "FM2"},
        {"code": "36.1000x001", "name": "冠状动脉旁路移植术", "category": "心血管手术", "adrg": "FM1"},
        # 消化系统手术 — ADRG under MDCG
        {"code": "43.7x03", "name": "腹腔镜胃大部切除伴胃空肠吻合术", "category": "消化系统手术", "adrg": "GB2"},
        {"code": "47.0001", "name": "腹腔镜阑尾切除术", "category": "消化系统手术", "adrg": "GD1"},
        {"code": "45.7300x007", "name": "大肠部分切除术", "category": "消化系统手术", "adrg": "GB1"},
        # 肝、胆、胰手术 — ADRG under MDCH
        {"code": "51.22001", "name": "腹腔镜胆囊切除术", "category": "肝胆胰手术", "adrg": "HC2"},
        {"code": "51.6303", "name": "胆总管切除术", "category": "肝胆胰手术", "adrg": "HC1"},
        {"code": "51.3901", "name": "胆管空肠吻合术", "category": "肝胆胰手术", "adrg": "HC1"},
        # 呼吸系统手术 — ADRG under MDCE
        {"code": "34.8200x002", "name": "膈肌缝合术", "category": "胸外科手术", "adrg": "EC2"},
        {"code": "32.41001", "name": "肺叶切除术", "category": "胸外科手术", "adrg": "EB1"},
        # 骨科手术 — ADRG under MDCI
        {"code": "81.54001", "name": "全膝关节置换术", "category": "骨科手术", "adrg": "IC3"},
        {"code": "81.51001", "name": "全髋关节置换术", "category": "骨科手术", "adrg": "IC3"},
        {"code": "79.35001", "name": "股骨骨折切开复位内固定术", "category": "骨科手术", "adrg": "ID1"},
        # 产科手术 — ADRG under MDCO
        {"code": "74.1001", "name": "低位子宫下段剖宫产", "category": "产科手术", "adrg": "OB2"},
    ]

    # ── DRG 分组示例（严格使用 CN-DRG 2018 编码体系）──
    # 格式: ADRG编码 + 数字后缀（5=无CC, 9=有CC, 1=有MCC）
    drg_group_examples = [
        # 循环系统内科 — MDCF → FR3
        {"drg_code": "FR39", "drg_name": "心血管系统内科疾病，伴一般合并症/并发症",
         "mdc": "MDCF 循环系统", "type": "内科", "factors": "心血管疾病+CC", "adrg": "FR3"},
        {"drg_code": "FR35", "drg_name": "心血管系统内科疾病，不伴合并症/并发症",
         "mdc": "MDCF 循环系统", "type": "内科", "factors": "心血管疾病无CC", "adrg": "FR3"},
        # 消化系统外科 — MDCG → GB2
        {"drg_code": "GB29", "drg_name": "胃、十二指肠大手术，伴一般合并症/并发症",
         "mdc": "MDCG 消化道", "type": "外科", "factors": "胃手术+CC", "adrg": "GB2"},
        {"drg_code": "GB25", "drg_name": "胃、十二指肠大手术，不伴合并症/并发症",
         "mdc": "MDCG 消化道", "type": "外科", "factors": "胃手术无CC", "adrg": "GB2"},
        # 呼吸系统外科 — MDCE → EC2
        {"drg_code": "EC29", "drg_name": "纵隔、气管、胸壁其他手术，伴一般合并症/并发症",
         "mdc": "MDCE 呼吸系统", "type": "外科", "factors": "胸壁手术+CC", "adrg": "EC2"},
        # 肝胆胰外科 — MDCH → HC1
        {"drg_code": "HC15", "drg_name": "胆总管手术，不伴合并症/并发症",
         "mdc": "MDCH 肝胆胰", "type": "外科", "factors": "胆道手术无CC", "adrg": "HC1"},
        {"drg_code": "HC19", "drg_name": "胆总管手术，伴一般合并症/并发症",
         "mdc": "MDCH 肝胆胰", "type": "外科", "factors": "胆道手术+CC", "adrg": "HC1"},
        # 骨科外科 — MDCI → IC3
        {"drg_code": "IC35", "drg_name": "髋/膝关节置换术，不伴合并症/并发症",
         "mdc": "MDCI 骨骼肌肉", "type": "外科", "factors": "关节置换无CC", "adrg": "IC3"},
        {"drg_code": "IC39", "drg_name": "髋/膝关节置换术，伴一般合并症/并发症",
         "mdc": "MDCI 骨骼肌肉", "type": "外科", "factors": "关节置换+CC", "adrg": "IC3"},
    ]

    medical_records = {
        "sample_template": sample_record_template,
        "icd10_diagnosis_ref": icd10_diagnosis_ref,
        "icd9_procedure_ref": icd9_procedure_ref,
        "drg_group_examples": drg_group_examples,
        "record_schema_description": {
            "性别": "str, '男' 或 '女'",
            "年龄": "int, 患者年龄（0-120）",
            "主要诊断.疾病编码": "str, ICD-10 编码（如 C16.301, J15.9, I21.3）",
            "主要诊断.疾病名称": "str, 诊断中文名称",
            "次要诊断列表[].疾病编码": "str, 次要诊断 ICD-10 编码",
            "次要诊断列表[].疾病名称": "str, 次要诊断中文名称",
            "主要手术.手术编码": "str, ICD-9-CM-3 编码（如 43.7x03, 36.06001）",
            "主要手术.手术名称": "str, 手术中文名称",
            "主要手术.手术级别": "int, 1-4 级手术",
            "其他手术列表[].手术编码": "str, 额外手术/操作 ICD-9-CM-3 编码",
            "其他手术列表[].手术名称": "str, 额外手术中文名称",
            "其他手术列表[].手术级别": "int, 1-4 级手术",
        },
    }

    state["medical_records"] = medical_records
    append_trace(state, "medical_record_context",
                 f"Prepared CN-DRG aligned medical templates: "
                 f"{len(icd10_diagnosis_ref)} ICD-10 codes, "
                 f"{len(icd9_procedure_ref)} ICD-9-CM-3 codes, "
                 f"{len(drg_group_examples)} CN-DRG examples")
    return state
