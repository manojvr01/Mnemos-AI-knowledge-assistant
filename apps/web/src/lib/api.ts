const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>;
}

async function fetchJson<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  let url = `${API_BASE}${endpoint}`;
  if (options.params) {
    const searchParams = new URLSearchParams();
    for (const [key, val] of Object.entries(options.params)) {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    }
    const qs = searchParams.toString();
    if (qs) {
      url += (url.includes("?") ? "&" : "?") + qs;
    }
  }

  const defaultHeaders: Record<string, string> = {
    Accept: "application/json",
  };

  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: "include", // send httpOnly JWT cookies
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // keep fallback statusText
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  getMe: () => fetchJson<{ id: string; email: string; full_name: string | null }>("/auth/me"),
  register: (data: { email: string; password: string; full_name?: string }) =>
    fetchJson<{ id: string; email: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (data: { email: string; password: string }) =>
    fetchJson<{ message: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  logout: () => fetchJson<{ message: string }>("/auth/logout", { method: "POST" }),

  // Documents
  getDocuments: () => fetchJson<any[]>("/documents"),
  getDocument: (id: string) => fetchJson<any>(`/documents/${id}`),
  getDocumentStatus: (id: string) => fetchJson<any>(`/documents/${id}/status`),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return fetchJson<any>("/documents", {
      method: "POST",
      body: formData,
    });
  },
  deleteDocument: (id: string) =>
    fetchJson<{ message: string }>(`/documents/${id}`, { method: "DELETE" }),
  getDocumentContent: (id: string, pageNumber?: number) =>
    fetchJson<{ document_id: string; page_number: number | null; content: string }>(
      `/documents/${id}/content`,
      { params: { page_number: pageNumber } }
    ),

  // Search
  semanticSearch: (data: { query: string; top_k?: number; similarity_threshold?: number; collection_id?: string; document_id?: string }) =>
    fetchJson<any>("/search", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Conversations & RAG
  getConversations: () => fetchJson<any[]>("/conversations"),
  getConversation: (id: string) => fetchJson<any>(`/conversations/${id}`),
  createConversation: (title?: string, scope: "WORKSPACE" | "DOCUMENT" = "WORKSPACE", scopeId?: string) =>
    fetchJson<any>("/conversations", {
      method: "POST",
      body: JSON.stringify({
        title: title || "New Conversation",
        scope,
        scope_id: scopeId || null,
      }),
    }),
  sendMessage: (conversationId: string, content: string) =>
    fetchJson<any>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
};
