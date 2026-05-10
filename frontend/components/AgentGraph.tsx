"use client";

import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import NodeCard from "./NodeCard";
import { useTraceStore } from "../store/traceStore";

const order = [
  ["supervisor", "Supervisor"],
  ["entity", "Entity"],
  ["medical_report", "Medical Report"],
  ["retrieval", "DRG Retrieval"],
  ["reasoning", "SGLang Reasoning"],
  ["ranking", "Ranking"],
  ["treatment_plan", "Treatment Plan"],
  ["explain", "Explain"],
] as const;

const nodeTypes = { agent: NodeCard };

export default function AgentGraph() {
  const activeNode = useTraceStore((state) => state.activeNode);
  const completedNodes = useTraceStore((state) => state.completedNodes);

  const nodes: Node[] = order.map(([id, label], index) => ({
    id,
    type: "agent",
    position: { x: (index % 2) * 300, y: Math.floor(index / 2) * 110 },
    data: {
      label,
      active: activeNode === id,
      complete: completedNodes.includes(id),
    },
  }));

  const edges: Edge[] = order.slice(0, -1).map(([id], index) => ({
    id: `${id}-${order[index + 1][0]}`,
    source: id,
    target: order[index + 1][0],
    animated: activeNode === id,
  }));

  return (
    <div className="agent-graph">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
      </ReactFlow>
      <style jsx global>{`
        .agent-graph {
          width: 100%;
          height: 100%;
          min-height: 620px;
        }
        .node-card {
          width: 190px;
          min-height: 48px;
          display: flex;
          align-items: center;
          gap: 10px;
          border: 1px solid var(--border);
          border-radius: 8px;
          background: #fff;
          padding: 10px 12px;
          box-shadow: 0 6px 18px rgba(23, 32, 42, 0.08);
          font-size: 13px;
          font-weight: 650;
        }
        .node-card.active {
          border-color: var(--active);
          color: var(--active);
        }
        .node-card.complete {
          border-color: var(--ok);
          color: var(--ok);
        }
      `}</style>
    </div>
  );
}
