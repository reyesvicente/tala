export type TranscriptionStatus = "pending" | "processing" | "done" | "failed";
export type TranscriptionTask = "transcribe" | "translate";

export interface Segment {
  start: number;
  end: number;
  text: string;
}

export interface Transcription {
  slug: string;
  status: TranscriptionStatus;
  task: TranscriptionTask;
  /** Belongs to an account: only the owner can open it. */
  private: boolean;
  original_filename: string;
  requested_language: string | null;
  detected_language: string | null;
  duration_seconds: number | null;
  progress: number;
  text: string | null;
  segments: Segment[] | null;
  error: string | null;
  model_name: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  expires_at: string;
}

export interface ServiceInfo {
  model: string;
  max_upload_mb: number;
  retention_hours: number;
  languages: Record<string, string>;
}

export interface TranscriptionSummary {
  slug: string;
  status: TranscriptionStatus;
  original_filename: string;
  detected_language: string | null;
  duration_seconds: number | null;
  created_at: string;
  expires_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
