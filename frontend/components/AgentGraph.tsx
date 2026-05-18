"use client";

import { Background, Controls, Handle, Position, ReactFlow, ReactFlowProvider, useReactFlow, type Edge, type Node } from "@xyflow/react";
import { CheckCircle2, GitFork, Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useTraceStore } from "../store/traceStore";

const labels: Record<string, string> = {
  supervisor: "意图分类",
  entity: "实体抽取",
  medical_report: "病例理解",
  retrieval: "DRG 检索",
  reasoning: "医学推理",
  ranking: "路径排序",
  treatment_plan: "治疗规划",
  explain: "解释生成",
};

const englishLabels: Record<string, string> = {
  supervisor: "Classify intent",
  entity: "Find medical terms",
  medical_report: "Understand case",
  retrieval: "Search DRG graph",
  reasoning: "Reason medically",
  ranking: "Rank evidence",
  treatment_plan: "Draft care plan",
  explain: "Explain result",
};

const optionLabels: Record<string, { zh: string; en: string }> = {
  simple: { zh: "简单回答", en: "Simple answer" },
  "multi-hop": { zh: "多步推理", en: "Multi-step reasoning" },
  "deep-reasoning": { zh: "深度推理", en: "Deep reasoning" },
  entity_extractor: { zh: "提取医学关键词", en: "Extract medical terms" },
  terminology_normalizer: { zh: "规范医学术语", en: "Normalize medical terms" },
  symptom_parser: { zh: "识别症状描述", en: "Identify symptoms" },
  case_summarizer: { zh: "整理病例摘要", en: "Summarize case" },
  risk_factor_analyzer: { zh: "分析风险因素", en: "Analyze risk factors" },
  severity_estimator: { zh: "估计严重程度", en: "Estimate severity" },
  direct_drg_lookup: { zh: "直接查找 DRG 关系", en: "Direct DRG lookup" },
  multi_hop_expansion: { zh: "扩展多跳关系", en: "Expand graph paths" },
  fallback_subgraph: { zh: "使用备用子图", en: "Use fallback graph" },
  llm_reasoner: { zh: "调用通用模型推理", en: "Use general LLM" },
  deepseek_reasoner: { zh: "调用 DeepSeek 推理", en: "Use DeepSeek" },
  sglang_reasoner: { zh: "调用 SGLang 推理", en: "Use SGLang" },
  path_ranker: { zh: "排序推理路径", en: "Rank reasoning paths" },
  confidence_scorer: { zh: "评估可信度", en: "Score confidence" },
  evidence_filter: { zh: "筛选证据", en: "Filter evidence" },
  treatment_generator: { zh: "生成方案草案", en: "Draft care options" },
  drug_candidate_lookup: { zh: "查找候选用药", en: "Find drug candidates" },
  warning_checker: { zh: "检查风险提示", en: "Check warnings" },
  trace_summarizer: { zh: "总结执行过程", en: "Summarize trace" },
  plain_language_explainer: { zh: "转成易懂解释", en: "Explain plainly" },
  limitation_writer: { zh: "补充限制说明", en: "Add limitations" },
};

const nodeTypes = { decision: DecisionNode, option: OptionNode };
const centerX = 150;
const optionGap = 96;
const levelGap = 184;

export default function AgentGraph() {
  return (
    <ReactFlowProvider>
      <RunTree />
    </ReactFlowProvider>
  );
}

