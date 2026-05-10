from langgraph.graph import StateGraph
from graph.state import DRGState
from runtime.event_bus import event_bus
from runtime.executor import Executor

from agents.supervisor import supervisor_agent
from agents.entity import entity_agent
from agents.retrieval import retrieval_agent
from agents.reasoning import reasoning_agent
from agents.ranking import ranking_agent
from agents.explain import explain_agent

# 🆕 新增
from agents.medical_report import medical_report_agent
from agents.treatment_plan import treatment_plan_agent


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

    # 🆕 medical agents
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

    # 🆕 治疗方案生成
    graph.add_edge("ranking", "treatment_plan")

    graph.add_edge("treatment_plan", "explain")

    graph.set_finish_point("explain")

    return graph.compile()
