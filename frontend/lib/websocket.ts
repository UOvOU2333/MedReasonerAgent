import type { TraceEvent } from "../store/traceStore";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function wsUrl(path: string) {
  const url = new URL(API_BASE);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = path;
  return url.toString();
}

export function streamReasoning(
  query: string,
  onEvent: (event: TraceEvent) => void,
  onClose?: () => void,
) {
  const socket = new WebSocket(wsUrl("/ws/run"));
  socket.onopen = () => socket.send(JSON.stringify({query}));
  socket.onmessage = (message) => onEvent(JSON.parse(message.data));
  socket.onclose = () => onClose?.();
  socket.onerror = () => onEvent({event: "error", node: "websocket"});
  return () => socket.close();
}
