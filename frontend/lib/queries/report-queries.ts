'use client';

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api-client";
import type { Report, ReportSummary } from "@/lib/types";

export function useReport(reportId: string) {
  return useQuery<Report>({
    queryKey: ["report", reportId],
    queryFn: () => get<Report>(`/api/reports/${reportId}`),
    enabled: Boolean(reportId),
  });
}

export function useRecordingReports(recordingId: string) {
  return useQuery<ReportSummary[]>({
    queryKey: ["recordingReports", recordingId],
    queryFn: () => get<ReportSummary[]>(`/api/recordings/${recordingId}/reports`),
    enabled: Boolean(recordingId),
  });
}

interface GenerateReportPayload {
  recording_id: string;
  job_id: string;
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GenerateReportPayload) =>
      post<Report>("/api/reports/generate", payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["recordingReports", data.recording_id] });
    },
  });
}

interface FreshnessResponse {
  report_id: string;
  is_stale: boolean;
  checked_at: string;
}

export function useReportFreshness(reportId: string) {
  return useQuery<FreshnessResponse>({
    queryKey: ["reportFreshness", reportId],
    queryFn: () => get<FreshnessResponse>(`/api/reports/${reportId}/freshness`),
    enabled: Boolean(reportId),
  });
}
