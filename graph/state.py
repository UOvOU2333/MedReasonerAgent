from typing import Any, List, TypedDict

class DRGState(TypedDict):
    query: str
    language: str

    # core KG
    entities: List[str]
    subgraph: dict[str, Any]

    # reasoning
    reasoning_paths: List[Any]
    ranked_paths: List[Any]

    # 🆕 医疗增强能力
    medical_report: dict
    treatment_plan: dict

    answer: str
    plan: dict

    # 可视化关键
    trace: List[dict]
