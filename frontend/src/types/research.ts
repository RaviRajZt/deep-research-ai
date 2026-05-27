export type ResearchStatus =
  | "pending"
  | "planning"
  | "researching"
  | "writing"
  | "completed"
  | "failed"
  | "cancelled";

export interface ResearchSession {
  id: string;
  topic: string;
  status: ResearchStatus;
  result_summary: string | null;
  result_token_count: number | null;
  error_message: string | null;
  session_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchSessionListResponse {
  items: ResearchSession[];
  total: number;
  limit: number;
  offset: number;
}

export interface ExecutionLog {
  id: string;
  agent_role: string;
  step_name: string;
  status: "running" | "completed" | "failed";
  message: string | null;
  duration_ms: number | null;
  token_count: number | null;
  step_order: number | null;
  step_metadata: Record<string, unknown> | null;
  error_detail: string | null;
  created_at: string;
}

export interface Source {
  id: string;
  session_id: string;
  url: string;
  domain: string | null;
  title: string | null;
  content_hash: string | null;
  fetch_status: string;
  fetch_error: string | null;
  raw_token_count: number | null;
  summary_token_count: number | null;
  chunk_count: number | null;
  source_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
