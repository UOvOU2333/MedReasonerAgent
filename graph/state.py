from typing import Any, List, TypedDict

# ── DRG 入组智能体状态 ──────────────────────────────────
class DRGState(TypedDict):
    query: str
    language: str

    # core KG — 旧管线兼容
    entities: List[str]
    subgraph: dict[str, Any]

    # reasoning
    reasoning_paths: List[Any]
    ranked_paths: List[Any]

    # 医疗增强能力
    medical_report: dict
    treatment_plan: dict

    # ── 新增：结构化 EMR + DRG 入组结果 ──
    emr_data: dict              # entity 解析的结构化电子病历
    drg_result: dict            # retrieval → reasoning 最终入组结果

    answer: str
    plan: dict

    # 可视化关键
    trace: List[dict]


# ── 文档自动生成智能体状态 ──────────────────────────────
class DocGenState(TypedDict):
    query: str             # 用户指令，含文档类型（requirements / architecture / testing）
    language: str          # zh / en
    doc_type: str          # 目标文档类型：requirements / architecture / testing
    project_name: str      # 项目名称

    # 子智能体传递
    code_analysis: dict    # code_scanner 输出：文件结构、模块清单等
    context_data: dict     # context_collector 输出：项目背景、需求摘要
    doc_draft: str         # doc_composer 输出：初稿 Markdown
    doc_formatted: str     # doc_formatter 输出：格式化后 Markdown
    doc_final: str         # doc_reviewer 审核通过后的最终文档
    review_report: dict    # 审核报告：检查项通过/失败

    answer: str            # 最终输出：文件保存路径 + 摘要
    trace: List[dict]


# ── 测试用例生成智能体状态 ──────────────────────────────
class TCGenState(TypedDict):
    query: str             # 用户指令，含测试类型 (normal / boundary / abnormal)
    language: str          # zh / en
    tc_type: str           # 目标测试类型：normal / boundary / abnormal
    project_name: str      # 项目名称

    # 子智能体传递
    drg_rules: dict        # drg_rule_extractor 输出：DRG 分组规则
    medical_records: dict  # medical_record_context 输出：病历样本
    tc_draft: str          # tc_composer 输出：初稿 Markdown
    tc_formatted: str      # tc_formatter 输出：格式化后 Markdown
    tc_final: str          # tc_reviewer 审核通过后的最终文档
    review_report: dict    # 审核报告：检查项通过/失败

    answer: str            # 最终输出：文件保存路径 + 摘要
    trace: List[dict]


# ── 虚拟文档系统智能体状态 ──────────────────────────────
class VDocState(TypedDict):
    query: str             # 操作指令
    language: str          # zh / en
    doc_name: str          # 文档名称
    doc_content: str       # 文档内容（由文档生成智能体传入）
    doc_type: str          # requirements / architecture / testing / tc_normal / tc_boundary / tc_abnormal

    # 子智能体传递
    validation_result: dict   # doc_validator 输出：格式检查结果
    doc_metadata: dict        # metadata_tagger 输出：文档元数据
    storage_path: str         # doc_storer 输出：实际保存路径
    index_status: dict        # index_updater 输出：索引更新状态
    notification: dict        # doc_notifier 输出：通知信息

    answer: str            # 最终输出：保存确认信息
    trace: List[dict]
