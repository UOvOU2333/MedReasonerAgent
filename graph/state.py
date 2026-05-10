from typing import TypedDict, List, Any

class DRGState(TypedDict):
    query: str

    # core KG
    entities: List[str]
    subgraph: Any

    # reasoning
    reasoning_paths: List[Any]
    ranked_paths: List[Any]

    # 🆕 医疗增强能力
    medical_report: dict
    treatment_plan: dict

    answer: str

    # 可视化关键
    trace: List[dict]