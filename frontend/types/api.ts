// All API request/response TypeScript interfaces

export interface RecordingMetadata {
  signal_type: string;
  sampling_rate: number;
  file_format: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  subject_id: string | null;
  device_id: string | null;
  uploaded_at: string;
}

export interface UploadResponse {
  recording_id: string;
  filename: string;
  status: string;
  metadata: RecordingMetadata;
}

export interface RecordingSummary {
  recording_id: string;
  filename: string;
  signal_type: string;
  status: string;
  uploaded_at: string;
  latest_assessment_job_id?: string;
  latest_verdict?: string;
}

export interface RecordingListResponse {
  items: RecordingSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface RecordingDetailResponse {
  recording_id: string;
  filename: string;
  signal_type: string;
  sampling_rate: number;
  file_format: string;
  duration_seconds: number | null;
  status: string;
  subject_id: string | null;
}

export interface WaveformChannel {
  name: string;
  data: number[];
}

export interface WaveformResponse {
  recording_id: string;
  signal_type: string;
  sampling_rate: number;
  start_time: number;
  end_time: number;
  channels: WaveformChannel[];
  downsampled: boolean;
  original_length: number;
  returned_length: number;
}

export interface AssessJobRequest {
  recording_id: string;
  config?: {
    segment_duration?: number;
    overlap?: number;
    sqi_metrics?: string[];
    rule_dict?: Record<string, { min?: number; max?: number }>;
  };
}

export interface AssessJobResponse {
  assessment_job_id: string;
  recording_id: string;
  status: string;
  estimated_duration_seconds?: number;
}

export interface JobProgress {
  current_stage: string;
  segments_processed: number;
  total_segments: number | null;
  progress_pct: number;
}

export interface AssessJobStatusResponse {
  assessment_job_id: string;
  recording_id: string;
  status: string;
  progress?: JobProgress;
  started_at?: string;
  completed_at?: string;
  total_segments?: number;
  processed_segments?: number;
}

export interface SegmentSummary {
  segment_id: string;
  segment_number: number;
  start_time: number;
  end_time: number;
  classification: "accept" | "reject" | "pending" | "uncomputable";
  quality_score: number | null;
  sqi_summary: Record<string, number>;
}

export interface ResultsSummary {
  total_segments: number;
  accepted: number;
  rejected: number;
  uncomputable: number;
  acceptance_rate: number;
  overall_quality_score: number | null;
  verdict: string | null;
}

export interface AssessJobResultsResponse {
  assessment_job_id: string;
  recording_id: string;
  status: string;
  signal_type: string | null;
  assessed_at: string | null;
  summary: ResultsSummary;
  segments: SegmentSummary[];
  agent_interpretation: string | null;
  escalated: boolean;
}

export interface FailedRule {
  metric: string;
  value: number;
  threshold: number;
  operator: string;
  description?: string;
}

export interface SegmentSQIBreakdown {
  segment_id: string;
  assessment_job_id: string;
  recording_id: string;
  segment_number: number;
  start_time: number;
  end_time: number;
  classification: string;
  quality_score: number | null;
  sqi_values: Record<string, number | null>;
  failed_rules: FailedRule[];
}

export interface ReportGenerateRequest {
  assessment_job_id: string;
  format: "json" | "html" | "pdf";
  include_waveform_plots?: boolean;
}

export interface ReportResponse {
  report_id: string;
  recording_id: string;
  assessment_job_id: string;
  format: string;
  generated_at: string;
  status?: string;
  content_json?: Record<string, unknown>;
  content_html?: string;
}

export interface AlertItem {
  alert_id: string;
  type: string;
  severity: string;
  recording_id: string;
  assessment_job_id: string;
  message: string;
  created_at: string | null;
  acknowledged: boolean;
}

export interface DashboardSummaryResponse {
  total_recordings: number;
  period_days: number;
  recent_assessments: Array<{
    recording_id: string;
    assessment_job_id: string;
    assessed_at: string | null;
    acceptance_rate: number | null;
    verdict: string | null;
  }>;
  quality_trends: Array<{ date: string; mean_acceptance_rate: number; assessments_count: number }>;
  alerts: AlertItem[];
}

export interface TimelineSegment {
  segment_number: number;
  start_time: number;
  end_time: number;
  classification: string;
  quality_score: number | null;
}

export interface TimelineResponse {
  assessment_job_id: string;
  recording_id: string;
  total_segments: number;
  timeline: TimelineSegment[];
}

export interface ConversationResponse {
  conversation_id: string;
  recording_id: string;
  assessment_job_id: string | null;
  title: string | null;
  created_at: string;
}

export interface MessageResponse {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  sources: unknown[];
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  response: string;
  sources: unknown[];
}

export interface ThresholdsResponse {
  thresholds: Record<string, { min?: number | null; max?: number | null }>;
}
