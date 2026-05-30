// Core domain types matching backend schemas

export interface Recording {
  id: string;
  filename: string;
  signal_type: "ecg" | "ppg";
  sampling_rate: number;
  signal_column: string;
  subject_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  status: "pending" | "processing" | "completed" | "failed";
  num_segments?: number;
}

export interface AssessmentJob {
  job_id: string;
  recording_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  error_message?: string;
  progress?: number;
}

export interface SqiMetric {
  metric_name: string;
  value: number;
  passed: boolean;
  threshold_min?: number;
  threshold_max?: number;
}

export interface SegmentResult {
  segment_id: string;
  segment_number: number;
  start_sample: number;
  end_sample: number;
  ai_classification: "accept" | "reject" | "uncomputable" | "pending";
  quality_score?: number;
  sqi_summary?: SqiMetric[];
  created_at: string;
}

export interface EffectiveSegmentResult extends SegmentResult {
  effective_classification: "accept" | "reject" | "uncomputable" | "pending";
  override_count: number;
  latest_override_at?: string;
}

export interface JobResultsResponse {
  job_id: string;
  recording_id: string;
  status: string;
  segments: EffectiveSegmentResult[];
  summary: {
    total_segments: number;
    accepted: number;
    rejected: number;
    uncomputable: number;
    pending: number;
    acceptance_rate: number;
  };
}

export interface ReportSummary {
  report_id: string;
  recording_id: string;
  job_id: string;
  created_at: string;
  is_stale: boolean;
  title?: string;
}

export interface Report extends ReportSummary {
  content_json: {
    summary?: Record<string, number | string>;
    segments?: EffectiveSegmentResult[];
    metadata?: Record<string, unknown>;
  };
  export_html_url?: string;
  export_pdf_url?: string;
}

export interface OverrideEvent {
  override_id: string;
  segment_id: string;
  practitioner_id: string;
  label: "accept" | "reject";
  reason_category: string;
  note: string;
  created_at: string;
}

export interface EffectiveClassificationResponse {
  segment_id: string;
  ai_classification: string;
  effective_classification: string;
  override_count: number;
  latest_override?: OverrideEvent;
}

export interface AgentLogEntry {
  log_id: string;
  job_id: string;
  level: "info" | "warning" | "error" | "debug";
  message: string;
  timestamp: string;
  agent_step?: string;
  metadata?: Record<string, unknown>;
}

export interface ThresholdSettings {
  [key: string]: number | string | boolean;
}
