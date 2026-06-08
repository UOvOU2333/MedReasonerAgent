import json
from tools.trace import append_trace


def medical_record_context_agent(state):
    """
    收集并提供标准化的病历样本模板和 DRG 编码参考数据。
    纯计算步骤，不依赖 LLM。
    为 tc_composer 提供准确、完整的病历样本结构和 ICD 编码参考。
    """
    language = state.get("language", "zh")

    # 标准病历 JSON 模板
    sample_record_template = {
        "patient": {
            "age": 0,         # int: 患者年龄
            "gender": "",     # "M" 或 "F"
        },
        "principal_diagnosis": {
            "code": "",       # ICD-10 编码
            "name": "",       # 诊断名称
        },
        "secondary_diagnoses": [
            {"code": "", "name": ""},
        ],
        "procedures": [
            {"code": "", "name": ""},  # ICD-9-CM-3 编码
        ],
        "discharge_status": "",  # home / transfer / deceased / other
    }

    # DRG 常用 ICD-10 诊断编码参考（供 LLM 生成测试用例时参考）
    icd10_diagnosis_ref = [
        {"code": "I21.3", "name": "急性透壁性心肌梗死", "category": "循环系统"},
        {"code": "I21.4", "name": "急性非透壁性心肌梗死", "category": "循环系统"},
        {"code": "I25.10", "name": "冠状动脉粥样硬化性心脏病", "category": "循环系统"},
        {"code": "I50.9", "name": "心力衰竭", "category": "循环系统"},
        {"code": "I63.9", "name": "脑梗死", "category": "循环系统"},
        {"code": "J15.9", "name": "细菌性肺炎", "category": "呼吸系统"},
        {"code": "J44.9", "name": "慢性阻塞性肺疾病", "category": "呼吸系统"},
        {"code": "J45.9", "name": "哮喘", "category": "呼吸系统"},
        {"code": "K80.0", "name": "胆囊结石伴急性胆囊炎", "category": "消化系统"},
        {"code": "K35.8", "name": "急性阑尾炎", "category": "消化系统"},
        {"code": "K85.9", "name": "急性胰腺炎", "category": "消化系统"},
        {"code": "S72.0", "name": "股骨颈骨折", "category": "骨骼肌肉"},
        {"code": "S72.1", "name": "股骨粗隆间骨折", "category": "骨骼肌肉"},
        {"code": "M17.9", "name": "膝关节骨性关节炎", "category": "骨骼肌肉"},
        {"code": "O80.0", "name": "头位顺产", "category": "妊娠分娩"},
        {"code": "O82.0", "name": "选择性剖宫产", "category": "妊娠分娩"},
        {"code": "C34.9", "name": "支气管肺癌", "category": "肿瘤"},
        {"code": "C50.9", "name": "乳腺恶性肿瘤", "category": "肿瘤"},
        {"code": "E11.9", "name": "2型糖尿病", "category": "内分泌"},
        {"code": "I10", "name": "原发性高血压", "category": "循环系统"},
        {"code": "N18.9", "name": "慢性肾脏病", "category": "泌尿系统"},
        {"code": "N39.0", "name": "泌尿道感染", "category": "泌尿系统"},
    ]

    # DRG 常用 ICD-9-CM-3 手术/操作编码参考
    icd9_procedure_ref = [
        {"code": "36.06", "name": "冠状动脉支架植入术", "category": "心血管手术"},
        {"code": "36.10", "name": "冠状动脉旁路移植术(CABG)", "category": "心血管手术"},
        {"code": "47.0", "name": "腹腔镜阑尾切除术", "category": "消化系统手术"},
        {"code": "51.22", "name": "腹腔镜胆囊切除术", "category": "消化系统手术"},
        {"code": "81.54", "name": "全膝关节置换术", "category": "骨科手术"},
        {"code": "81.51", "name": "全髋关节置换术", "category": "骨科手术"},
        {"code": "79.35", "name": "股骨骨折切开复位内固定术", "category": "骨科手术"},
        {"code": "74.1", "name": "低位子宫下段剖宫产", "category": "产科手术"},
        {"code": "96.71", "name": "呼吸机治疗<96小时", "category": "操作"},
        {"code": "96.72", "name": "呼吸机治疗≥96小时", "category": "操作"},
        {"code": "99.25", "name": "化疗药物注射", "category": "操作"},
    ]

    # 常见 DRG 分组示例（用于帮助 LLM 理解 DRG 分组逻辑）
    drg_group_examples = [
        {"drg_code": "F62A", "drg_name": "心力衰竭和休克，伴严重合并症/并发症",
         "mdc": "循环系统", "type": "内科", "factors": "心力衰竭+CC"},
        {"drg_code": "F62B", "drg_name": "心力衰竭和休克，不伴严重合并症/并发症",
         "mdc": "循环系统", "type": "内科", "factors": "心力衰竭"},
        {"drg_code": "E01A", "drg_name": "胸部大手术，伴严重合并症/并发症",
         "mdc": "呼吸系统", "type": "外科", "factors": "胸部手术+CC"},
        {"drg_code": "I03A", "drg_name": "髋/膝关节置换术，伴严重合并症/并发症",
         "mdc": "骨骼肌肉", "type": "外科", "factors": "关节置换+CC"},
        {"drg_code": "I03B", "drg_name": "髋/膝关节置换术，不伴严重合并症/并发症",
         "mdc": "骨骼肌肉", "type": "外科", "factors": "关节置换"},
        {"drg_code": "G02A", "drg_name": "小肠和大肠手术，伴严重合并症/并发症",
         "mdc": "消化系统", "type": "外科", "factors": "肠道手术+CC"},
        {"drg_code": "O01A", "drg_name": "剖宫产，伴严重合并症/并发症",
         "mdc": "妊娠分娩", "type": "外科", "factors": "剖宫产+CC"},
        {"drg_code": "B02A", "drg_name": "颅骨切开术，伴严重合并症/并发症",
         "mdc": "神经系统", "type": "外科", "factors": "开颅手术+CC"},
    ]

    medical_records = {
        "sample_template": sample_record_template,
        "icd10_diagnosis_ref": icd10_diagnosis_ref,
        "icd9_procedure_ref": icd9_procedure_ref,
        "drg_group_examples": drg_group_examples,
        "record_schema_description": {
            "patient.age": "int, 患者年龄（0-120）",
            "patient.gender": "str, 'M' 或 'F'",
            "principal_diagnosis.code": "str, 有效的 ICD-10-CM 编码（如 I21.3）",
            "principal_diagnosis.name": "str, 诊断中文或英文名称",
            "secondary_diagnoses": "list, 次要诊断列表（可为空），含 code 和 name",
            "procedures": "list, 手术/操作列表（可为空），含 ICD-9-CM-3 code 和 name",
            "discharge_status": "str, home / transfer / deceased / other",
        },
    }

    state["medical_records"] = medical_records
    append_trace(state, "medical_record_context",
                 f"Prepared medical record templates: "
                 f"{len(icd10_diagnosis_ref)} ICD-10 codes, "
                 f"{len(icd9_procedure_ref)} ICD-9-CM-3 codes, "
                 f"{len(drg_group_examples)} DRG examples")
    return state
