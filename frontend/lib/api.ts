import type {
  ChatResponse,
  DocumentDetail,
  DocumentItem,
  EvalCase,
  EvalResult,
  EvalRunResponse
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  return apiRequest<DocumentItem[]>("/documents");
}

export async function getDocument(documentId: number): Promise<DocumentDetail> {
  return apiRequest<DocumentDetail>(`/documents/${documentId}`);
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<DocumentItem>("/documents/upload", {
    method: "POST",
    body: formData
  });
}

export async function addWebDocument(url: string): Promise<DocumentItem> {
  return apiRequest<DocumentItem>("/documents/web", {
    method: "POST",
    body: JSON.stringify({ url })
  });
}

export async function indexDocument(documentId: number): Promise<DocumentItem> {
  return apiRequest<DocumentItem>(`/documents/${documentId}/index`, {
    method: "POST"
  });
}

export async function askQuestion(question: string, topK = 5): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/chat/ask", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK })
  });
}

export async function listEvalCases(): Promise<EvalCase[]> {
  return apiRequest<EvalCase[]>("/eval/cases");
}

export async function runEvals(): Promise<EvalRunResponse> {
  return apiRequest<EvalRunResponse>("/eval/run", {
    method: "POST"
  });
}

export async function listEvalResults(): Promise<EvalResult[]> {
  return apiRequest<EvalResult[]>("/eval/results");
}
