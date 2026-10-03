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
