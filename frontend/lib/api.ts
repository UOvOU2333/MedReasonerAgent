export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function runReasoning(query: string, language: "zh" | "en" = "zh") {
  const response = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({query, language}),
  });

  if (!response.ok) {
    throw new Error(`Run failed: ${response.status}`);
  }
  return response.json();
}
