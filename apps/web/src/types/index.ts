export type DocumentStatus = "PENDING" | "PROCESSING" | "INDEXED" | "FAILED";

export interface Document {
  id: string;
  workspace_id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id: string;
  citation_index: number;
  document_id: string;
  document_title: string;
  page_number: number | null;
  excerpt: string;
  chunk_id: string | null;
  similarity_score?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  insufficient_evidence?: boolean;
  created_at: string;
}

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  document_count?: number;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
}
