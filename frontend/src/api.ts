import type { RecapRequest, RecapResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function generateRecap(payload: RecapRequest): Promise<RecapResponse> {
  const response = await fetch(`${API_BASE}/api/recap`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }

  return response.json();
}
