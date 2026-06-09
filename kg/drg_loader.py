"""
CN-DRG 2018 分组规则数据层。

提供四张核心查询表：
  get_mdc()          ICD-10 诊断编码 → MDC
  get_adrg()         MDC + 手术编码 → ADRG
  check_complications()  次要诊断 → MCC / CC / 无
  resolve_drg()      ADRG + 并发症等级 → 最终 DRG 编码
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  MDC 查表：ICD-10 诊断编码前缀 → MDC
# ═══════════════════════════════════════════════════════════════
# 格式: {icd_prefix: (mdc_code, mdc_name)}
MDC_TABLE: dict[str, tuple[str, str]] = {
    # 神经系统
    "G":   ("MDCA", "神经系统疾病及功能障碍"),
    # 眼
    "H00": ("MDCB", "眼疾病及功能障碍"),
    # 耳鼻喉
    "H60": ("MDCC", "耳、鼻、口、喉疾病及功能障碍"),
    "H61": ("MDCC", "耳、鼻、口、喉疾病及功能障碍"),
    # 呼吸系统
    "J":   ("MDCE", "呼吸系统疾病及功能障碍"),
    # 循环系统
    "I":   ("MDCF", "循环系统疾病及功能障碍"),
    # 消化系统
    "C15": ("MDCG", "消化道疾病及功能障碍"),
    "C16": ("MDCG", "消化道疾病及功能障碍"),
    "C17": ("MDCG", "消化道疾病及功能障碍"),
    "C18": ("MDCG", "消化道疾病及功能障碍"),
    "C19": ("MDCG", "消化道疾病及功能障碍"),
    "C20": ("MDCG", "消化道疾病及功能障碍"),
    "C21": ("MDCG", "消化道疾病及功能障碍"),
    "C22": ("MDCG", "消化道疾病及功能障碍"),
    "C23": ("MDCG", "消化道疾病及功能障碍"),
    "C24": ("MDCG", "消化道疾病及功能障碍"),
    "C25": ("MDCG", "消化道疾病及功能障碍"),
    "C26": ("MDCG", "消化道疾病及功能障碍"),
    "K":   ("MDCG", "消化道疾病及功能障碍"),
    # 肝、胆、胰
    "B15": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "B16": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "B17": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "B18": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "B19": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K70": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K71": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K72": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K73": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K74": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K75": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K76": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K77": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K80": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K81": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K82": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K83": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K85": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K86": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    "K87": ("MDCH", "肝、胆、胰疾病及功能障碍"),
    # 骨骼肌肉
    "M":   ("MDCI", "骨骼、肌肉疾病及功能障碍"),
    "S":   ("MDCI", "骨骼、肌肉疾病及功能障碍"),
    # 皮肤
    "L":   ("MDCJ", "皮肤、皮下组织及乳腺疾病"),
    # 内分泌
    "E":   ("MDCK", "内分泌、营养、代谢疾病及功能障碍"),
    # 肾脏泌尿
    "N":   ("MDCL", "肾脏及泌尿系统疾病及功能障碍"),
    # 男性生殖
    "C60": ("MDCM", "男性生殖系统疾病及功能障碍"),
    "C61": ("MDCM", "男性生殖系统疾病及功能障碍"),
    "C62": ("MDCM", "男性生殖系统疾病及功能障碍"),
    # 女性生殖
    "C50": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C51": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C52": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C53": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C54": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C55": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C56": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C57": ("MDCN", "女性生殖系统疾病及功能障碍"),
    "C58": ("MDCN", "女性生殖系统疾病及功能障碍"),
    # 妊娠分娩
    "O":   ("MDCO", "妊娠、分娩及产褥期"),
    # 新生儿
    "P":   ("MDCP", "新生儿及其他围产期疾病"),
    # 血液
    "D":   ("MDCQ", "血液、造血器官及免疫疾病"),
    # 肿瘤（通用兜底）
    "C":   ("MDCR", "骨髓增生疾病及功能障碍，低分化肿瘤"),
    # 感染
    "A":   ("MDCS", "感染及寄生虫病（全身性或不明确部位）"),
    "B":   ("MDCS", "感染及寄生虫病（全身性或不明确部位）"),
    # 精神
    "F":   ("MDCT", "精神疾病及功能障碍"),
    # 损伤中毒
    "T":   ("MDCV", "创伤、中毒及药物毒性"),
    # 烧伤
    "T20": ("MDCW", "烧伤"),
    "T21": ("MDCW", "烧伤"),
    "T22": ("MDCW", "烧伤"),
    "T23": ("MDCW", "烧伤"),
    "T24": ("MDCW", "烧伤"),
    "T25": ("MDCW", "烧伤"),
    "T26": ("MDCW", "烧伤"),
    "T27": ("MDCW", "烧伤"),
    "T28": ("MDCW", "烧伤"),
    "T29": ("MDCW", "烧伤"),
    "T30": ("MDCW", "烧伤"),
    "T31": ("MDCW", "烧伤"),
    "T32": ("MDCW", "烧伤"),
    # 其他
    "Z":   ("MDCX", "影响健康状态的其他因素"),
    "R":   ("MDCZ", "多发性严重创伤"),
}


# ═══════════════════════════════════════════════════════════════
#  ADRG 查表: (MDC, 手术前缀) → ADRG
# ═══════════════════════════════════════════════════════════════
# 键格式: "MDC|proc_prefix" → (adrg_code, adrg_name)
ADRG_TABLE: dict[str, tuple[str, str]] = {
    # ── 消化系统手术 ──
    "MDCG|43.7": ("GB2", "胃、十二指肠大手术"),
    "MDCG|43.8": ("GB2", "胃、十二指肠大手术"),
    "MDCG|47.0": ("GD1", "阑尾切除术"),
    "MDCG|45.7": ("GB1", "大肠部分切除术"),
    "MDCG|45.8": ("GB1", "大肠部分切除术"),
    "MDCH|51.2": ("HC2", "胆囊切除术"),
    "MDCH|51.0": ("HC1", "胆管手术"),
    "MDCH|51.6": ("HC1", "胆总管手术"),
    # ── 循环系统手术 ──
    "MDCF|36.0": ("FM2", "经皮心血管介入治疗"),
    "MDCF|36.1": ("FM1", "冠状动脉旁路移植术"),
    "MDCF|35.2": ("FL1", "心脏瓣膜手术"),
    # ── 骨骼肌肉手术 ──
    "MDCI|81.5": ("IC3", "髋/膝关节置换术"),
    "MDCI|81.54": ("IC3", "髋/膝关节置换术"),
    "MDCI|81.51": ("IC3", "髋/膝关节置换术"),
    "MDCI|79.3": ("ID1", "股骨骨折手术"),
    "MDCI|79.1": ("ID1", "骨折切开复位内固定术"),
    "MDCI|81.0": ("IC1", "脊柱融合术"),
    # ── 呼吸系统手术 ──
    "MDCE|32.4": ("EB1", "肺叶切除术"),
    "MDCE|34.02": ("EB1", "胸部大手术（胸腔镜）"),
    "MDCE|34.8": ("EC2", "纵隔、气管、胸壁其他手术"),
    "MDCE|34.91": ("ED1", "胸腔穿刺术"),
    # ── 产科手术 ──
    "MDCO|74.": ("OB2", "剖宫产"),
    # ── 肿瘤手术 ──
    "MDCG|40.5": ("GB2", "胃恶性肿瘤根治术（含淋巴结清扫）"),
    # ── 泌尿系统手术 ──
    "MDCL|55.": ("LB1", "肾切除术"),
    # ── 神经系统手术 ──
    "MDCA|01.": ("BB1", "颅骨切开术"),
    "MDCA|01.2": ("BB1", "颅骨切开术"),
}

# ── 内科 ADRG（无手术时使用）──
# 格式: {mdc: (adrg_code, adrg_name)}  仅兜底
MEDICAL_ADRG: dict[str, tuple[str, str]] = {
    "MDCF": ("FR3", "心血管系统内科疾病"),
    "MDCE": ("ER3", "呼吸系统内科疾病"),
    "MDCG": ("GR1", "消化系统内科疾病"),
    "MDCH": ("HR1", "肝、胆、胰内科疾病"),
    "MDCI": ("IR1", "骨骼、肌肉内科疾病"),
    "MDCK": ("KR1", "内分泌、营养、代谢内科疾病"),
    "MDCL": ("LR1", "肾脏及泌尿系统内科疾病"),
    "MDCN": ("NR1", "女性生殖系统内科疾病"),
    "MDCS": ("SR1", "感染及寄生虫内科疾病"),
    "MDCQ": ("QR1", "血液、造血器官及免疫内科疾病"),
    "MDCA": ("BR2", "神经系统内科疾病"),
}


# ═══════════════════════════════════════════════════════════════
#  MCC 列表：严重合并症/并发症
# ═══════════════════════════════════════════════════════════════
MCC_SET: set[str] = {
    "C77.0", "C77.1", "C77.2", "C77.3", "C77.4", "C77.5",
    "C77.8", "C77.9",          # 淋巴结继发恶性肿瘤
    "I21.0", "I21.1", "I21.2", "I21.3", "I21.4", "I21.9",  # 急性心肌梗死
    "I22.0", "I22.1", "I22.8", "I22.9",                     # 再发心梗
    "J96.0", "J96.9", "J96.00",                             # 呼吸衰竭
    "N17.0", "N17.1", "N17.2", "N17.8", "N17.9",           # 急性肾衰竭
    "R57.0", "R57.1", "R57.8", "R57.9",                     # 休克
    "R65.0", "R65.1", "R65.2", "R65.9",                     # 全身炎症反应综合征
    "K72.0", "K72.9",                                       # 肝功能衰竭
    "I50.1", "I50.2", "I50.9",                              # 心力衰竭（重度）
    "I26.0", "I26.9",                                       # 肺栓塞
    "G93.1",                                                # 缺氧性脑损伤
    "A41.0", "A41.1", "A41.2", "A41.5", "A41.8", "A41.9", # 败血症
    "D65",                                                  # 弥散性血管内凝血
}


# ═══════════════════════════════════════════════════════════════
#  CC 列表：一般合并症/并发症
# ═══════════════════════════════════════════════════════════════
CC_SET: set[str] = {
    "E11.9", "E11.0", "E11.1",  # 2型糖尿病
    "E10.9", "E10.0",            # 1型糖尿病
    "I10",                       # 原发性高血压
    "I11.9",                     # 高血压性心脏病
    "N18.9", "N18.3", "N18.4", "N18.5",  # 慢性肾脏病
    "K66.0", "K66.002",          # 肠粘连
    "I63.8", "I63.801", "I63.9", # 脑梗死
    "I64",                       # 卒中
    "J44.9", "J44.0", "J44.1",  # COPD
    "K76.8", "K76.807",          # 肝囊肿
    "Z98.8", "Z98.800",          # 术后状态
    "E78.0", "E78.1", "E78.2", "E78.5",  # 高脂血症
    "I48.0", "I48.1", "I48.9",  # 房颤
    "I49.9",                     # 心律失常
    "D64.9",                     # 贫血
    "E87.1",                     # 低钠血症
    "E87.6",                     # 低钾血症
    "N39.0",                     # 泌尿道感染
    "J15.9",                     # 肺炎
    "F32.9",                     # 抑郁症
    "G47.3",                     # 睡眠呼吸暂停
    "B18.2",                     # 慢性丙型肝炎
}


# ── DRG 后缀 ──
# 无 CC: 后缀 "5"; 有 CC: 后缀 "9"; 有 MCC: 后缀 "1"
COMPLICATION_SUFFIX: dict[str, str] = {
    "NONE": "5",
    "none": "5",
    "CC": "9",
    "MCC": "1",
}


# ═══════════════════════════════════════════════════════════════
#  查询函数
# ═══════════════════════════════════════════════════════════════

def get_mdc(icd_code: str) -> dict[str, str] | None:
    """根据 ICD-10 编码查找对应的 MDC。
    按前缀长度降序匹配，确保长前缀（如 K83）优先于短前缀（如 K）。
    """
    icd = icd_code.strip().upper().rstrip("X")

    # 按前缀长度降序排列，保证更具体的匹配优先
    sorted_prefixes = sorted(MDC_TABLE.items(), key=lambda x: len(x[0]), reverse=True)

    for prefix, (mdc_code, mdc_name) in sorted_prefixes:
        if icd.startswith(prefix):
            return {"mdc": mdc_code, "mdc_name": mdc_name}

    return None


def get_adrg(mdc: str, proc_codes: list[str]) -> dict | None:
    """根据 MDC 和手术编码列表查询 ADRG。
    返回优先级最高的 ADRG（按手术级别，列表中越靠前优先级越高）。
    若无匹配，回退到内科 ADRG。
    """
    for proc in proc_codes:
        if not proc:
            continue
        proc_key = proc.strip()
        # 尝试前缀匹配（前4个→前3个→前2个字符）
        for length in (5, 4, 3, 2):
            prefix = proc_key[:length]
            key = f"{mdc}|{prefix}"
            if key in ADRG_TABLE:
                adrg_code, adrg_name = ADRG_TABLE[key]
                return {"adrg": adrg_code, "adrg_name": adrg_name, "matched_proc": proc,
                        "type": "surgical"}

    # 内科兜底
    if mdc in MEDICAL_ADRG:
        adrg_code, adrg_name = MEDICAL_ADRG[mdc]
        return {"adrg": adrg_code, "adrg_name": adrg_name, "matched_proc": None,
                "type": "medical"}

    return None


def check_complications(secondary_codes: list[str]) -> dict:
    """检查次要诊断中是否包含 MCC 或 CC。
    返回 {'level': 'MCC'|'CC'|'none', 'matched': [...]}
    """
    has_mcc = []
    has_cc = []

    for code in secondary_codes:
        code_clean = code.strip().upper()
        if code_clean in MCC_SET:
            has_mcc.append(code_clean)
        elif code_clean in CC_SET:
            has_cc.append(code_clean)

    if has_mcc:
        return {"level": "MCC", "matched_mcc": has_mcc, "matched_cc": has_cc}
    if has_cc:
        return {"level": "CC", "matched_mcc": [], "matched_cc": has_cc}
    return {"level": "NONE", "matched_mcc": [], "matched_cc": []}


def resolve_drg(adrg: str, complication_level: str) -> str:
    """根据 ADRG + 并发症等级计算最终 DRG 编码。
    CN-DRG 规则：完整 ADRG（如 GB2）+ 后缀数字 = 最终 DRG（如 GB29）。
    后缀: 5=无CC, 9=有CC, 1=有MCC
    """
    suffix = COMPLICATION_SUFFIX.get(complication_level) or COMPLICATION_SUFFIX.get(complication_level.upper(), "5")
    return f"{adrg}{suffix}"


# ── 向后兼容 ──
def load_drg_graph() -> list[dict[str, Any]]:
    """保留旧接口兼容性。返回关系类型摘要。"""
    return [
        {"source": "symptom", "relation": "suggests", "target": "disease"},
        {"source": "disease", "relation": "mapped_to", "target": "drg_group"},
        {"source": "disease", "relation": "treated_by", "target": "treatment"},
        {"source": "risk_factor", "relation": "increases_risk_of", "target": "disease"},
        {"source": "test", "relation": "confirms_or_rules_out", "target": "disease"},
    ]