function RunTree() {
  const activeNode = useTraceStore((state) => state.activeNode);
  const decisionSequence = useTraceStore((state) => state.decisionSequence);
  const completedNodes = useTraceStore((state) => state.completedNodes);
  const availableTools = useTraceStore((state) => state.availableTools);
  const selectedTools = useTraceStore((state) => state.selectedTools);
  const decisionParents = useTraceStore((state) => state.decisionParents);
  const language = useTraceStore((state) => state.language);
  const { fitView } = useReactFlow();

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  decisionSequence.forEach((decisionId, depth) => {
    const options = availableTools[decisionId] ?? [];
    const selected = selectedTools[decisionId];
    const y = depth * levelGap + 24;

    nodes.push({
      id: decisionId,
      type: "decision",
      position: { x: centerX, y },
      data: {
        label: decisionLabel(decisionId, language),
        internalName: decisionId,
        active: activeNode === decisionId,
        complete: completedNodes.includes(decisionId),
      },
    });

    options.forEach((option, index) => {
      const optionId = optionNodeId(decisionId, option);
      const optionX = centerX + (index - (options.length - 1) / 2) * optionGap;
      nodes.push({
        id: optionId,
        type: "option",
        position: { x: optionX, y: y + 74 },
        data: {
          label: optionLabel(option, language),
          internalName: option,
          selected: selected === option,
          active: activeNode === decisionId,
        },
        draggable: false,
      });
      edges.push({
        id: `${decisionId}-${optionId}`,
        source: decisionId,
        sourceHandle: "bottom",
        target: optionId,
        targetHandle: "top",
        animated: activeNode === decisionId || selected === option,
        className: selected === option ? "executed-edge" : undefined,
        type: "smoothstep",
      });
    });

    const nextDecision = decisionSequence[depth + 1];
    if (nextDecision) {
      const parentDecision = decisionParents[nextDecision] ?? decisionId;
      const parentSelected = selectedTools[parentDecision];
      if (parentSelected) {
        edges.push({
          id: `${parentDecision}-${parentSelected}-${nextDecision}`,
          source: optionNodeId(parentDecision, parentSelected),
          sourceHandle: "bottom",
          target: nextDecision,
          targetHandle: "top",
          animated: activeNode === nextDecision,
          className: "executed-edge",
          type: "smoothstep",
        });
      }
    }
  });

  useEffect(() => {
    if (!decisionSequence.length) {
      return;
    }
    requestAnimationFrame(() => {
      fitView({
        duration: 450,
        padding: 0.22,
        includeHiddenNodes: false,
        maxZoom: 1,
      });
    });
  }, [decisionSequence.length, fitView]);

  return (
    <aside className="run-tree">
      <div className="run-tree-header">
        <h2>{language === "zh" ? "运行决策树" : "Decision Tree"}</h2>
        <span>
          {activeNode
            ? `${language === "zh" ? "当前决策" : "Current decision"}：${decisionLabel(activeNode, language)}`
            : decisionSequence.length
              ? language === "zh"
                ? "执行路径已更新"
                : "Execution path updated"
              : language === "zh"
                ? "等待输入"
                : "Waiting"}
        </span>
      </div>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView minZoom={0.15}>
        <Background gap={18} />
        <Controls showInteractive={false} />
      </ReactFlow>
      <style jsx global>{`
        .run-tree {
          height: 100%;
          min-height: 0;
          display: grid;
          grid-template-rows: auto 1fr;
          background: var(--panel);
          border-left: 1px solid var(--border);
        }
        .run-tree-header {
          padding: 14px;
          border-bottom: 1px solid var(--border);
        }
        .run-tree-header h2 {
          margin: 0 0 4px;
          font-size: 15px;
        }
        .run-tree-header span {
          color: var(--muted);
          font-size: 12px;
        }
        .decision-node {
          width: 128px;
          min-height: 42px;
          display: grid;
          grid-template-columns: 18px 1fr;
          align-items: center;
          gap: 7px;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: #fff;
          padding: 8px 10px;
          box-shadow: 0 4px 12px rgba(23, 32, 42, 0.08);
          font-size: 12px;
          font-weight: 700;
        }
        .decision-node.active {
          border-color: var(--active);
          color: var(--active);
        }
        .decision-node.complete {
          border-color: var(--ok);
          color: var(--ok);
        }
        .option-node {
          width: 92px;
          min-height: 40px;
          display: grid;
          place-items: center;
          text-align: center;
          border: 1px solid #e1e6ee;
          border-radius: 8px;
          background: #f8fafc;
          color: var(--muted);
          padding: 5px;
          font-size: 10px;
          font-weight: 700;
          line-height: 1.2;
          overflow-wrap: anywhere;
        }
        .option-node.active {
          border-color: #d7c6a7;
          background: #fffaf0;
        }
        .option-node.selected {
          border-color: var(--ok);
          background: #edf8f1;
          color: var(--ok);
        }
        .executed-edge path {
          stroke: var(--ok);
          stroke-width: 2.2;
        }
        .tree-handle {
          width: 7px;
          height: 7px;
          border: 1px solid var(--border);
          background: #fff;
          opacity: 0;
        }
      `}</style>
    </aside>
  );
}

function optionNodeId(decisionId: string, option: string) {
  return `${decisionId}:${option}`;
}

function decisionLabel(decisionId: string, language: "zh" | "en") {
  return language === "zh" ? labels[decisionId] ?? decisionId : englishLabels[decisionId] ?? decisionId;
}

function optionLabel(option: string, language: "zh" | "en") {
  const label = optionLabels[option];
  if (!label) {
    return option.replaceAll("_", " ");
  }
  return label[language];
}

function DecisionNode({ data }: { data: { label: string; internalName?: string; active?: boolean; complete?: boolean } }) {
  const status = data.complete ? "complete" : data.active ? "active" : "";
  return (
    <div className={`decision-node ${status}`} title={data.internalName}>
      <Handle type="target" position={Position.Top} id="top" className="tree-handle" />
      {data.complete ? <CheckCircle2 size={16} /> : data.active ? <Loader2 size={16} /> : <GitFork size={16} />}
      <span>{data.label}</span>
      <Handle type="source" position={Position.Bottom} id="bottom" className="tree-handle" />
    </div>
  );
}

function OptionNode({ data }: { data: { label: string; internalName?: string; selected?: boolean; active?: boolean } }) {
  const status = data.selected ? "selected" : data.active ? "active" : "";
  return (
    <div className={`option-node ${status}`} title={data.internalName}>
      <Handle type="target" position={Position.Top} id="top" className="tree-handle" />
      {data.label}
      <Handle type="source" position={Position.Bottom} id="bottom" className="tree-handle" />
    </div>
  );
}
