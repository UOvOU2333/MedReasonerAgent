from langgraph.graph import StateGraph
from graph.state import DRGState, DocGenState, VDocState
from runtime.event_bus import event_bus
from runtime.executor import Executor

# ── DRG 入组智能体 ──
from agents.supervisor import supervisor_agent
from agents.entity import entity_agent
from agents.retrieval import retrieval_agent
from agents.reasoning import reasoning_agent
from agents.ranking import ranking_agent
from agents.explain import explain_agent
from agents.medical_report import medical_report_agent
from agents.treatment_plan import treatment_plan_agent

# ── 文档自动生成智能体 ──
from agents.doc_supervisor import doc_supervisor_agent
from agents.code_scanner import code_scanner_agent
from agents.context_collector import context_collector_agent
from agents.doc_composer import doc_composer_agent
from agents.doc_formatter import doc_formatter_agent
from agents.doc_reviewer import doc_reviewer_agent

# ── 虚拟文档系统智能体 ──
from agents.doc_receiver import doc_receiver_agent
from agents.doc_validator import doc_validator_agent
from agents.doc_metadata_tagger import doc_metadata_tagger_agent
from agents.doc_storer import doc_storer_agent
from agents.doc_notifier import doc_notifier_agent


# ═══════════════════════════════════════════════════════════
#  DRG 入组智能体工作流
# ═══════════════════════════════════════════════════════════
def build_graph():

    graph = StateGraph(DRGState)
    executor = Executor(event_bus)

    def node(name, fn):
        return lambda state: executor.run_node(name, fn, state)

    # core agents
    graph.add_node("supervisor", node("supervisor", supervisor_agent))
    graph.add_node("entity", node("entity", entity_agent))
    graph.add_node("retrieval", node("retrieval", retrieval_agent))
    graph.add_node("reasoning", node("reasoning", reasoning_agent))
    graph.add_node("ranking", node("ranking", ranking_agent))
    graph.add_node("explain", node("explain", explain_agent))

    # medical agents
    graph.add_node("medical_report", node("medical_report", medical_report_agent))
    graph.add_node("treatment_plan", node("treatment_plan", treatment_plan_agent))

    # entry
    graph.set_entry_point("supervisor")

    # flow
    graph.add_edge("supervisor", "entity")
    graph.add_edge("entity", "medical_report")
    graph.add_edge("medical_report", "retrieval")
    graph.add_edge("retrieval", "reasoning")
    graph.add_edge("reasoning", "ranking")
    graph.add_edge("ranking", "treatment_plan")
    graph.add_edge("treatment_plan", "explain")

    graph.set_finish_point("explain")

    return graph.compile()


# ═══════════════════════════════════════════════════════════
#  文档自动生成智能体工作流
# ═══════════════════════════════════════════════════════════
def build_docgen_graph():

    graph = StateGraph(DocGenState)
    executor = Executor(event_bus)

    def node(name, fn):
        return lambda state: executor.run_node(name, fn, state)

    graph.add_node("doc_supervisor", node("doc_supervisor", doc_supervisor_agent))
    graph.add_node("code_scanner", node("code_scanner", code_scanner_agent))
    graph.add_node("context_collector", node("context_collector", context_collector_agent))
    graph.add_node("doc_composer", node("doc_composer", doc_composer_agent))
    graph.add_node("doc_formatter", node("doc_formatter", doc_formatter_agent))
    graph.add_node("doc_reviewer", node("doc_reviewer", doc_reviewer_agent))

    graph.set_entry_point("doc_supervisor")

    # 线性流水线：分类 → 扫描代码 → 收集上下文 → 组稿 → 格式化 → 审核
    graph.add_edge("doc_supervisor", "code_scanner")
    graph.add_edge("code_scanner", "context_collector")
    graph.add_edge("context_collector", "doc_composer")
    graph.add_edge("doc_composer", "doc_formatter")
    graph.add_edge("doc_formatter", "doc_reviewer")

    graph.set_finish_point("doc_reviewer")

    return graph.compile()


# ═══════════════════════════════════════════════════════════
#  虚拟文档系统智能体工作流
# ═══════════════════════════════════════════════════════════
def build_vdoc_graph():

    graph = StateGraph(VDocState)
    executor = Executor(event_bus)

    def node(name, fn):
        return lambda state: executor.run_node(name, fn, state)

    graph.add_node("doc_receiver", node("doc_receiver", doc_receiver_agent))
    graph.add_node("doc_validator", node("doc_validator", doc_validator_agent))
    graph.add_node("doc_metadata_tagger", node("doc_metadata_tagger", doc_metadata_tagger_agent))
    graph.add_node("doc_storer", node("doc_storer", doc_storer_agent))
    graph.add_node("doc_notifier", node("doc_notifier", doc_notifier_agent))

    graph.set_entry_point("doc_receiver")

    # 线性流水线：接收 → 验证 → 标记元数据 → 存储 → 通知
    graph.add_edge("doc_receiver", "doc_validator")
    graph.add_edge("doc_validator", "doc_metadata_tagger")
    graph.add_edge("doc_metadata_tagger", "doc_storer")
    graph.add_edge("doc_storer", "doc_notifier")

    graph.set_finish_point("doc_notifier")

    return graph.compile()
